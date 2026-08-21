import aiohttp
import re
import struct
import json
from datetime import datetime
from urllib.parse import quote as urlquote

DOMAIN = "gold-usergeneratedcontent.net"
LTN_DOMAIN = f"ltn.{DOMAIN}"
ROOT = "https://hitomi.la"
REFERER = f"{ROOT}/"
NOZOMI_LIMIT = 300


def parse_nozomi(data):
    count = len(data) // 4
    if count == 0:
        return []
    return list(struct.unpack(f">{count}I", data[: count * 4]))


def nozomi_url(tag, language="all"):
    tag = tag.strip()
    if ":" in tag:
        ns, _, value = tag.partition(":")
    else:
        ns, value = "", tag
    if ns in ("female", "male"):
        tag_path = urlquote(tag.replace("_", " "), safe=":")
        return f"https://{LTN_DOMAIN}/n/tag/{tag_path}-{language}.nozomi"
    elif ns == "language":
        return f"https://{LTN_DOMAIN}/n/index-{value}.nozomi"
    elif ns:
        tag_path = urlquote(value.replace("_", " "), safe="")
        return f"https://{LTN_DOMAIN}/n/{ns}/{tag_path}-{language}.nozomi"
    else:
        tag_path = urlquote(value.replace("_", " "), safe="")
        return f"https://{LTN_DOMAIN}/n/tag/{tag_path}-{language}.nozomi"


async def load_ids(session, tag, language="all", limit=NOZOMI_LIMIT):
    url = nozomi_url(tag, language)
    headers = {"Referer": REFERER, "Range": f"bytes=0-{limit * 4 - 1}"}
    try:
        async with session.get(url, headers=headers) as resp:
            if resp.status in (200, 206):
                data = await resp.read()
                return parse_nozomi(data)
    except Exception:
        pass
    return []


class QueryParser:
    """Parse tag queries: AND (space), OR (|), grouping (()).
    Tags use underscores for spaces (e.g. sole_male).
    Namespace prefixes optional (e.g. female:sole_female).
    """

    def __init__(self, query):
        self.query = query
        self.pos = 0

    def parse(self):
        if not self.query or not self.query.strip():
            return None
        result = self.parse_or()
        return result

    def parse_or(self):
        left = self.parse_and()
        while self._match_char("|"):
            right = self.parse_and()
            left = ("or", left, right)
        return left

    def parse_and(self):
        left = self.parse_atom()
        while True:
            self._skip_spaces()
            if self.pos >= len(self.query) or self.query[self.pos] in ("|", ")"):
                break
            right = self.parse_atom()
            if right is not None:
                left = ("and", left, right)
        return left

    def parse_atom(self):
        self._skip_spaces()
        if self._peek() == "(":
            self.pos += 1
            result = self.parse_or()
            self._skip_spaces()
            if self._peek() == ")":
                self.pos += 1
            return result
        return self.parse_tag()

    def parse_tag(self):
        self._skip_spaces()
        start = self.pos
        while self.pos < len(self.query) and self.query[self.pos] not in ("|", ")", " ", "("):
            self.pos += 1
        tag = self.query[start:self.pos].strip()
        return ("tag", tag) if tag else None

    def _peek(self):
        self._skip_spaces()
        return self.query[self.pos] if self.pos < len(self.query) else None

    def _match_char(self, char):
        self._skip_spaces()
        if self.pos < len(self.query) and self.query[self.pos] == char:
            self.pos += 1
            return True
        return False

    def _skip_spaces(self):
        while self.pos < len(self.query) and self.query[self.pos] == " ":
            self.pos += 1


async def evaluate_query(session, node, language="all", limit=NOZOMI_LIMIT):
    if node is None:
        return set(await load_ids(session, "language:all", language, limit))
    if node[0] == "tag":
        return set(await load_ids(session, node[1], language, limit))
    if node[0] == "and":
        left = await evaluate_query(session, node[1], language, limit)
        right = await evaluate_query(session, node[2], language, limit)
        return left & right
    if node[0] == "or":
        left = await evaluate_query(session, node[1], language, limit)
        right = await evaluate_query(session, node[2], language, limit)
        return left | right
    return set()


