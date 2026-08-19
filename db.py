import sqlite3
import bcrypt
from datetime import datetime

DB_PATH = "data.sqlite"

# Each entry can hold any combination of these fields. All are optional;
# a user might fill in just a Prompt, or a Prompt + Response + Chat Link
# together in a single entry, etc.
FIELDS = [
    ("prompt", "Prompt"),
    ("response", "Response"),
    ("image_url", "Image URL"),
    ("video_url", "Video URL"),
    ("chat_link", "Chat Link"),
    ("artifact_link", "Artifact Link"),
]
FIELD_KEYS = [key for key, _ in FIELDS]

PROVIDERS = [
    "ChatGPT",
    "Claude",
    "Gemini",
    "Qwen",
    "DeepSeek",
    "Grok",
    "Local / Self-hosted",
    "Other",
]


def normalize_tags(raw):
    """Lowercases, strips whitespace, deduplicates, and returns a
    comma-separated string ready to store in the category column.
    e.g. "  Coding, python,CODING " → "coding,python"
    Returns None if nothing meaningful was provided."""
    if not raw:
        return None
    tags = [t.strip().lower() for t in raw.split(",") if t.strip()]
    # Deduplicate while preserving order
    seen = set()
    unique = [t for t in tags if not (t in seen or seen.add(t))]
    return ",".join(unique) if unique else None


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            topic TEXT,
            prompt TEXT,
            response TEXT,
            image_url TEXT,
            video_url TEXT,
            chat_link TEXT,
            artifact_link TEXT,
            category TEXT,
            provider TEXT,
            created_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Migration safety net: if entries already existed from before a field
    # was added, add the missing column instead of failing.
    cursor.execute("PRAGMA table_info(entries)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    if "provider" not in existing_columns:
        cursor.execute("ALTER TABLE entries ADD COLUMN provider TEXT")
    if "topic" not in existing_columns:
        cursor.execute("ALTER TABLE entries ADD COLUMN topic TEXT")

    conn.commit()
    conn.close()


# ---------- Auth ----------

def create_user(username, password):
    """Returns True on success, False if username already exists."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        cursor.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (username, password_hash, datetime.now())
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def verify_user(username, password):
    """Returns user_id if credentials are valid, else None."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    if bcrypt.checkpw(password.encode(), row["password_hash"].encode()):
        return row["id"]
    return None


# ---------- Entries ----------

def add_entry(user_id, values, category=None, provider=None, topic=None):
    """
    values: dict with any subset of FIELD_KEYS, e.g.
            {"prompt": "...", "response": "...", "chat_link": "..."}
    Fields not provided (or left blank) are stored as NULL.
    provider: which AI produced this (e.g. "Claude", "ChatGPT"), optional.
    topic: short user-given headline for the entry, optional.
    """
    conn = get_connection()
    cursor = conn.cursor()

    row = {key: (values.get(key) or None) for key in FIELD_KEYS}

    cursor.execute(
        f"""INSERT INTO entries
            (user_id, topic, {', '.join(FIELD_KEYS)}, category, provider, created_at)
            VALUES (?, ?, {', '.join(['?'] * len(FIELD_KEYS))}, ?, ?, ?)""",
        (user_id, topic or None, *[row[key] for key in FIELD_KEYS], normalize_tags(category), provider or None, datetime.now())
    )
    conn.commit()
    conn.close()


def get_entries(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM entries WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    )
    entries = cursor.fetchall()
    conn.close()
    return entries


def update_entry(entry_id, user_id, values, category=None, provider=None, topic=None):
    """Overwrites an existing entry's fields. Same shape as add_entry."""
    conn = get_connection()
    cursor = conn.cursor()

    row = {key: (values.get(key) or None) for key in FIELD_KEYS}
    set_clause = ", ".join(f"{key} = ?" for key in FIELD_KEYS)

    cursor.execute(
        f"""UPDATE entries SET topic = ?, {set_clause}, category = ?, provider = ?
            WHERE id = ? AND user_id = ?""",
        (topic or None, *[row[key] for key in FIELD_KEYS], normalize_tags(category), provider or None, entry_id, user_id)
    )
    conn.commit()
    conn.close()


def delete_entry(entry_id, user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM entries WHERE id = ? AND user_id = ?", (entry_id, user_id))
    conn.commit()
    conn.close()


def get_stats(user_id):
    """Returns dict with total count, counts per field (how many entries
    have that field filled in), counts by category, and entries over time."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM entries WHERE user_id = ?", (user_id,))
    total = cursor.fetchone()["total"]

    by_field = []
    for key, label in FIELDS:
        cursor.execute(
            f"SELECT COUNT(*) as count FROM entries WHERE user_id = ? AND {key} IS NOT NULL AND {key} != ''",
            (user_id,)
        )
        count = cursor.fetchone()["count"]
        if count > 0:
            by_field.append({"field": label, "count": count})

    # Tags are stored comma-separated ("coding,python,refactor").
    # Pull all non-null category strings and split them into individual
    # tags before counting, so each tag is counted independently.
    cursor.execute(
        """SELECT category FROM entries
           WHERE user_id = ? AND category IS NOT NULL AND category != ''""",
        (user_id,)
    )
    tag_counts = {}
    for row in cursor.fetchall():
        for tag in row["category"].split(","):
            tag = tag.strip()
            if tag:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
    by_category = [{"category": tag, "count": count} for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1])]

    cursor.execute(
        """SELECT provider, COUNT(*) as count FROM entries
           WHERE user_id = ? AND provider IS NOT NULL AND provider != ''
           GROUP BY provider""",
        (user_id,)
    )
    by_provider = cursor.fetchall()

    cursor.execute(
        """SELECT DATE(created_at) as day, COUNT(*) as count FROM entries
           WHERE user_id = ? GROUP BY DATE(created_at) ORDER BY day""",
        (user_id,)
    )
    over_time = cursor.fetchall()

    cursor.execute(
        "SELECT created_at FROM entries WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
        (user_id,)
    )
    last_row = cursor.fetchone()
    last_saved = last_row["created_at"] if last_row else None

    top_provider = max(by_provider, key=lambda r: r["count"])["provider"] if by_provider else None
    top_category = max(by_category, key=lambda r: r["count"])["category"] if by_category else None

    conn.close()
    return {
        "total": total,
        "by_field": by_field,
        "by_category": by_category,
        "by_provider": by_provider,
        "over_time": over_time,
        "last_saved": last_saved,
        "top_provider": top_provider,
        "top_category": top_category,
    }