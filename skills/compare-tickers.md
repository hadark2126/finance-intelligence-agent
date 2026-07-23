# Compare Tickers Skill

## When to use

Use this when the user asks to compare two companies, tickers, or stocks
(e.g. "compare AAPL and TSLA", "AAPL vs NVDA").

## Which tool

Use the CompareTickers tool.

## How to call it

Action: CompareTickers
Action Input: TICKER_A,TICKER_B

Examples:

- AAPL,TSLA
- NVDA,AAPL

Rules:

- Exactly two tickers
- Separated by a comma
- No extra words in the Action Input

## What the tool returns

A side-by-side summary of stock data and news sentiment for both tickers,
based on finance_data.db.

## What to do after

Read the Observation, then give a Final Answer that compares both companies
clearly (trend, recent change, sentiment). Do not invent numbers that were
not in the Observation.

## What not to do

- Do not call StockData and SentimentData four times instead of CompareTickers
  when the question is a comparison of exactly two tickers
- Do not pass only one ticker
- Do not pass three or more tickers