def _prefix_query(node, ns):
    if node is None:
        return None
    if node[0] == "tag":
        tag = node[1]
        if ":" not in tag:
            tag = f"{ns}:{tag}"
        return ("tag", tag)
    if node[0] in ("and", "or"):
        return (node[0], _prefix_query(node[1], ns), _prefix_query(node[2], ns))
    return node


async def _load_query_ids(session, query, language="all", limit=NOZOMI_LIMIT):
    parser = QueryParser(query)
    tree = parser.parse()
    return await evaluate_query(session, tree, language, limit)


async def _load_ns_query_ids(session, query, ns, language="all", limit=NOZOMI_LIMIT):
    parser = QueryParser(query)
    tree = parser.parse()
    tree = _prefix_query(tree, ns)
    return await evaluate_query(session, tree, language, limit)


async def search(
    session,
    include,
    exclude="",
    language="japanese",
    category="",
    series="",
    artist="",
    limit=NOZOMI_LIMIT,
):
    parser = QueryParser(include)
    tree = parser.parse()
    result = await evaluate_query(session, tree, language, limit)

    if category:
        cat_ids = await _load_ns_query_ids(session, category, "type", "all", limit)
        result &= cat_ids

    if series:
        series_ids = await _load_ns_query_ids(session, series, "series", "all", limit)
        result &= series_ids

    if artist:
        artist_ids = await _load_ns_query_ids(session, artist, "artist", "all", limit)
        result &= artist_ids

    if exclude:
        for token in exclude.split():
            token = token.strip()
            if token.startswith("-") and len(token) > 1:
                tag = token[1:]
                if ":" not in tag:
                    tag = f"tag:{tag}"
                ids = await _load_query_ids(session, tag, "all", limit)
                result -= ids

    return sorted(result, reverse=True) if result else []


async def gallery_info(session, gid):
    url = f"https://{LTN_DOMAIN}/galleries/{gid}.js"
    headers = {"Referer": REFERER}
    try:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                text = await resp.text()
                json_str = text.partition("=")[2].strip().rstrip(";")
                return json.loads(json_str)
    except Exception:
        pass
    return None


def thumb_url(hash_str):
    return (
        f"https://atn.{DOMAIN}/avifbigtn/"
        f"{hash_str[-1]}/{hash_str[-3:-1]}/{hash_str}.avif"
    )


_gg_data = None


async def _load_gg(session):
    global _gg_data
    if _gg_data is not None:
        return _gg_data
    try:
        async with session.get(
            f"https://{LTN_DOMAIN}/gg.js", headers={"Referer": REFERER}
        ) as resp:
            if resp.status == 200:
                text = await resp.text()
                b_match = re.search(r"b:\s*'([^']+)'", text)
                cases = {int(m.group(1)) for m in re.finditer(r"case (\d+):", text)}
                _gg_data = {"b": b_match.group(1) if b_match else "", "cases": cases}
                return _gg_data
    except Exception:
        pass
    _gg_data = {"b": "", "cases": set()}
    return _gg_data


async def page_image_url(session, hash_str, filename):
    gg = await _load_gg(session)
    ext = filename.rsplit(".", 1)[-1] if "." in filename else "jpg"
    inum = int(hash_str[-1] + hash_str[-3:-1], 16)
    gg_m = 1 if inum in gg["cases"] else 0
    sub = str(1 + gg_m)
    return f"https://{sub}.{DOMAIN}/{gg['b']}{inum}/{hash_str}.{ext}"


def page_url(info):
    return ROOT + info.get("galleryurl", "")


def parse_gallery_date(date_str):
    try:
        return datetime.fromisoformat(date_str)
    except (ValueError, TypeError):
        return None


def extract_tags(info):
    tags = []
    for t in info.get("tags", []):
        name = t.get("tag", "")
        if t.get("female") == "1":
            name += " ♀"
        elif t.get("male") == "1":
            name += " ♂"
        tags.append(name)
    return tags


def extract_artists(info):
    artists = []
    for a in info.get("artists", []):
        if isinstance(a, dict):
            artists.append(a.get("artist", ""))
        elif isinstance(a, str):
            artists.append(a)
    return [a for a in artists if a]


def extract_series(info):
    series = []
    for s in info.get("parodys", []):
        if isinstance(s, dict):
            series.append(s.get("parody", ""))
        elif isinstance(s, str):
            series.append(s)
    return [s for s in series if s]
