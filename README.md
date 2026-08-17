# Prompt Vault

A Streamlit app to store and manage prompts, responses, media URLs, and links — with username/password login and a stats dashboard.

## Features

- 🔐 Username + password authentication (bcrypt-hashed)
- 📝 Store prompts, responses, image/video URLs, chat links, and artifact links
- 🏷️ Optional categorization, and linking responses to prompts
- 📊 Dashboard with charts (by type, by category, over time)
- 💾 Persistent SQLite database

## Project Structure

```
project/
├── app.py              # Main entry point (router)
├── pages/
│   ├── login.py         # Login / signup page
│   ├── dashboard.py     # Stats & analysis
│   └── storage.py       # Add/view/manage items
├── db.py                # All database functions
├── data.sqlite              # SQLite database (created on first run)
├── requirements.txt
└── README.md
```

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the app:
   ```bash
   streamlit run app.py
   ```
3. Visit `http://localhost:8501`, sign up, and log in.


## Database Schema

```sql
users
├── id (INTEGER PRIMARY KEY)
├── username (TEXT UNIQUE)
├── password_hash (TEXT)
└── created_at (TIMESTAMP)

entries
├── id (INTEGER PRIMARY KEY)
├── user_id (INTEGER FK -> users.id)
├── prompt (TEXT)
├── response (TEXT)
├── image_url (TEXT)
├── video_url (TEXT)
├── chat_link (TEXT)
├── artifact_link (TEXT)
├── category (TEXT)
├── provider (TEXT)
└── created_at (TIMESTAMP)
```

## API Reference (Internal Functions)

The application uses an internal data-access layer (`db.py`) to interact with the SQLite database. Below is the reference for the core functions used across the app.

### Data Layer (`db.py`)

| Function | Parameters | Returns | Description |
| :--- | :--- | :--- | :--- |
| `init_db()` | *None* | `None` | Creates the `users` and `entries` tables if they don't exist and runs necessary schema migrations (e.g., adding the `provider` column). |
| `get_connection()` | *None* | `sqlite3.Connection` | Returns a new connection to the SQLite database with the row factory enabled for dict-like access. |
| `create_user(username, password)` | `username` (str), `password` (str) | `bool` | Hashes the password using `bcrypt` and creates a new user. Returns `True` on success, `False` if the username is already taken. |
| `verify_user(username, password)` | `username` (str), `password` (str) | `int` or `None` | Validates credentials against the database. Returns the user's `id` if valid, or `None` if invalid. |
| `add_entry(user_id, values, category, provider)` | `user_id` (int), `values` (dict), `category` (str, optional), `provider` (str, optional) | `None` | Saves a new entry. The `values` dict accepts keys: `prompt`, `response`, `image_url`, `video_url`, `chat_link`, `artifact_link`. |
| `get_entries(user_id)` | `user_id` (int) | `list[sqlite3.Row]` | Retrieves all entries for the specified user, ordered by creation date (newest first). |
| `delete_entry(entry_id, user_id)` | `entry_id` (int), `user_id` (int) | `None` | Deletes a specific entry, ensuring it belongs to the requesting user (scoped security). |
| `get_stats(user_id)` | `user_id` (int) | `dict` | Gathers dashboard metrics: `total` entries, counts `by_field`, `by_category`, `by_provider`, and daily activity `over_time`. |

### UI Modules (`pages/`)

| Module | Function | Description |
| :--- | :--- | :--- |
| `login` | `render()` | Handles the Login and Sign Up tabs, authenticating users and updating `st.session_state`. |
| `dashboard` | `render()` | Generates Plotly charts (Bar, Pie, Line) dynamically using stats fetched from `get_stats()`. |
| `storage` | `render()` | Provides the UI forms to add new entries and lists existing entries with delete capabilities. |

## Notes

- Passwords are hashed with `bcrypt` before storage — plaintext passwords are never saved.
- Each user only sees their own items (scoped by `user_id`).
- The dashboard uses Plotly for bar, pie, and line charts.
