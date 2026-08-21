import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timezone
import aiohttp
from typing import Optional, Dict, Any

from utils.hitomi import TagQueryEvaluator

class TrackCog(commands.Cog, name="track"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.tracks: Dict[int, Dict[int, Dict[str, Any]]] = {}
        self.track_counter: int = 1
        self.last_checked_id: Optional[int] = None
        self.tracker_loop.start()

    @app_commands.command(name="addtrack", description="Add a new gallery tracking query.")
    @app_commands.dm_only()
    async def addtrack(
        self,
        interaction: discord.Interaction,
        include: Optional[str] = None,
        exclude: Optional[str] = None,
        series: Optional[str] = "original",
        category: Optional[str] = "doujinshi",
        artist: Optional[str] = None,
        language: Optional[str] = "japanese"
    ):
        user_id = interaction.user.id
        if user_id not in self.tracks:
            self.tracks[user_id] = {}

        track_id = self.track_counter
        self.track_counter += 1

        clean_exclude = (
            " ".join([f"-{t.strip('-')}" for t in exclude.split() if t])
            if exclude else ""
        )
        parts = [p for p in [include, clean_exclude] if p]
        combined_query = " ".join(parts).strip()

        ast = TagQueryEvaluator(combined_query).parse() if combined_query else None

        self.tracks[user_id][track_id] = {
            "query_ast": ast,
            "series": series.lower() if series else None,
            "category": category.lower() if category else None,
            "artist": artist.lower() if artist else None,
            "language": language.lower() if language else None,
            "timestamp": datetime.now(timezone.utc),
            "raw_include": include or "None",
            "raw_exclude": exclude or "None"
        }

        display_query = combined_query if combined_query else "*All tags*"
        await interaction.response.send_message(
            f"Tracking registered successfully with ID `#{track_id}`.\n"
            f"**Tags:** `{display_query}` | **Artist:** `{artist or 'Any'}` | **Category:** `{category or 'Any'}` | **Lang:** `{language or 'Any'}`",
            ephemeral=True
        )

    @app_commands.command(name="deletetrack", description="Delete an active tracking ID.")
    @app_commands.dm_only()
    async def deletetrack(self, interaction: discord.Interaction, track_id: int):
        user_id = interaction.user.id
        if user_id in self.tracks and track_id in self.tracks[user_id]:
            del self.tracks[user_id][track_id]
            await interaction.response.send_message(f"Track `#{track_id}` removed.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Track `#{track_id}` not found.", ephemeral=True)

    # --- Background Polling Worker ---

    @tasks.loop(seconds=30.0)
    async def tracker_loop(self):
        """Single central worker that checks latest updates and notifies users."""
        if not any(self.tracks.values()):
            return

        async with aiohttp.ClientSession() as session:
            # Step 1: Fetch recent gallery updates (Replace with your actual metadata endpoint)
            recent_galleries = await self.fetch_recent_galleries(session)
            
            for gallery in recent_galleries:
                gallery_id = gallery.get("id")
                gallery_tags = set(t.lower().replace(" ", "_") for t in gallery.get("tags", []))
                gallery_time = gallery.get("timestamp", datetime.now(timezone.utc))

                # Step 2: Test against all user filters in memory
                for user_id, user_tracks in self.tracks.items():
                    for track_id, rule in list(user_tracks.items()):
                        if gallery_time <= rule["timestamp"]:
                            continue

                        # Metadata assertions
                        if rule["language"] and gallery.get("language", "").lower() != rule["language"]:
                            continue
                        if rule["category"] and gallery.get("type", "").lower() != rule["category"]:
                            continue
                        if rule["artist"] and rule["artist"] not in [a.lower() for a in gallery.get("artists", [])]:
                            continue
                        if rule["series"] and rule["series"] not in [s.lower() for s in gallery.get("parodys", [])]:
                            continue

                        # Boolean tag matching
                        if TagQueryEvaluator.evaluate(rule["query_ast"], gallery_tags):
                            await self.notify_user(user_id, gallery)
                            # Advance timestamp to avoid duplicate notifications
                            rule["timestamp"] = gallery_time

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
        embed.add_field(name="Language", value=gallery.get("language", "N/A"), inline=True)
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
    
