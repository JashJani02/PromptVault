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
├── id
├── username (unique)
├── password_hash
└── created_at

storage_items
├── id
├── user_id (FK -> users.id)
├── item_type   -- Prompt, Response, Image URL, Video URL, Chat Link, Artifact Link
├── content     -- text or URL
├── category    -- optional, user-defined
├── related_prompt_id  -- optional, links a Response to a Prompt
└── created_at
```

## Notes

- Passwords are hashed with `bcrypt` before storage — plaintext passwords are never saved.
- Each user only sees their own items (scoped by `user_id`).
- The dashboard uses Plotly for bar, pie, and line charts.