import discord
import asyncio
import json
import os
import aiohttp
from datetime import datetime, timezone
from discord import app_commands
from discord.ext import commands, tasks

from utils.hitomi import (
    search,
    gallery_info,
    thumb_url,
    page_url,
    parse_gallery_date,
    extract_tags,
    extract_artists,
    extract_series,
)

FILE_PATH = os.path.expanduser("~/.local/state/aronaldo")
os.makedirs(FILE_PATH, exist_ok=True)
FILE_PATH = os.path.join(FILE_PATH, "tracks.json")


def load_tracks():
    try:
        with open(FILE_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {"next_id": 1, "tracks": []}


async def save_tracks(data):
    with open(FILE_PATH, "w") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def is_dm():
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.guild is not None:
            await interaction.response.send_message(
                "Lệnh này chỉ dùng trong DM!", ephemeral=True
            )
            return False
        return True
    return app_commands.check(predicate)


class track(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_tracks()
        self.session = None
        self.crawl_loop.start()

    async def _get_session(self):
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(ssl=False)
            self.session = aiohttp.ClientSession(connector=connector)
        return self.session

    def cog_unload(self):
        self.crawl_loop.cancel()
        if self.session and not self.session.closed:
            asyncio.create_task(self.session.close())

    @tasks.loop(seconds=5)
    async def crawl_loop(self):
        session = await self._get_session()
        for track_entry in self.data["tracks"][:]:
            try:
                include = track_entry.get("include", "")
                exclude = track_entry.get("exclude", "")
                series = track_entry.get("series", "")
                category = track_entry.get("category", "")
                artist = track_entry.get("artist", "")
                language = track_entry.get("language", "japanese")
                ts_str = track_entry.get("timestamp", "")
                ts = parse_gallery_date(ts_str)
                if ts is None:
                    continue

                gids = await search(
                    session,
                    include,
                    exclude,
                    language=language,
                    category=category,
                    series=series,
                    artist=artist,
                    limit=300,
                )
                seen = set(track_entry.get("seen_galleries", []))
                new_ids = [gid for gid in gids if gid not in seen]

                if not new_ids:
                    continue

                user = self.bot.get_user(track_entry["user_id"])
                if user is None:
                    continue

                notified = []
                for gid in new_ids:
                    info = await gallery_info(session, gid)
                    if info is None:
                        continue

                    gallery_date = parse_gallery_date(info.get("date", ""))
                    if gallery_date is None:
                        continue

                    gallery_dt_naive = gallery_date.replace(tzinfo=None) if gallery_date.tzinfo else gallery_date
                    if gallery_dt_naive <= ts:
                        continue

                    artists = extract_artists(info)
                    tags = extract_tags(info)
                    url = page_url(info)

                    if info.get("files"):
                        cover = thumb_url(info["files"][0]["hash"])
                    else:
                        cover = None

                    emb = discord.Embed(
                        title=info.get("title", "Untitled"),
                        url=url,
                        color=0xBA30FF,
                        timestamp=gallery_date.replace(tzinfo=timezone.utc) if gallery_date.tzinfo is None else gallery_date,
                    )
                    if cover:
                        emb.set_image(url=cover)
                    emb.set_thumbnail(url="https://i.ibb.co/HTCpvDNW/aronaldo.png")
                    if artists:
                        emb.add_field(name="Artist", value=", ".join(artists), inline=True)
                    series_list = extract_series(info)
                    if series_list:
                        emb.add_field(name="Series", value=", ".join(series_list), inline=True)
                    if tags:
                        emb.add_field(name="Tags", value=", ".join(tags[:15]), inline=False)
                    emb.add_field(name="🔗 Gallery", value=f"[Xem trên hitomi.la]({url})", inline=False)
                    emb.add_field(name="📦 Download", value=f"[Tải về]({url})", inline=False)
                    emb.set_footer(text=f"Track #{track_entry['id']}")

                    try:
                        await user.send(embed=emb)
                        notified.append(gid)
                    except discord.Forbidden:
                        pass

                if notified:
                    track_entry["seen_galleries"] = list(seen | set(notified))
                    await save_tracks(self.data)

            except Exception:
                continue

    @crawl_loop.before_loop
    async def before_crawl_loop(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="addtrack", description="Thêm track mới (DM only)")
    @app_commands.describe(
        include="Tags cần include. AND: espacio, OR: |, Group: (). Dùng _ thay khoảng trắng trong tag",
        exclude="Tags exclude, mỗi từ có '-' trước",
        series="Series/parodyparody cần track (vd: blue_archive). Để trống nếu không cần",
        category="Loại gallery (mặc định: doujinshi). Vd: doujinshi, manga, artistcg",
        artist="Artist cần track (vd: kujou_danbo). Để trống nếu không cần",
        language="Ngôn ngữ (mặc định: japanese)",
        timestamp="Thời gian (mặc định: hiện tại). Format: YYYY-MM-DD HH:MM:SS",
    )
    @is_dm()
    async def addtrack(
        self,
        interaction: discord.Interaction,
        include: str = "",
        exclude: str = "",
        series: str = "",
        category: str = "doujinshi",
        artist: str = "",
        language: str = "japanese",
        timestamp: str = "",
    ):
        await interaction.response.defer(ephemeral=True)

        if timestamp:
            ts = parse_gallery_date(timestamp)
            if ts is None:
                await interaction.followup.send(
                    "Format timestamp không hợp lệ! Dùng: `YYYY-MM-DD HH:MM:SS`"
                )
                return
            ts_str = timestamp
        else:
            ts_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        track_id = self.data["next_id"]
        self.data["next_id"] += 1
        entry = {
            "id": track_id,
            "user_id": interaction.user.id,
            "include": include,
            "exclude": exclude,
            "series": series,
            "category": category,
            "artist": artist,
            "language": language,
            "timestamp": ts_str,
            "seen_galleries": [],
        }
        self.data["tracks"].append(entry)
        await save_tracks(self.data)

        emb = discord.Embed(title=f"Đã thêm Track #{track_id}", color=0x2E8B57)
        emb.add_field(name="Include", value=f"`{include}`", inline=False)
        if exclude:
            emb.add_field(name="Exclude", value=f"`{exclude}`", inline=False)
        if series:
            emb.add_field(name="Series", value=f"`{series}`", inline=True)
        emb.add_field(name="Category", value=f"`{category}`", inline=True)
        if artist:
            emb.add_field(name="Artist", value=f"`{artist}`", inline=True)
        emb.add_field(name="Language", value=f"`{language}`", inline=True)
        emb.add_field(name="Timestamp", value=f"`{ts_str}`", inline=False)
        await interaction.followup.send(embed=emb)

    @app_commands.command(name="edittrack", description="Sửa track (DM only)")
    @app_commands.describe(
        track_id="ID của track",
        include="Tags include mới",
        exclude="Tags exclude mới",
        series="Series/parody mới",
        category="Category mới",
        artist="Artist mới",
        language="Language mới",
        timestamp="Timestamp mới",
    )
    @is_dm()
    async def edittrack(
        self,
        interaction: discord.Interaction,
        track_id: int,
        include: str = "",
        exclude: str = "",
        series: str = "",
        category: str = "",
        artist: str = "",
        language: str = "",
        timestamp: str = "",
    ):
        await interaction.response.defer(ephemeral=True)

        entry = None
        for t in self.data["tracks"]:
            if t["id"] == track_id and t["user_id"] == interaction.user.id:
                entry = t
                break

        if entry is None:
            await interaction.followup.send(f"Không tìm thấy Track #{track_id}!")
            return

        if include:
            entry["include"] = include
        if exclude:
            entry["exclude"] = exclude
        if series:
            entry["series"] = series
        if category:
            entry["category"] = category
        if artist:
            entry["artist"] = artist
        if language:
            entry["language"] = language
        if timestamp:
            ts = parse_gallery_date(timestamp)
            if ts is None:
                await interaction.followup.send(
                    "Format timestamp không hợp lệ! Dùng: `YYYY-MM-DD HH:MM:SS`"
                )
                return
            entry["timestamp"] = timestamp

        await save_tracks(self.data)

        emb = discord.Embed(title=f"Đã cập nhật Track #{track_id}", color=0x2E8B57)
        emb.add_field(name="Include", value=f"`{entry['include']}`", inline=False)
        if entry.get("exclude"):
            emb.add_field(name="Exclude", value=f"`{entry['exclude']}`", inline=False)
        if entry.get("series"):
            emb.add_field(name="Series", value=f"`{entry['series']}`", inline=True)
        emb.add_field(name="Category", value=f"`{entry.get('category', '')}`", inline=True)
        if entry.get("artist"):
            emb.add_field(name="Artist", value=f"`{entry['artist']}`", inline=True)
        emb.add_field(name="Language", value=f"`{entry.get('language', 'japanese')}`", inline=True)
        emb.add_field(name="Timestamp", value=f"`{entry['timestamp']}`", inline=False)
        await interaction.followup.send(embed=emb)

    @app_commands.command(name="deletetrack", description="Xóa track (DM only)")
    @app_commands.describe(track_id="ID của track cần xóa")
    @is_dm()
    async def deletetrack(
        self,
        interaction: discord.Interaction,
        track_id: int,
    ):
        await interaction.response.defer(ephemeral=True)

        found = False
        for i, t in enumerate(self.data["tracks"]):
            if t["id"] == track_id and t["user_id"] == interaction.user.id:
                self.data["tracks"].pop(i)
                found = True
                break

        if not found:
            await interaction.followup.send(f"Không tìm thấy Track #{track_id}!")
            return

        await save_tracks(self.data)
        await interaction.followup.send(f"Đã xóa Track #{track_id}!")

    @app_commands.command(name="listtrack", description="Xem danh sách track (DM only)")
    @is_dm()
    async def listtrack(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        user_tracks = [
            t for t in self.data["tracks"] if t["user_id"] == interaction.user.id
        ]
        if not user_tracks:
            await interaction.followup.send("Bạn chưa có track nào!")
            return

        emb = discord.Embed(title="Danh sách Track", color=0xBA30FF)
        for t in user_tracks:
            value = f"**Include:** `{t['include']}`"
            if t.get("exclude"):
                value += f"\n**Exclude:** `{t['exclude']}`"
            if t.get("series"):
                value += f"\n**Series:** `{t['series']}`"
            value += f"\n**Category:** `{t.get('category', '')}`"
            if t.get("artist"):
                value += f"\n**Artist:** `{t['artist']}`"
            value += f"\n**Language:** `{t.get('language', 'japanese')}`"
            value += f"\n**Since:** `{t['timestamp']}`"
            value += f"\n**Seen:** {len(t.get('seen_galleries', []))} galleries"
            emb.add_field(name=f"Track #{t['id']}", value=value, inline=False)

        await interaction.followup.send(embed=emb)


async def setup(bot):
    await bot.add_cog(track(bot))
