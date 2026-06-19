# Finance Intelligence Agent

An AI agent that combines market data and news sentiment to produce investment summaries. The system pulls recent stock data and related news headlines, classifies sentiment with a financial-domain language model, and synthesizes the results into a written summary using Claude via a LangChain ReAct agent. Everything is exposed through a FastAPI backend.

> **Disclaimer:** This project is built for personal learning and software engineering practice. It is not a financial product, does not provide investment advice, and is not intended for commercial use. All data sources are accessed through their publicly available developer interfaces in accordance with their terms. The summaries produced by the AI agent are illustrative outputs of a software pipeline and must not be used as the basis for any real investment decision.

## What it does

The system works in two stages. First, an ingestion pipeline pulls recent stock data for a set of tickers, fetches related news headlines, and runs each headline through FinBERT to classify it as positive, neutral, or negative. All of this lands in a local SQLite database. Second, a FastAPI server exposes three read endpoints over that data, plus an `/analyze/{ticker}` endpoint that hands the question to a Claude-powered agent. The agent has two tools — one for stock data, one for sentiment — and decides which to call to produce its summary.

## Tech stack

**Backend:** Python 3.13, FastAPI, uvicorn
**AI agent:** Anthropic Claude API (`claude-sonnet-4-6`), LangChain (ReAct pattern)
**Machine learning:** FinBERT (`ProsusAI/finbert`) via Hugging Face Transformers, PyTorch
**Data sources:** `yfinance` for market data, NewsAPI for news headlines
**Storage:** SQLite, with pandas for ingestion
**Config:** python-dotenv for environment variables
**Container:** Docker
**Development tooling:** Cursor IDE, Git, GitHub

## Prerequisites

