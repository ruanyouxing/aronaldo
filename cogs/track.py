import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timezone
import aiohttp
from typing import Optional, Dict, Any

from utils.hitomi import TagQueryEvaluator
from utils.db import TrackDatabase

class TrackCog(commands.Cog, name="track"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = TrackDatabase()
        self.active_tracks: Dict[int, Dict[str, Any]] = {}

    async def cog_load(self):
        await self.db.init()
        await self._load_tracks_into_cache()
        self.tracker_loop.start()

    def cog_unload(self):
        self.tracker_loop.cancel()

    async def _load_tracks_into_cache(self):
        self.active_tracks.clear()
        records = await self.db.get_all_tracks()
        for record in records:
            include = record["raw_include"] or ""
            exclude = record["raw_exclude"] or ""
            clean_exclude = " ".join([f"-{t.strip('-')}" for t in exclude.split() if t])
            parts = [p for p in [include, clean_exclude] if p]
            combined_query = " ".join(parts).strip()

            ast = TagQueryEvaluator(combined_query).parse() if combined_query else None
            ts = datetime.fromisoformat(record["last_checked_timestamp"])

            self.active_tracks[record["track_id"]] = {
                "user_id": record["user_id"],
                "query_ast": ast,
                "series": record["series"],
                "character": record.get("character"),
                "category": record["category"],
                "artist": record["artist"],
                "language": record["language"],
                "timestamp": ts
            }

    # --- Slash Commands (DM Only) ---

    @app_commands.command(name="addtrack", description="Add a new gallery tracking query.")
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
        
        track_id = await self.db.add_track(
            user_id=user_id,
            raw_include=include,
            raw_exclude=exclude,
            series=series.lower() if series else None,
            character=character.lower().replace(" ", "_") if character else None,
            category=category.lower() if category else None,
            artist=artist.lower() if artist else None,
            language=language.lower() if language else None
        )

        clean_exclude = " ".join([f"-{t.strip('-')}" for t in exclude.split() if t]) if exclude else ""
        parts = [p for p in [include, clean_exclude] if p]
        combined_query = " ".join(parts).strip()
        ast = TagQueryEvaluator(combined_query).parse() if combined_query else None

        self.active_tracks[track_id] = {
            "user_id": user_id,
            "query_ast": ast,
            "series": series.lower() if series else None,
            "character": character.lower().replace(" ", "_") if character else None,
            "category": category.lower() if category else None,
            "artist": artist.lower() if artist else None,
            "language": language.lower() if language else None,
            "timestamp": datetime.now(timezone.utc)
        }

        display_query = combined_query if combined_query else "*All tags*"
        await interaction.response.send_message(
            f"Tracking registered successfully with ID `#{track_id}`.\n"
            f"**Tags:** `{display_query}` | **Artist:** `{artist or 'Any'}` | **Char:** `{character or 'Any'}` | **Category:** `{category or 'Any'}` | **Lang:** `{language or 'Any'}`",
            ephemeral=True
        )

    @app_commands.command(name="edittrack", description="Edit an existing tracking query.")
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
            await interaction.response.send_message(
                f"Track `#{track_id}` was not found in your active tracking list.",
                ephemeral=True
            )
            return

        new_include = include if include is not None else existing["raw_include"]
        new_exclude = exclude if exclude is not None else existing["raw_exclude"]
        new_series = series.lower() if series is not None else existing["series"]
        new_character = character.lower().replace(" ", "_") if character is not None else existing.get("character")
        new_category = category.lower() if category is not None else existing["category"]
        new_artist = artist.lower() if artist is not None else existing["artist"]
        new_language = language.lower() if language is not None else existing["language"]
        new_timestamp = datetime.now(timezone.utc) if reset_timestamp else None

        success = await self.db.update_track(
            user_id=user_id,
            track_id=track_id,
            raw_include=new_include,
            raw_exclude=new_exclude,
            series=new_series,
            character=new_character,
            category=new_category,
            artist=new_artist,
            language=new_language,
            timestamp=new_timestamp
        )

        if not success:
            await interaction.response.send_message(
                f"Failed to update track `#{track_id}`.",
                ephemeral=True
            )
            return

        clean_exclude = " ".join([f"-{t.strip('-')}" for t in new_exclude.split() if t]) if new_exclude else ""
        parts = [p for p in [new_include, clean_exclude] if p]
        combined_query = " ".join(parts).strip()
        new_ast = TagQueryEvaluator(combined_query).parse() if combined_query else None

        current_cached_ts = self.active_tracks.get(track_id, {}).get(
            "timestamp", datetime.fromisoformat(existing["last_checked_timestamp"])
        )

        self.active_tracks[track_id] = {
            "user_id": user_id,
            "query_ast": new_ast,
            "series": new_series,
            "character": new_character,
            "category": new_category,
            "artist": new_artist,
            "language": new_language,
            "timestamp": new_timestamp or current_cached_ts
        }

        display_query = combined_query if combined_query else "*All tags*"
        await interaction.response.send_message(
            f"Track `#{track_id}` updated successfully.\n"
            f"**Tags:** `{display_query}` | **Artist:** `{new_artist or 'Any'}` | **Char:** `{new_character or 'Any'}` | "
            f"**Category:** `{new_category or 'Any'}` | **Lang:** `{new_language or 'Any'}`",
            ephemeral=True
        )

    @app_commands.command(name="listtrack", description="List all of your active tracking queries.")
    @app_commands.dm_only()
    async def listtrack(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        user_records = await self.db.get_user_tracks(user_id)

        if not user_records:
            await interaction.response.send_message(
                "You currently have no active tracking queries. Use `/addtrack` to create one.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="📋 Active Hitomi Track Queries",
            description=f"You have **{len(user_records)}** active tracking rule(s).",
            color=discord.Color.gold(),
            timestamp=datetime.now(timezone.utc)
        )

        for record in user_records:
            track_id = record["track_id"]
            include_str = record["raw_include"] or "*None*"
            exclude_str = record["raw_exclude"] or "*None*"
            artist_str = record["artist"] or "*Any*"
            series_str = record["series"] or "*Any*"
            char_str = record.get("character") or "*Any*"
            cat_str = record["category"] or "*Any*"
            lang_str = record["language"] or "*Any*"
            ts = datetime.fromisoformat(record["last_checked_timestamp"])
            unix_ts = int(ts.timestamp())

            field_value = (
                f"**Include:** `{include_str}`\n"
                f"**Exclude:** `{exclude_str}`\n"
                f"**Filters:** Artist: `{artist_str}` | Series: `{series_str}` | Char: `{char_str}`\n"
                f"**Type:** `{cat_str}` | **Lang:** `{lang_str}`\n"
                f"**Since:** <t:{unix_ts}:R>"
            )

            embed.add_field(
                name=f"Track ID: #{track_id}",
                value=field_value,
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="deletetrack", description="Delete an active tracking ID.")
    @app_commands.dm_only()
    async def deletetrack(self, interaction: discord.Interaction, track_id: int):
        user_id = interaction.user.id
        deleted = await self.db.delete_track(user_id, track_id)

        if deleted:
            self.active_tracks.pop(track_id, None)
            await interaction.response.send_message(f"Track `#{track_id}` removed.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Track `#{track_id}` not found.", ephemeral=True)

    # --- Background Polling Worker ---

    @tasks.loop(seconds=30.0)
    async def tracker_loop(self):
        if not self.active_tracks:
            return

        async with aiohttp.ClientSession() as session:
            recent_galleries = await self.fetch_recent_galleries(session)
            
            for gallery in recent_galleries:
                gallery_tags = set(t.lower().replace(" ", "_") for t in gallery.get("tags", []))
                gallery_characters = [c.lower().replace(" ", "_") for c in gallery.get("characters", [])]
                gallery_time = gallery.get("timestamp", datetime.now(timezone.utc))

                for track_id, rule in list(self.active_tracks.items()):
                    if gallery_time <= rule["timestamp"]:
                        continue

                    if rule["language"] and gallery.get("language", "").lower() != rule["language"]:
                        continue
                    if rule["category"] and gallery.get("type", "").lower() != rule["category"]:
                        continue
                    if rule["artist"] and rule["artist"] not in [a.lower() for a in gallery.get("artists", [])]:
                        continue
                    if rule["series"] and rule["series"] not in [s.lower() for s in gallery.get("parodys", [])]:
                        continue
                    if rule["character"] and rule["character"] not in gallery_characters:
                        continue

                    if TagQueryEvaluator.evaluate(rule["query_ast"], gallery_tags):
                        await self.notify_user(rule["user_id"], gallery)
                        rule["timestamp"] = gallery_time
                        await self.db.update_track_timestamp(track_id, gallery_time)

    async def notify_user(self, user_id: int, gallery: Dict[str, Any]):
        user = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
        if not user:
            return

        embed = discord.Embed(
            title=gallery.get("title", "Unknown Title"),
            url=f"https://hitomi.la/galleries/{gallery['id']}.html",
            color=discord.Color.blue(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_thumbnail(url=gallery.get("thumbnail_url", ""))
        embed.add_field(name="Artist", value=", ".join(gallery.get("artists", ["N/A"])), inline=True)
        embed.add_field(name="Series", value=", ".join(gallery.get("parodys", ["Original"])), inline=True)
        embed.add_field(name="Character", value=", ".join(gallery.get("characters", ["N/A"])), inline=True)
        embed.add_field(name="Language", value=gallery.get("language", "N/A"), inline=True)
        embed.add_field(name="Type", value=gallery.get("type", "N/A"), inline=True)
        embed.add_field(name="Tags", value=", ".join(gallery.get("tags", []))[:1024] or "None", inline=False)

        try:
            await user.send(embed=embed)
        except discord.Forbidden:
            pass

    async def fetch_recent_galleries(self, session: aiohttp.ClientSession) -> list:
        return []

    @tracker_loop.before_loop
    async def before_tracker(self):
        await self.bot.wait_until_ready()

async def setup(bot: commands.Bot):
    await bot.add_cog(TrackCog(bot))
