import os

# Set dummy credentials before any project module is imported, since
# agents.py builds its ChatAnthropic client at import time and would
# otherwise fail without a real ANTHROPIC_API_KEY.
os.environ.setdefault("ANTHROPIC_API_KEY", "dummy-test-key")
os.environ.setdefault("NEWS_API_KEY", "dummy-test-key")

import sqlite3

import pytest


@pytest.fixture
def fake_db(tmp_path, monkeypatch):
    """Create a throwaway finance_data.db with the schema the app expects.

    Runs from a temp directory so the app's hardcoded relative path
    ("finance_data.db") resolves here instead of touching the real db.
    """
    monkeypatch.chdir(tmp_path)

    conn = sqlite3.connect("finance_data.db")
    conn.execute(
        'CREATE TABLE stock_history ('
        '"Date" TIMESTAMP, '
        "Open REAL, "
        "High REAL, "
        "Low REAL, "
        "Close REAL, "
        "Volume INTEGER, "
        "Dividends REAL, "
        '"Stock Splits" REAL, '
        "Company TEXT, "
        "pct_change REAL"
        ")"
    )
    conn.execute(
        "INSERT INTO stock_history VALUES "
        "('2024-01-01', 149.0, 151.0, 148.0, 150.0, 1000, 0.0, 0.0, 'AAPL', 0.0),"
        "('2024-01-02', 150.0, 154.0, 149.5, 153.0, 1200, 0.0, 0.0, 'AAPL', 2.0)"
    )
    conn.execute(
        "CREATE TABLE news_history ("
        "source TEXT, "
        "author TEXT, "
        "title TEXT, "
        "description TEXT, "
        "url TEXT, "
        "urlToImage TEXT, "
        "publishedAt TEXT, "
        "content TEXT, "
        "Company TEXT, "
        "sentiment_label TEXT, "
        "sentiment_score REAL"
        ")"
    )
    conn.execute(
        "INSERT INTO news_history VALUES ("
        "'Reuters', "
        "'Jane Doe', "
        "'Apple hits record revenue', "
        "'Apple reported strong quarterly results.', "
        "'https://example.com/apple-revenue', "
        "'https://example.com/apple.jpg', "
        "'2024-01-01', "
        "'Full article content about Apple revenue.', "
        "'AAPL', "
        "'positive', "
        "0.91"
        ")"
    )
    conn.commit()
    conn.close()

    yield "finance_data.db"
