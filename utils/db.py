import aiosqlite
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

class TrackDatabase:
    def __init__(self, db_path: str = "tracks.db"):
        self.db_path = db_path

    async def init(self) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS tracks (
                    track_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    raw_include TEXT,
                    raw_exclude TEXT,
                    series TEXT,
                    character TEXT,
                    category TEXT,
                    artist TEXT,
                    language TEXT,
                    last_checked_timestamp TEXT NOT NULL
                )
            """)
            # Migration check in case the table already existed without character
            async with db.execute("PRAGMA table_info(tracks)") as cursor:
                columns = [row[1] for row in await cursor.fetchall()]
                if "character" not in columns:
                    await db.execute("ALTER TABLE tracks ADD COLUMN character TEXT")
            await db.commit()

    async def add_track(
        self,
        user_id: int,
        raw_include: Optional[str],
        raw_exclude: Optional[str],
        series: Optional[str],
        character: Optional[str],
        category: Optional[str],
        artist: Optional[str],
        language: Optional[str]
    ) -> int:
        now_iso = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO tracks (
                    user_id, raw_include, raw_exclude, series, character, category, artist, language, last_checked_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, raw_include, raw_exclude, series, character, category, artist, language, now_iso))
            await db.commit()
            return cursor.lastrowid

    async def get_track(self, user_id: int, track_id: int) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM tracks WHERE track_id = ? AND user_id = ?",
                (track_id, user_id)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def get_user_tracks(self, user_id: int) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM tracks WHERE user_id = ?", (user_id,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_all_tracks(self) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM tracks") as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def update_track_timestamp(self, track_id: int, timestamp: datetime) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE tracks SET last_checked_timestamp = ? WHERE track_id = ?",
                (timestamp.isoformat(), track_id)
            )
            await db.commit()

    async def update_track(
        self,
        user_id: int,
        track_id: int,
        raw_include: Optional[str] = None,
        raw_exclude: Optional[str] = None,
        series: Optional[str] = None,
        character: Optional[str] = None,
        category: Optional[str] = None,
        artist: Optional[str] = None,
        language: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> bool:
        existing = await self.get_track(user_id, track_id)
        if not existing:
            return False

        updated_include = raw_include if raw_include is not None else existing["raw_include"]
        updated_exclude = raw_exclude if raw_exclude is not None else existing["raw_exclude"]
        updated_series = series if series is not None else existing["series"]
        updated_character = character if character is not None else existing.get("character")
        updated_category = category if category is not None else existing["category"]
        updated_artist = artist if artist is not None else existing["artist"]
        updated_language = language if language is not None else existing["language"]
        updated_timestamp = (
            timestamp.isoformat() if timestamp is not None else existing["last_checked_timestamp"]
        )

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                UPDATE tracks
                SET raw_include = ?,
                    raw_exclude = ?,
                    series = ?,
                    character = ?,
                    category = ?,
                    artist = ?,
                    language = ?,
                    last_checked_timestamp = ?
                WHERE track_id = ? AND user_id = ?
            """, (
                updated_include,
                updated_exclude,
                updated_series,
                updated_character,
                updated_category,
                updated_artist,
                updated_language,
                updated_timestamp,
                track_id,
                user_id
            ))
            await db.commit()
            return cursor.rowcount > 0

    async def delete_track(self, user_id: int, track_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM tracks WHERE track_id = ? AND user_id = ?",
                (track_id, user_id)
            )
            await db.commit()
            return cursor.rowcount > 0
