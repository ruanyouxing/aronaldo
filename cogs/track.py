import io
import asyncio
import json
import re
import struct
from urllib.parse import quote
import aiohttp
import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from utils.hitomi import BooleanQueryParser, get_thumbnail_url
from utils.db import TrackDatabase

HITOMI_CDN = "https://ltn.gold-usergeneratedcontent.net"
HITOMI_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://hitomi.la/",
}
# .nozomi files are newest-first big-endian uint32 galleryblock IDs.
# Read this many IDs deep per index per tick; metadata downloads are gated
# by the seen-cache so depth only costs bytes, not requests.
NOZOMI_SCAN_DEPTH = 400
METADATA_CONCURRENCY = 8
SEEN_CACHE_MAX = 20000


class TrackCog(commands.Cog, name="track"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = TrackDatabase()
        self.session: Optional[aiohttp.ClientSession] = None
        self.active_tracks: Dict[int, Dict[str, Any]] = {}
        # Ordered set of galleryblock IDs already downloaded (insertion-ordered dict)
        self._seen_ids: Dict[int, None] = {}

    async def cog_load(self):
        await self.db.init()
        # Initialize aiohttp Session within running loop
        resolver = aiohttp.AsyncResolver(nameservers=["1.1.1.1", "8.8.8.8"])
        connector = aiohttp.TCPConnector(resolver=resolver)
        self.session = aiohttp.ClientSession(connector=connector)

        try:
            await self._load_tracks_into_cache()
        except Exception:
            await self.session.close()
            raise
        self.tracker_loop.start()

    async def cog_unload(self):
        self.tracker_loop.cancel()
        if self.session and not self.session.closed:
            await self.session.close()

    @staticmethod
    def _ensure_aware(ts) -> datetime:
        """Coerces a stored/raw timestamp into a tz-aware UTC datetime."""
        if isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts)
            except ValueError:
                return datetime.now(timezone.utc)
        if not isinstance(ts, datetime):
            return datetime.now(timezone.utc)
        return ts.replace(tzinfo=timezone.utc) if ts.tzinfo is None else ts

    @staticmethod
    def _clear_filter(value: Optional[str]) -> Optional[str]:
        """Treat a literal 'NONE' argument as an explicit clear -> match any."""
        if value is not None and value.strip().upper() == "NONE":
            return ""
        return value

    def _build_ast_dict(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Pre-parses ASTs for all fields for zero-latency evaluations in polling loop."""
        # Merge include and exclude into single tag query AST
        inc = record.get("raw_include") or ""
        exc = record.get("raw_exclude") or ""
        clean_exc = " ".join([f"-{t.strip('-')}" for t in exc.split() if t])
        tag_query = f"{inc} {clean_exc}".strip()

        return {
            "user_id": record["user_id"],
            "tag_ast": BooleanQueryParser(tag_query).parse() if tag_query else None,
            "artist_ast": BooleanQueryParser(record["artist"]).parse() if record.get("artist") else None,
            "character_ast": BooleanQueryParser(record["character"]).parse() if record.get("character") else None,
            "series_ast": BooleanQueryParser(record["series"]).parse() if record.get("series") else None,
            "language_ast": BooleanQueryParser(record["language"]).parse() if record.get("language") else None,
            "category_ast": BooleanQueryParser(record["category"]).parse() if record.get("category") else None,
            "timestamp": self._ensure_aware(record.get("last_checked_timestamp")),
            "raw": record
        }

    async def _load_tracks_into_cache(self):
        self.active_tracks.clear()
        records = await self.db.get_all_tracks()
        for record in records:
            self.active_tracks[record["track_id"]] = self._build_ast_dict(record)

    # --- Slash Commands ---

    @app_commands.command(name="addtrack", description="Add a new gallery tracking query (Supports AND, OR, grouping).")
    @app_commands.dm_only()
    async def addtrack(
        self,
        interaction: discord.Interaction,
        include: Optional[str] = None,
        exclude: Optional[str] = None,
        series: Optional[str] = "original",
        character: Optional[str] = None,
        category: Optional[str] = "doujinshi",
        artist: Optional[str] = None,
        language: Optional[str] = "japanese"
    ):
        user_id = interaction.user.id

        # Literal "NONE" clears a filter -> empty string matches any item
        include = self._clear_filter(include)
        exclude = self._clear_filter(exclude)
        series = self._clear_filter(series)
        character = self._clear_filter(character)
        category = self._clear_filter(category)
        artist = self._clear_filter(artist)
        language = self._clear_filter(language)

        track_id = await self.db.add_track(
            user_id=user_id,
            raw_include=include,
            raw_exclude=exclude,
            series=series,
            character=character,
            category=category,
            artist=artist,
            language=language
        )

        record = {
            "track_id": track_id,
            "user_id": user_id,
            "raw_include": include,
            "raw_exclude": exclude,
            "series": series,
            "character": character,
            "category": category,
            "artist": artist,
            "language": language,
            "last_checked_timestamp": datetime.now(timezone.utc)
        }
        self.active_tracks[track_id] = self._build_ast_dict(record)

        await interaction.response.send_message(
            f"Tracking registered with ID `#{track_id}`.\n"
            f"**Tags:** `{include or 'All'}` | **Exclude:** `{exclude or 'None'}`\n"
            f"**Artist:** `{artist or 'Any'}` | **Character:** `{character or 'Any'}`\n"
            f"**Series:** `{series or 'Any'}` | **Type:** `{category or 'Any'}` | **Lang:** `{language or 'Any'}`",
            ephemeral=True
        )

    @app_commands.command(name="edittrack", description="Edit an existing query with boolean filters. Pass NONE to a filter to clear it.")
    @app_commands.dm_only()
    async def edittrack(
        self,
        interaction: discord.Interaction,
        track_id: int,
        include: Optional[str] = None,
        exclude: Optional[str] = None,
        series: Optional[str] = None,
        character: Optional[str] = None,
        category: Optional[str] = None,
        artist: Optional[str] = None,
        language: Optional[str] = None,
        reset_timestamp: Optional[bool] = False
    ):
        user_id = interaction.user.id
        existing = await self.db.get_track(user_id, track_id)
        if not existing:
            await interaction.response.send_message(f"Track `#{track_id}` not found.", ephemeral=True)
            return

        # Literal "NONE" clears a filter. Normalized to "" (not None) BEFORE the
        # merge below, since None here means "keep existing value".
        include = self._clear_filter(include)
        exclude = self._clear_filter(exclude)
        series = self._clear_filter(series)
        character = self._clear_filter(character)
        category = self._clear_filter(category)
        artist = self._clear_filter(artist)
        language = self._clear_filter(language)

        new_include = include if include is not None else existing["raw_include"]
        new_exclude = exclude if exclude is not None else existing["raw_exclude"]
        new_series = series if series is not None else existing["series"]
        new_character = character if character is not None else existing.get("character")
        new_category = category if category is not None else existing["category"]
        new_artist = artist if artist is not None else existing["artist"]
        new_language = language if language is not None else existing["language"]
        new_ts = datetime.now(timezone.utc) if reset_timestamp else None

        await self.db.update_track(
            user_id=user_id,
            track_id=track_id,
            raw_include=new_include,
            raw_exclude=new_exclude,
            series=new_series,
            character=new_character,
            category=new_category,
            artist=new_artist,
            language=new_language,
            timestamp=new_ts
        )

        updated_record = {
            "track_id": track_id,
            "user_id": user_id,
            "raw_include": new_include,
            "raw_exclude": new_exclude,
            "series": new_series,
            "character": new_character,
            "category": new_category,
            "artist": new_artist,
            "language": new_language,
            "last_checked_timestamp": new_ts or existing["last_checked_timestamp"]
        }
        self.active_tracks[track_id] = self._build_ast_dict(updated_record)

        await interaction.response.send_message(f"Track `#{track_id}` updated successfully.", ephemeral=True)

    @app_commands.command(name="listtrack", description="List your active tracking queries.")
    @app_commands.dm_only()
    async def listtrack(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        records = await self.db.get_user_tracks(user_id)
        if not records:
            await interaction.response.send_message("No active tracking queries found.", ephemeral=True)
            return

        embed = discord.Embed(
            title="📋 Active Hitomi Track Queries",
            color=discord.Color.gold(),
            timestamp=datetime.now(timezone.utc)
        )

        # Discord allows at most 25 fields per embed
        shown = records[:25]
        if len(records) > len(shown):
            embed.description = f"Showing first {len(shown)} of {len(records)} tracking rules."

        for r in shown:
            ts = self._ensure_aware(r["last_checked_timestamp"])
            field_value = (
                f"**Include:** `{r['raw_include'] or '*'}`\n"
                f"**Exclude:** `{r['raw_exclude'] or 'None'}`\n"
                f"**Artist:** `{r['artist'] or 'Any'}` | **Char:** `{r['character'] or 'Any'}`\n"
                f"**Series:** `{r['series'] or 'Any'}` | **Type:** `{r['category'] or 'Any'}`\n"
                f"**Lang:** `{r['language'] or 'Any'}` | **Since:** <t:{int(ts.timestamp())}:R>"
            )
            embed.add_field(name=f"Track ID: #{r['track_id']}", value=field_value, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="deletetrack", description="Delete an active tracking query.")
    @app_commands.dm_only()
    async def deletetrack(self, interaction: discord.Interaction, track_id: int):
        user_id = interaction.user.id
        if await self.db.delete_track(user_id, track_id):
            self.active_tracks.pop(track_id, None)
            await interaction.response.send_message(f"Track `#{track_id}` removed.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Track `#{track_id}` not found.", ephemeral=True)

    # --- Background Evaluation Worker ---

    @tasks.loop(seconds=30.0)
    async def tracker_loop(self):
        if not self.active_tracks:
            return

        recent_galleries = await self.fetch_recent_galleries()
        for gallery in recent_galleries:
            if not isinstance(gallery, dict):
                continue

            # Null-safe extraction (crawlers may emit explicit JSON nulls)
            gallery_time = gallery.get("timestamp") or datetime.now(timezone.utc)
            if gallery_time.tzinfo is None:
                gallery_time = gallery_time.replace(tzinfo=timezone.utc)
            tags = gallery.get("tags") or []
            artists = gallery.get("artists") or []
            characters = gallery.get("characters") or []
            series = gallery.get("parodys") or []
            language = gallery.get("language") or ""
            category = gallery.get("type") or ""

            for track_id, rule in list(self.active_tracks.items()):
                if gallery_time <= rule["timestamp"]:
                    continue

                # Universal boolean evaluation across all fields
                if not BooleanQueryParser.evaluate(rule["tag_ast"], tags):
                    continue
                if not BooleanQueryParser.evaluate(rule["artist_ast"], artists):
                    continue
                if not BooleanQueryParser.evaluate(rule["character_ast"], characters):
                    continue
                if not BooleanQueryParser.evaluate(rule["series_ast"], series):
                    continue
                if not BooleanQueryParser.evaluate(rule["language_ast"], language):
                    continue
                if not BooleanQueryParser.evaluate(rule["category_ast"], category):
                    continue

                # Match satisfied: notify and update cutoff.
                # Isolated so one failing DM/db write doesn't abort the whole batch.
                try:
                    await self.notify_user(rule["user_id"], gallery)
                    rule["timestamp"] = gallery_time
                    await self.db.update_track_timestamp(track_id, gallery_time)
                except Exception:
                    continue

    async def notify_user(self, user_id: int, gallery: Dict[str, Any]):
        user = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
        if not user:
            return

        gallery_id = gallery.get("id")
        files = gallery.get("files") or []
        thumbnail_file = None

        if files and self.session:
            thumb_url = get_thumbnail_url(gallery_id, files[0])
            if thumb_url:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    "Referer": f"https://hitomi.la/galleries/{gallery_id}.html"
                }
                try:
                    async with self.session.get(thumb_url, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                        if resp.status == 200:
                            image_bytes = await resp.read()
                            # get_thumbnail_url always returns a .webp URL
                            thumbnail_file = discord.File(io.BytesIO(image_bytes), filename="cover.webp")
                except Exception:
                    thumbnail_file = None

        embed = discord.Embed(
            title=gallery.get("title") or "Unknown Title",
            url=f"https://hitomi.la/galleries/{gallery_id}.html",
            color=discord.Color.blue(),
            timestamp=gallery.get("timestamp") or datetime.now(timezone.utc)
        )

        if embed.timestamp.tzinfo is None:
            embed.timestamp = embed.timestamp.replace(tzinfo=timezone.utc)

        if thumbnail_file:
            embed.set_thumbnail(url=f"attachment://{thumbnail_file.filename}")

        embed.add_field(name="Artist", value=", ".join(gallery.get("artists") or []) or "N/A", inline=True)
        embed.add_field(name="Series", value=", ".join(gallery.get("parodys") or []) or "Original", inline=True)
        embed.add_field(name="Character", value=", ".join(gallery.get("characters") or []) or "N/A", inline=True)
        embed.add_field(name="Language", value=str(gallery.get("language") or "N/A"), inline=True)
        embed.add_field(name="Type", value=str(gallery.get("type") or "N/A"), inline=True)
        embed.add_field(name="Tags", value=", ".join(gallery.get("tags") or [])[:1024] or "None", inline=False)

        try:
            if thumbnail_file:
                await user.send(embed=embed, file=thumbnail_file)
            else:
                await user.send(embed=embed)
        except (discord.Forbidden, discord.HTTPException):
            pass

    @staticmethod
    def _parse_nozomi_ids(data: bytes) -> list:
        """Parses a .nozomi payload: big-endian uint32 galleryblock IDs, newest-first."""
        n = len(data) // 4
        return list(struct.unpack(f">{n}I", data[: n * 4]))

    @staticmethod
    def _index_urls_for(record: Dict[str, Any]) -> set:
        """Maps a track record to hitomi nozomi search-index URLs.

        Index scheme (verified live):
            {cdn}/type/{category}-{language}.nozomi
        Values are lowercase; empty side becomes 'all'; multi-values split on '|'.
        """
        def split_values(field: Optional[str]) -> list:
            if not field:
                return []
            return [v.strip().strip('"').lower() for v in field.split("|") if v.strip().strip('"')]

        categories = split_values(record.get("category")) or ["all"]
        languages = split_values(record.get("language")) or ["all"]

        urls = set()
        for cat in categories:
            for lang in languages:
                urls.add(f"{HITOMI_CDN}/type/{quote(cat)}-{quote(lang)}.nozomi")
        return urls

    @staticmethod
    def _parse_gallery_timestamp(info: Dict[str, Any]) -> datetime:
        raw = info.get("date") or info.get("datepublished")
        ts = None
        if raw:
            s = str(raw)
            # hitomi sometimes emits short UTC offsets like '+09' which
            # fromisoformat rejects -> normalize to '+09:00'
            if re.search(r"[+-]\d{2}$", s):
                s += ":00"
            try:
                ts = datetime.fromisoformat(s)
            except ValueError:
                ts = None
        if ts is None:
            return datetime.now(timezone.utc)
        return ts.replace(tzinfo=timezone.utc) if ts.tzinfo is None else ts

    def _normalize_gallery_info(self, info: Dict[str, Any]) -> Dict[str, Any]:
        """Converts raw galleries/{id}.js JSON into the crawler dict shape the loop expects."""
        return {
            "id": info["id"],
            "title": info.get("title") or "Unknown Title",
            "artists": [a.get("artist", "") for a in (info.get("artists") or [])],
            "parodys": [p.get("parody", "") for p in (info.get("parodys") or [])],
            "characters": [c.get("character", "") for c in (info.get("characters") or [])],
            "language": info.get("language") or "",
            "type": info.get("type") or "",
            "tags": [t.get("tag", "") for t in (info.get("tags") or [])],
            "timestamp": self._parse_gallery_timestamp(info),
            "files": info.get("files") or [],
        }

    async def _fetch_gallery_info(self, session: aiohttp.ClientSession, gallery_id: int):
        url = f"{HITOMI_CDN}/galleries/{gallery_id}.js"
        try:
            async with session.get(url, headers=HITOMI_HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    return None
                text = await resp.text()
        except Exception as e:
            print(f"[track] metadata fetch failed for {gallery_id}: {e}")
            return None
        try:
            info = json.loads(text.partition("=")[2].strip().rstrip(";"))
        except (ValueError, IndexError):
            return None
        return self._normalize_gallery_info(info)

    async def fetch_recent_galleries(self) -> list:
        """Crawls hitomi.la search indexes derived from active rules and returns
        normalized gallery dicts newer than what has already been processed."""
        if not self.session or self.session.closed or not self.active_tracks:
            return []

        index_urls = set()
        for rule in self.active_tracks.values():
            index_urls |= self._index_urls_for(rule["raw"])
        if not index_urls:
            return []

        candidate_ids = []
        # Hitomi's CDN truncates large plain GETs on .nozomi files (>1MB), so
        # read only the head slice we need via a Range request (their frontend
        # does the same); servers ignoring Range return 200 with the full body.
        index_headers = {**HITOMI_HEADERS, "Range": f"bytes=0-{NOZOMI_SCAN_DEPTH * 4 - 1}"}
        for url in index_urls:
            try:
                async with self.session.get(url, headers=index_headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status not in (200, 206):
                        print(f"[track] index unavailable ({resp.status}): {url}")
                        continue
                    data = await resp.read()
            except Exception as e:
                print(f"[track] index fetch failed: {url} ({e})")
                continue
            candidate_ids.extend(
                self._parse_nozomi_ids(data[: NOZOMI_SCAN_DEPTH * 4])[:NOZOMI_SCAN_DEPTH]
            )

        unseen = []
        seen_now = self._seen_ids
        for gid in candidate_ids:
            if gid not in seen_now:
                seen_now[gid] = None
                unseen.append(gid)
        # Trim ordered-set cache to bound memory
        if len(seen_now) > SEEN_CACHE_MAX:
            for old in list(seen_now.keys())[: len(seen_now) - SEEN_CACHE_MAX // 2]:
                del seen_now[old]
        if not unseen:
            return []

        semaphore = asyncio.Semaphore(METADATA_CONCURRENCY)

        async def bounded(gid):
            async with semaphore:
                return await self._fetch_gallery_info(self.session, gid)

        results = await asyncio.gather(*(bounded(g) for g in unseen))
        return [g for g in results if g]

    @tracker_loop.before_loop
    async def before_tracker(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(TrackCog(bot))
