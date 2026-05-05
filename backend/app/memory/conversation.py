"""Conversation memory management — persistent conversation history with summarization.

AI Technique: Memory / Conversation Management
- Stores conversation history per user per session
- Summarizes old messages when context exceeds a threshold
- Enables the system to recall prior interactions
"""

import json
import logging
from datetime import datetime, timezone

from app.services.llm import get_llm_service

logger = logging.getLogger(__name__)

MAX_HISTORY_MESSAGES = 20
SUMMARIZE_AFTER = 10

SUMMARIZATION_PROMPT = """You are a conversation summarizer. Given a series of past user-assistant messages,
produce a concise summary (2-3 sentences) capturing the key topics discussed and any important decisions made.
Respond with ONLY valid JSON: {"summary": "your summary text here"}"""


class ConversationMemory:
    """Manages per-user conversation history with summarization."""

    def __init__(self, db):
        self.db = db
        self._ensure_table()

    def _ensure_table(self):
        self.db.conn.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS conversation_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                summary TEXT NOT NULL,
                message_count INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """)
        self.db.conn.commit()

    def add_message(self, user_id: int, role: str, content: str):
        """Add a message to the conversation history."""
        self.db.conn.execute(
            "INSERT INTO conversations (user_id, role, content) VALUES (?, ?, ?)",
            (user_id, role, content),
        )
        self.db.conn.commit()

        # Check if summarization is needed
        count = self._message_count(user_id)
        if count > MAX_HISTORY_MESSAGES:
            self._summarize_and_prune(user_id)

    def get_context(self, user_id: int) -> dict:
        """Get conversation context: summary + recent messages."""
        summary = self._get_summary(user_id)
        recent = self._get_recent_messages(user_id, limit=SUMMARIZE_AFTER)

        return {
            "summary": summary,
            "recent_messages": recent,
            "total_messages": self._message_count(user_id),
        }

    def get_history(self, user_id: int, limit: int = 50) -> list[dict]:
        """Get raw conversation history for display."""
        rows = self.db.conn.execute(
            "SELECT role, content, created_at FROM conversations WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return [{"role": r["role"], "content": r["content"], "created_at": r["created_at"]} for r in reversed(rows)]

    def _message_count(self, user_id: int) -> int:
        row = self.db.conn.execute(
            "SELECT COUNT(*) as cnt FROM conversations WHERE user_id = ?", (user_id,)
        ).fetchone()
        return row["cnt"] if row else 0

    def _get_recent_messages(self, user_id: int, limit: int = 10) -> list[dict]:
        rows = self.db.conn.execute(
            "SELECT role, content FROM conversations WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]

    def _get_summary(self, user_id: int) -> str | None:
        row = self.db.conn.execute(
            "SELECT summary FROM conversation_summaries WHERE user_id = ?", (user_id,)
        ).fetchone()
        return row["summary"] if row else None

    def _summarize_and_prune(self, user_id: int):
        """Summarize older messages and prune them from the table."""
        # Get older messages (all except the most recent SUMMARIZE_AFTER)
        all_messages = self.db.conn.execute(
            "SELECT id, role, content FROM conversations WHERE user_id = ? ORDER BY created_at ASC",
            (user_id,),
        ).fetchall()

        if len(all_messages) <= SUMMARIZE_AFTER:
            return

        to_summarize = all_messages[:-SUMMARIZE_AFTER]
        to_keep_ids = [m["id"] for m in all_messages[-SUMMARIZE_AFTER:]]

        # Build text for summarization
        messages_text = "\n".join(
            f"{m['role']}: {m['content']}" for m in to_summarize
        )

        # Get existing summary
        existing_summary = self._get_summary(user_id) or ""

        # Summarize using LLM
        new_summary = self._run_summarization(existing_summary, messages_text)

        # Store summary
        self.db.conn.execute(
            """INSERT INTO conversation_summaries (user_id, summary, message_count, updated_at)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET
                   summary = excluded.summary,
                   message_count = excluded.message_count,
                   updated_at = excluded.updated_at""",
            (user_id, new_summary, len(all_messages), datetime.now(timezone.utc).isoformat()),
        )

        # Delete old messages
        ids_to_delete = [m["id"] for m in to_summarize]
        placeholders = ",".join("?" * len(ids_to_delete))
        self.db.conn.execute(
            f"DELETE FROM conversations WHERE id IN ({placeholders})", ids_to_delete
        )
        self.db.conn.commit()
        logger.info("Summarized %d messages for user %d", len(ids_to_delete), user_id)

    def _run_summarization(self, existing_summary: str, messages_text: str) -> str:
        """Use LLM to summarize conversation history."""
        try:
            llm = get_llm_service()
            prompt = f"Previous summary: {existing_summary}\n\nNew messages:\n{messages_text}"
            response = llm.complete(
                prompt=prompt,
                system_prompt=SUMMARIZATION_PROMPT,
                output_schema={"summary": "string"},
                max_tokens=256,
            )
            if response.parsed and "summary" in response.parsed:
                return response.parsed["summary"]
            return response.content[:500]
        except Exception as e:
            logger.warning("Summarization failed: %s, using fallback", e)
            # Fallback: just take the last 200 chars as summary
            return f"Previous context: {messages_text[-200:]}"


_memory: ConversationMemory | None = None


def get_conversation_memory(db) -> ConversationMemory:
    global _memory
    if _memory is None:
        _memory = ConversationMemory(db)
    return _memory
