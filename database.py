"""Database models and schema for telemetry data persistence."""
import aiosqlite
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from config import settings


class Database:
    """Async SQLite database handler for telemetry data."""
    
    def __init__(self, db_path: str = "telemetry.db"):
        self.db_path = db_path
        self.connection = None
    
    async def connect(self):
        """Establish database connection."""
        self.connection = await aiosqlite.connect(self.db_path)
        await self._create_tables()
    
    async def close(self):
        """Close database connection."""
        if self.connection:
            await self.connection.close()
    
    async def _create_tables(self):
        """Create database tables if they don't exist."""
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS telemetry_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                vehicle_info TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS telemetry_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                pid TEXT NOT NULL,
                value REAL,
                unit TEXT,
                FOREIGN KEY (session_id) REFERENCES telemetry_sessions(session_id)
            )
        """)
        
        await self.connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_timestamp 
            ON telemetry_data(session_id, timestamp)
        """)
        
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS alert_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                pid TEXT NOT NULL,
                condition TEXT NOT NULL,
                threshold REAL NOT NULL,
                enabled BOOLEAN DEFAULT 1,
                email_notify BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS alert_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_config_id INTEGER,
                session_id TEXT,
                timestamp TIMESTAMP NOT NULL,
                pid TEXT NOT NULL,
                value REAL NOT NULL,
                message TEXT,
                FOREIGN KEY (alert_config_id) REFERENCES alert_configs(id)
            )
        """)
        
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                role TEXT DEFAULT 'viewer',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await self.connection.commit()
    
    async def create_session(self, session_id: str, vehicle_info: Optional[Dict] = None) -> int:
        """Create a new telemetry session."""
        cursor = await self.connection.execute(
            """INSERT INTO telemetry_sessions (session_id, start_time, vehicle_info)
               VALUES (?, ?, ?)""",
            (session_id, datetime.now(), json.dumps(vehicle_info) if vehicle_info else None)
        )
        await self.connection.commit()
        return cursor.lastrowid
    
    async def end_session(self, session_id: str):
        """Mark a session as ended."""
        await self.connection.execute(
            """UPDATE telemetry_sessions SET end_time = ? WHERE session_id = ?""",
            (datetime.now(), session_id)
        )
        await self.connection.commit()
    
    async def insert_telemetry(self, session_id: str, pid: str, value: float, 
                               unit: str, timestamp: Optional[datetime] = None):
        """Insert a telemetry data point."""
        if timestamp is None:
            timestamp = datetime.now()
        
        await self.connection.execute(
            """INSERT INTO telemetry_data (session_id, timestamp, pid, value, unit)
               VALUES (?, ?, ?, ?, ?)""",
            (session_id, timestamp, pid, value, unit)
        )
        await self.connection.commit()
    
    async def get_recent_telemetry(self, session_id: str, seconds: int = 600) -> List[Dict]:
        """Get recent telemetry data within the rolling buffer window."""
        cutoff = datetime.now() - timedelta(seconds=seconds)
        cursor = await self.connection.execute(
            """SELECT timestamp, pid, value, unit 
               FROM telemetry_data 
               WHERE session_id = ? AND timestamp > ?
               ORDER BY timestamp DESC""",
            (session_id, cutoff)
        )
        rows = await cursor.fetchall()
        return [
            {
                "timestamp": row[0],
                "pid": row[1],
                "value": row[2],
                "unit": row[3]
            }
            for row in rows
        ]
    
    async def get_session_data(self, session_id: str, start_time: Optional[datetime] = None,
                               end_time: Optional[datetime] = None) -> List[Dict]:
        """Get all telemetry data for a session within a time range."""
        query = """SELECT timestamp, pid, value, unit 
                   FROM telemetry_data 
                   WHERE session_id = ?"""
        params = [session_id]
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)
        
        query += " ORDER BY timestamp ASC"
        
        cursor = await self.connection.execute(query, params)
        rows = await cursor.fetchall()
        return [
            {
                "timestamp": row[0],
                "pid": row[1],
                "value": row[2],
                "unit": row[3]
            }
            for row in rows
        ]
    
    async def list_sessions(self, limit: int = 100) -> List[Dict]:
        """List all telemetry sessions."""
        cursor = await self.connection.execute(
            """SELECT session_id, start_time, end_time, vehicle_info
               FROM telemetry_sessions
               ORDER BY start_time DESC
               LIMIT ?""",
            (limit,)
        )
        rows = await cursor.fetchall()
        return [
            {
                "session_id": row[0],
                "start_time": row[1],
                "end_time": row[2],
                "vehicle_info": json.loads(row[3]) if row[3] else None
            }
            for row in rows
        ]
    
    async def cleanup_old_data(self, days: int = 30):
        """Clean up telemetry data older than specified days."""
        cutoff = datetime.now() - timedelta(days=days)
        await self.connection.execute(
            """DELETE FROM telemetry_data WHERE timestamp < ?""",
            (cutoff,)
        )
        await self.connection.commit()
    
    # Alert configuration methods
    async def create_alert(self, name: str, pid: str, condition: str, 
                          threshold: float, email_notify: bool = False) -> int:
        """Create a new alert configuration."""
        cursor = await self.connection.execute(
            """INSERT INTO alert_configs (name, pid, condition, threshold, email_notify)
               VALUES (?, ?, ?, ?, ?)""",
            (name, pid, condition, threshold, email_notify)
        )
        await self.connection.commit()
        return cursor.lastrowid
    
    async def get_alerts(self, enabled_only: bool = True) -> List[Dict]:
        """Get all alert configurations."""
        query = "SELECT id, name, pid, condition, threshold, enabled, email_notify FROM alert_configs"
        if enabled_only:
            query += " WHERE enabled = 1"
        
        cursor = await self.connection.execute(query)
        rows = await cursor.fetchall()
        return [
            {
                "id": row[0],
                "name": row[1],
                "pid": row[2],
                "condition": row[3],
                "threshold": row[4],
                "enabled": bool(row[5]),
                "email_notify": bool(row[6])
            }
            for row in rows
        ]
    
    async def log_alert(self, alert_config_id: int, session_id: str, 
                       pid: str, value: float, message: str):
        """Log an alert trigger."""
        await self.connection.execute(
            """INSERT INTO alert_history 
               (alert_config_id, session_id, timestamp, pid, value, message)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (alert_config_id, session_id, datetime.now(), pid, value, message)
        )
        await self.connection.commit()
    
    # User management methods
    async def create_user(self, username: str, email: str, 
                         hashed_password: str, role: str = "viewer") -> int:
        """Create a new user."""
        cursor = await self.connection.execute(
            """INSERT INTO users (username, email, hashed_password, role)
               VALUES (?, ?, ?, ?)""",
            (username, email, hashed_password, role)
        )
        await self.connection.commit()
        return cursor.lastrowid
    
    async def get_user(self, username: str) -> Optional[Dict]:
        """Get user by username."""
        cursor = await self.connection.execute(
            """SELECT id, username, email, hashed_password, role, is_active
               FROM users WHERE username = ?""",
            (username,)
        )
        row = await cursor.fetchone()
        if row:
            return {
                "id": row[0],
                "username": row[1],
                "email": row[2],
                "hashed_password": row[3],
                "role": row[4],
                "is_active": bool(row[5])
            }
        return None


# Global database instance
db = Database()
