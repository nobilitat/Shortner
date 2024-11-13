CREATE TABLE IF NOT EXISTS Url (
    id TEXT PRIMARY KEY,
    full_url TEXT NOT NULL,
    short_url TEXT,
    create_date TEXT
)