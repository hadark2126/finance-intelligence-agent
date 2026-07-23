"""Unit tests for the pure lookup/formatting logic in agents.py.

These exercise stock_tool/sentiment_tool directly against a fixture
database, without going through the LLM or the HTTP layer.
"""

from agents import compare_tickers_tool, sentiment_tool, stock_tool


def test_stock_tool_no_data_for_unknown_company(fake_db):
    result = stock_tool("ZZZZ")
    assert "No stock rows" in result


def test_stock_tool_reports_trend_for_known_company(fake_db):
    result = stock_tool("AAPL")
    assert "upward" in result
    assert "153.0" in result


def test_sentiment_tool_no_data_for_unknown_company(fake_db):
    result = sentiment_tool("ZZZZ")
    assert "No news rows" in result


def test_sentiment_tool_reports_average_for_known_company(fake_db):
    result = sentiment_tool("AAPL")
    assert "positive" in result
    assert "Positive amount : 1" in result


def test_compare_tickers_rejects_input_without_two_tickers():
    result = compare_tickers_tool("AAPL")
    assert "does not include two tickers" in result


def test_compare_tickers_reports_missing_data(fake_db):
    result = compare_tickers_tool("AAPL,ZZZZ")
    assert "Comparison: AAPL vs ZZZZ" in result
    assert "No stock rows" in result or "No news rows" in result


def test_compare_tickers_side_by_side(fake_db):
    result = compare_tickers_tool("AAPL,TSLA")
    assert "Comparison: AAPL vs TSLA" in result
    assert "AAPL — stock:" in result
    assert "TSLA — stock:" in result
    assert "Trend" in result
