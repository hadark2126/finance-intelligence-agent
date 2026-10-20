import pandas as pd
import sqlite3
from dotenv import load_dotenv
import os
import smtplib
from email.message import EmailMessage

# The agent tools set up
from langchain_classic.tools import Tool

#libraries for creating the agent
from langchain_classic.agents import create_react_agent, AgentExecutor
from langchain_classic.prompts import PromptTemplate

#importing Claude as the LLM
from langchain_anthropic import ChatAnthropic

#for the use of the skills
from pathlib import Path

#for the email sending
SEND_MAIL = True

load_dotenv()
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
ANTHROPIC_API_KEY=os.getenv("ANTHROPIC_API_KEY")
llm = ChatAnthropic(model=ANTHROPIC_MODEL, api_key=ANTHROPIC_API_KEY)

def stock_tool(company):
    # for not getting an error due to hidden "\n"
    company = str(company).strip().upper()
    conn=sqlite3.connect("finance_data.db")
    table_ok = pd.read_sql(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='stock_history'",
        conn,
    )
    if table_ok.empty:
        conn.close()
        return f"No stock rows in finance_data.db for {company}. Run fetch_stocks.py (or add that ticker) and retry."
    stock_history=pd.read_sql("SELECT * FROM stock_history WHERE Company = ?", conn, params=(company,))
    if stock_history.empty:
        conn.close()
        return f"No stock rows in finance_data.db for {company}. Run fetch_stocks.py (or add that ticker) and retry."
    recent_change=stock_history.iloc[-1]["pct_change"]
    recent_closing_price=stock_history.iloc[-1]["Close"]
    company_val=stock_history.iloc[-1]["Volume"]
    first_close = stock_history.iloc[0]["Close"]
    last_close = stock_history.iloc[-1]["Close"]
    trend = "upward" if last_close > first_close else "downward"
    days_count = len(stock_history)
    average_close = stock_history["Close"].mean()
    conn.close()
    return f"""
    Most recent closing price: {recent_closing_price}
    Most recent percentage difference: {recent_change}
    Company volume : {company_val}
    Trend : {trend}
    Average closing price over {days_count} days: {average_close}
    """

def sentiment_tool(company):
    company = str(company).strip().upper()
    # print(f"sentiment_tool called with: '{company}' type: {type(company)}")
    conn=sqlite3.connect("finance_data.db")
    table_ok = pd.read_sql(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='news_history'",
        conn,
    )
    if table_ok.empty:
        conn.close()
        return f"No news rows in finance_data.db for {company}. Run fetch_news.py (or add that ticker) and retry."
    news_history_df=pd.read_sql("SELECT * FROM news_history WHERE Company = ?", conn, params=(company,))
    if news_history_df.empty:
        conn.close()
        return f"No news rows in finance_data.db for {company}. Run fetch_news.py (or add that ticker) and retry."
    labels_dict={"positive":0,"negative":0,"neutral":0}
    aggregated_scores={"positive":0.0,"negative":0.0,"neutral":0.0}
    for i in range(len(news_history_df)):
        label = news_history_df["sentiment_label"].iloc[i]
        score = news_history_df["sentiment_score"].iloc[i]
        labels_dict[label] += 1
        aggregated_scores[label] += score
    avg_positive = aggregated_scores["positive"] / labels_dict["positive"] if labels_dict["positive"] else 0.0
    avg_negative = aggregated_scores["negative"] / labels_dict["negative"] if labels_dict["negative"] else 0.0
    avg_neutral = aggregated_scores["neutral"] / labels_dict["neutral"] if labels_dict["neutral"] else 0.0
    conn.close()
    return f"""
    Average positive score :{avg_positive}
    Average negative score :{avg_negative}
    Average neutral score :{avg_neutral}
    Positive amount : {labels_dict["positive"]}
    Negative amount : {labels_dict["negative"]}
    Neutral amount : {labels_dict["neutral"]}
    """

def compare_tickers_tool(tickers):
    """Compare stock + sentiment data for exactly two tickers.

    Input should be two tickers separated by a comma, e.g. 'AAPL,TSLA'.
    """
    text = str(tickers).strip().upper().replace(" ", "")
    parts = [p for p in text.split(",") if p]
    if len(parts) != 2:
        return (
            "The input does not include two tickers. "
            "Provide exactly two tickers separated by a comma, e.g. AAPL,TSLA."
        )

    ticker_a, ticker_b = parts
    stock_a = stock_tool(ticker_a)
    stock_b = stock_tool(ticker_b)
    sentiment_a = sentiment_tool(ticker_a)
    sentiment_b = sentiment_tool(ticker_b)

    return f"""
Comparison: {ticker_a} vs {ticker_b}

{ticker_a} — stock:
{stock_a}
{ticker_a} — sentiment:
{sentiment_a}

{ticker_b} — stock:
{stock_b}
{ticker_b} — sentiment:
{sentiment_b}
"""

tools = [
    Tool(
        name="StockData",
        description="Use this to get the latest stock price and percentage change for a company. Input should be a ticker symbol like AAPL, TSLA, or NVDA.",
        func=stock_tool
    ),
    Tool(
        name="SentimentData",
        description="Use this to get the average sentiment score and most common sentiment label from news headlines for a company. Input should be a ticker symbol like AAPL, TSLA, or NVDA.",
        func=sentiment_tool
    ),
    Tool(
        name="CompareTickers",
        description=(
            "Use this to compare two companies side by side using stock data "
            "(including average closing price) and news sentiment "
            "(overall and per-label averages). Input must be exactly two ticker "
            "symbols separated by a comma, e.g. AAPL,TSLA."
        ),
        func=compare_tickers_tool
    )
]
SKILLS_DIR = Path(__file__).resolve().parent / "skills"
compare_tickers_skill = (SKILLS_DIR / "compare-tickers.md").read_text(encoding="utf-8")

prompt = PromptTemplate.from_template(
    """
You are a financial analysis assistant. Your job is to analyze stock data and news sentiment for companies and provide a clear investment summary.

"""
    + compare_tickers_skill
    + """

You have access to the following tools:
{tools}

Use the following format:
Question: the input question you must answer
Thought: think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (repeat Thought/Action/Action Input/Observation as needed)
Thought: I now know the final answer
Final Answer: your investment summary

Question: {input}
{agent_scratchpad}
"""
)

#creating the agent
agent= create_react_agent(llm,tools,prompt)
agent_executor= AgentExecutor(agent=agent,tools=tools,verbose=True)


def send_email(subject, body):
    host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_APP_PASSWORD")
    recipient = os.getenv("EMAIL_TO", user)

    if not (user and password and recipient):
        print("Skipping email: EMAIL_USER, EMAIL_APP_PASSWORD, or EMAIL_TO not set.")
        return

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = user
    message["To"] = recipient
    message.set_content(body)

    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(user, password)
        server.send_message(message)
    print(f"Email sent to {recipient}: {subject}")


if __name__=="__main__":

    result=agent_executor.invoke({"input":"Analyze AAPL stock and provide an investment summary"})
    print(result.get("output", result))
    if SEND_MAIL:
        send_email("Investment analysis", str(result.get("output", result)))

    # # Comparison prompt
    # comparison = agent_executor.invoke(
    #     {"input": "Compare AAPL and NVDA and provide an investment summary"}
    # )
    # print(comparison.get("output", comparison))
    # if SEND_MAIL:
    #     send_email("AAPL vs NVDA comparison", str(comparison.get("output", comparison)))