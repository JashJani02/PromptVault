# Prompt Vault

A self-hostable, open-source Streamlit app to store and manage your AI conversations: prompts, responses, media URLs, links, and more: tagging, provider tracking, and an analytics dashboard.
 
> Built as a personal utility. No subscriptions, no vendor lock-in, your data stays yours.

## Features

- Username + password authentication (bcrypt-hashed)
- Flexible entry storage: prompt, response, image URL, video URL, chat link, artifact link (fill in any combination)
- Provider tracking: ChatGPT, Claude, Gemini, Qwen, DeepSeek, Grok, or any local/custom model
- Tags: comma-separated, auto-lowercased and deduplicated at write time
- Full-text search across topic, prompt, response, links, tags, and provider
- Edit entries inline with pre-filled forms
- Animated dashboard: entries by field, tag, provider, and activity over time
- SQLite database: zero config, self-contained, easy to back up

## Tech-Stack
<ol><li>Python</li><li>bcrypt</li><li>Sqlite</li><li>Pandas</li><li>Plotly</li></ol>

## Project Structure

```
PromptVault/
├── app.py              # Main entry point (router)
├── pages/
│   ├── login.py         # Login / signup page
│   ├── dashboard.py     # Stats & analysis
│   └── storage.py       # Add/view/manage items
├── db.py                # All database functions
├── data.sqlite          # SQLite database (created on first run)
├── requirements.txt
└── README.md
```

## Setup

1. Clone the repo:
   ```bash
   git clone https://github.com/JashJani02/PromptVault.git
   ```

2. Change directory:
   ```bash
   cd PromptVault
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the app:
   ```bash
   streamlit run app.py
   ```
5. Visit `http://localhost:8501`, sign up, and log in.


## Database Schema

```sql
users
├── id               INTEGER PRIMARY KEY
├── username         TEXT UNIQUE NOT NULL
├── password_hash    TEXT NOT NULL
└── created_at       TIMESTAMP
 
entries
├── id               INTEGER PRIMARY KEY
├── user_id          INTEGER FK → users.id
├── topic            TEXT              -- optional chat headline / title
├── prompt           TEXT              -- optional
├── response         TEXT              -- optional
├── image_url        TEXT              -- optional
├── video_url        TEXT              -- optional
├── chat_link        TEXT              -- optional
├── artifact_link    TEXT              -- optional
├── category         TEXT              -- comma-separated tags, stored lowercase
├── provider         TEXT              -- e.g. Claude, ChatGPT, local model name
└── created_at       TIMESTAMP
```

## API Reference (Internal Functions)

### `app.py`
 
| Responsibility | Description |
| :--- | :--- |
| Entry point | Initializes the DB, manages `st.session_state` (logged\_in, user\_id, username), and routes between login and authenticated pages using `st.navigation()`. |
| Page routing | Registers `login`, `dashboard`, and `storage` as `st.Page` objects with explicit `url_path` values. Logged-out users only see the login page. |
| Logout | Clears session state and reruns to return to the login page. |
 
---
 
### `db.py`
 
#### Core
 
| Function | Parameters | Returns | Description |
| :--- | :--- | :--- | :--- |
| `init_db()` | — | `None` | Creates tables if they don't exist. Runs column migrations automatically (safe to call on existing DBs). |
| `get_connection()` | — | `sqlite3.Connection` | Returns a DB connection with `row_factory` set for dict-like row access. |
| `normalize_tags(raw)` | `raw` (str) | `str \| None` | Strips, lowercases, and deduplicates a comma-separated tag string before storage. Returns `None` for blank input. |
 
#### Auth
 
| Function | Parameters | Returns | Description |
| :--- | :--- | :--- | :--- |
| `create_user(username, password)` | `username` (str), `password` (str) | `bool` | Hashes password with bcrypt and inserts a new user. Returns `False` if username is already taken. |
| `verify_user(username, password)` | `username` (str), `password` (str) | `int \| None` | Checks credentials. Returns `user_id` on success, `None` on failure. |
 
#### Entries
 
| Function | Parameters | Returns | Description |
| :--- | :--- | :--- | :--- |
| `add_entry(user_id, values, category, provider, topic)` | `user_id` (int), `values` (dict), `category` (str, opt), `provider` (str, opt), `topic` (str, opt) | `None` | Saves a new entry. `values` accepts any subset of: `prompt`, `response`, `image_url`, `video_url`, `chat_link`, `artifact_link`. Tags are normalized before storage. |
| `update_entry(entry_id, user_id, values, category, provider, topic)` | same shape as `add_entry` + `entry_id` (int) | `None` | Overwrites an existing entry's fields. Scoped to `user_id` for safety. |
| `get_entries(user_id)` | `user_id` (int) | `list[sqlite3.Row]` | Returns all entries for the user, newest first. |
| `delete_entry(entry_id, user_id)` | `entry_id` (int), `user_id` (int) | `None` | Deletes an entry scoped to the requesting user. |
 
#### Analytics
 
| Function | Parameters | Returns | Description |
| :--- | :--- | :--- | :--- |
| `get_stats(user_id)` | `user_id` (int) | `dict` | Returns `total`, `by_field`, `by_category` (individual tags split and counted), `by_provider`, `over_time`, `last_saved`, `top_provider`, `top_category`. |
 
---
 
### `pages/`
 
Each file exposes a single `render()` function called by `app.py` via `st.Page`. Pages share state through `st.session_state` and interact with the DB exclusively through `db.py`.
 
#### `login.py`
 
| Function | Description |
| :--- | :--- |
| `render()` | Renders Login and Sign Up tabs. On success, sets `logged_in`, `user_id`, and `username` in `st.session_state` and reruns to navigate to the dashboard. |
 
#### `dashboard.py`
 
| Function | Description |
| :--- | :--- |
| `render()` | Renders two rows of metric cards and four animated Plotly charts: entries by field (bar), by tag (donut), by provider (bar with count labels), and activity over time (line with area fill). All charts share an 800ms cubic-in-out entrance animation. |
 
#### `storage.py`
 
| Function | Description |
| :--- | :--- |
| `render()` | Renders the Add Entry form (provider selectbox outside the form for dynamic show/hide of the custom model field), a full-text search bar, and the entry list as collapsible expanders with inline edit and delete. |
| `_provider_inputs(prefix, entry)` | Renders the provider selectbox and optional custom model name field outside any `st.form` so they react to selection changes immediately. |
| `_resolve_provider(prefix)` | Reads the provider choice and custom text from `st.session_state` at submit time and returns the resolved provider string. |
| `_entry_title(entry)` | Returns the expander title: the entry's topic if set, otherwise a 60-char snippet of the first filled field. |
| `_is_loadable_image(url)` | Sends a HEAD request to validate an image URL before rendering. Returns `False` for broken or unreachable URLs, causing the display to fall back to a plain link. Cached for 5 minutes via `st.cache_data`. |
 
---
 
## Notes
 
- Passwords are hashed with `bcrypt`: plaintext is never stored.
- All DB writes are scoped by `user_id`: users can only read/write their own entries.
- Tags are normalized at write time via `normalize_tags()` : `"Coding, CODING, python"` stores as `"coding,python"`.
- Image URLs are validated with a HEAD request before rendering: broken URLs fall back to a plain link with no placeholder shown.
- Provider custom name field only appears when `Other` or `Local / Self-hosted` is selected.
 