- Python 3.13 or later
- An Anthropic API key — get one from [console.anthropic.com](https://console.anthropic.com)
- A NewsAPI key — sign up at [newsapi.org](https://newsapi.org)
- Docker (only if you want to run the backend as a container)

## Setup

Clone the repo and enter the project directory:

```bash
git clone <your-repo-url>
cd finance-intelligence-agent
```

A virtual environment is recommended so this project's dependencies don't mix with your system Python or other projects:

```bash
python3 -m venv venv
source venv/bin/activate    # macOS/Linux
# venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

## Configure your API keys

Copy the example env file and fill in your keys:

```bash
cp .env.example .env
```

Open `.env`:

```
ANTHROPIC_API_KEY=your_anthropic_key_here
NEWS_API_KEY=your_newsapi_key_here
ANTHROPIC_MODEL=claude-sonnet-4-6
```

`.env` is in `.gitignore` — never commit it. The `ANTHROPIC_MODEL` is pinned so you can change models without touching code; if Anthropic deprecates the current default, change this line.

## Populate the database

The backend reads from a local SQLite file called `finance_data.db`. This file is in `.gitignore`, so it doesn't ship with the repo — on a fresh clone it doesn't exist yet. The populate step creates it and fills it with the stock data, news headlines, and sentiment scores the backend needs:

```bash
python populate.py
```

This runs the three ingestion scripts in order — `fetch_stocks.py`, `fetch_news.py`, and `sentiment.py` — stopping immediately if any of them fail. The whole run takes about a minute. Re-run whenever you want fresh data.

If you skip populate, the backend still starts, but:

- /stocks and /sentiment return 500 if the DB tables don't exist
- If tables exist but are empty, those endpoints return 200 with []
- /analyze may return 500 (missing tables) or a "no data" summary (empty tables)

Run `python populate.py` before serving data.

## Run the backend (local)

With your virtual environment active and the database populated:

```bash
uvicorn backend_main:app --reload
```

The server runs at `http://localhost:8000`. The `--reload` flag tells uvicorn to restart automatically when you change code — useful in development, remove it for anything more permanent.

## Run the backend (Docker)

Build the image once:

```bash
docker build -t finance-agent .
```

The first build takes 5–15 minutes. Most of that time is downloading the FinBERT model — the Dockerfile bakes it into the image so the container starts instantly without a runtime download. Subsequent builds are fast thanks to layer caching.

Run the container, mounting your populated `finance_data.db` so the container can read it:

```bash
docker run -p 8000:8000 \
  --env-file .env \
  -v "$(pwd)/finance_data.db:/app/finance_data.db" \
  finance-agent
```

The `--env-file` flag injects your API keys at runtime — the `.env` file stays on your host and is never copied into the image. The volume mount shares the SQLite database file between host and container.

When the container starts you'll see uvicorn announce `http://0.0.0.0:8000` in the logs — that's the container's internal binding. From your machine, reach it as `http://localhost:8000`.

### Docker Desktop on macOS — volume mount permissions

Docker Desktop only mounts host paths from a sharing whitelist. `/Users/` is on it by default, but other locations (like `/Applications/`) aren't. If you get a `Mounts denied` error, add your project's parent directory under **Docker Desktop → Settings → Resources → File Sharing**, then Apply & Restart.

## Testing the endpoints

Once the server is running, you can hit each endpoint. The easiest way is the interactive Swagger UI at `http://localhost:8000/docs` — it lets you try every endpoint from the browser with no curl needed.

If you prefer the command line, here's each endpoint with what to expect:

**Health check** — confirms the server is up:

```bash
curl http://localhost:8000/
```

Expected: a JSON message saying the backend is alive.

**Stock data for a ticker:**

```bash
curl http://localhost:8000/stocks/AAPL
```

Expected: a JSON array of recent stock records (date, close price, percentage change, volume) for AAPL. Try `TSLA` or `NVDA` to see the other tickers. Any other ticker will return a 404 because the ingestion pipeline doesn't fetch it by default.

**Sentiment data for a ticker:**

```bash
curl http://localhost:8000/sentiment/AAPL
```

Expected: a JSON array of news headlines with their FinBERT sentiment label and confidence score.

**AI-generated investment summary:**

```bash
curl http://localhost:8000/analyze/AAPL
```

Expected: a JSON response containing a `summary` field with markdown text. In the terminal it appears as raw text with `\n` escape characters — it's intended to be rendered by a frontend that supports markdown. The endpoint runs the LangChain agent, which makes several Claude calls and uses the internal tools, so it takes 10 to 30 seconds. First call is on the longer end of that range.

If any endpoint returns a 500 error or an empty result, the database is likely missing or empty — run `python populate.py` first.

Note: the agent output is a software-generated narrative, not financial
guidance. See the disclaimer at the top of this README.

## About the external services

A few practical things to know about the rate limits and quirks of the services this project depends on:

**NewsAPI (free Developer plan)** allows about 100 requests per day, with a 24-hour delay on article freshness. NewsAPI's free Developer plan is licensed for development and testing only — the plan terms prohibit using it in production or in any commercial context. The ingestion pipeline issues one request per ticker per run, so populating data for three tickers costs three requests. That's well within the daily quota even if you re-populate many times.

**yfinance** is an open-source Python library widely used for accessing Yahoo Finance data for personal and educational projects. It's not part of an officially supported Yahoo API, so the right etiquette is moderate, non-aggressive usage. For this project's footprint — a handful of tickers, populated manually — you shouldn't see issues. If you scale the ticker list significantly, add delays between requests and consider caching.

**FinBERT** runs locally — it's a Hugging Face model loaded via Transformers, not a hosted API. Local inference has no rate limits; it's CPU/GPU work on your machine. The model download from the Hugging Face Hub is rate-limited, with stricter quotas for anonymous users, but you only download it once: the first run of `sentiment.py` caches it to `~/.cache/huggingface/` (about 440 MB). Inside the Docker image, the model is pre-downloaded at build time so the container never hits the Hub at runtime.

**Anthropic Claude** is the only paid call in this project. The `/analyze` endpoint typically makes 3–5 Claude calls per request (one per agent step). Sonnet 4.6 is priced at roughly $3 per million input tokens and $15 per million output tokens, so a single `/analyze` call costs a fraction of a cent. If you wire this up to a UI that fires requests automatically, keep an eye on your usage.

## Design notes

A few decisions worth flagging if you're reviewing the code:

**Two-phase setup over auto-populate.** The ingestion pipeline and the API are deliberately separate. I considered having the container fetch data on startup, but that means every restart re-fetches and burns rate-limit quota even when the data hasn't changed. Real production data systems keep ingestion and serving as separate jobs for the same reason.

**FinBERT baked into the Docker image.** Downloading the model at container start would make every fresh run wait for downloads and require working internet. Baking it in costs about 440 MB of image size in exchange for instant, internet-independent startup. For a project where the model is fixed and known, this is the right trade.

**SQLite over Postgres.** SQLite is the right call for a single-user setup like this — no server to manage, no authentication, no operational overhead. The cost is concurrency: SQLite serializes writes, so this design wouldn't scale to multiple users hitting the populate scripts simultaneously. Switching to Postgres later would mainly mean changing how the connection is created. The pandas calls that read and write to the database don't need to change.

**LangChain ReAct agent.** LangChain handles the prompt construction, output parsing, and tool dispatch loop. Writing this from scratch is around 60 lines of glue code with regex-based parsing, which is brittle. Using LangChain meant I could focus on defining the tools and writing the prompt rather than on the orchestration layer.

## Project structure

```
finance-intelligence-agent/
├── backend_main.py        # FastAPI app: routes and CORS
├── agents.py              # LangChain agent + tool definitions
├── fetch_stocks.py        # Stock data ingestion
├── fetch_news.py          # NewsAPI ingestion
├── sentiment.py           # FinBERT sentiment classification
├── populate.py            # Runs all three ingestion scripts in order
├── requirements.txt       # Python dependencies
├── Dockerfile             # Backend container build
├── .dockerignore          # Files excluded from the Docker image
├── .env.example           # Template for required env vars
└── README.md
```

## Known limitations

This project is intentionally scoped for local, single-user use. A few things to be aware of:

**The ticker list is hardcoded.** The ingestion pipeline currently fetches data for AAPL, TSLA, and NVDA only. Other tickers won't return data. Support for arbitrary tickers is planned for a future version.

**No tests.** A test suite is on the roadmap.

**SQL queries use string formatting.** The query construction in some endpoints uses f-strings rather than parameterized queries. For local use with controlled inputs this is fine; for any internet-exposed deployment it would need to be changed to parameterized queries to prevent SQL injection.

These are all on the roadmap.
