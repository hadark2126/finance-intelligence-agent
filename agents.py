import pandas as pd
import sqlite3
from dotenv import load_dotenv
import os

# The agent tools set up
from langchain_classic.tools import Tool

#libraries for creating the agent
from langchain_classic.agents import create_react_agent, AgentExecutor
from langchain_classic.prompts import PromptTemplate

#importing Claude as the LLM
from langchain_anthropic import ChatAnthropic

load_dotenv()
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
ANTHROPIC_API_KEY=os.getenv("ANTHROPIC_API_KEY")
llm = ChatAnthropic(model=ANTHROPIC_MODEL, api_key=ANTHROPIC_API_KEY)
# ANTHROPIC_API_KEY=os.getenv("ANTHROPIC_API_KEY")
# llm = ChatAnthropic(model="claude-sonnet-4-20250514", api_key=ANTHROPIC_API_KEY)

def stock_tool(company):
    # for not getting an error due to hidden "\n"
    company = str(company).strip().upper()
    conn=sqlite3.connect("finance_data.db")
    stock_history=pd.read_sql(f"SELECT * FROM stock_history WHERE Company = '{company}'",conn)
    if stock_history.empty:
        conn.close()
        return f"No stock rows in finance_data.db for {company}. Run fetch_stocks.py (or add that ticker) and retry."
    recent_change=stock_history.iloc[-1]["pct_change"]
    recent_closing_price=stock_history.iloc[-1]["Close"]
    company_val=stock_history.iloc[-1]["Volume"]
    first_close = stock_history.iloc[0]["Close"]
    last_close = stock_history.iloc[-1]["Close"]
    trend = "upward" if last_close > first_close else "downward"
    conn.close()
    return f"""
    Most recent closing price: {recent_closing_price}
    Most recent percentage difference: {recent_change}
    Company volume : {company_val}
    Trend : {trend}
    """

def sentiment_tool(company):
    company = str(company).strip().upper()
    # print(f"sentiment_tool called with: '{company}' type: {type(company)}")
    conn=sqlite3.connect("finance_data.db")
    news_history_df=pd.read_sql(f"SELECT * FROM news_history WHERE Company = '{company}'",conn)
    if news_history_df.empty:
        conn.close()
        return f"No news rows in finance_data.db for {company}. Run fetch_news.py (or add that ticker) and retry."
    average_score=news_history_df["sentiment_score"].mean()
    most_common_label=news_history_df["sentiment_label"].mode()[0]
    positive_count = len(news_history_df[news_history_df["sentiment_label"] == "positive"])
    negative_count = len(news_history_df[news_history_df["sentiment_label"] == "negative"])
    neutral_count = len(news_history_df[news_history_df["sentiment_label"] == "neutral"])
    conn.close()
    return f"""
    Average score :{average_score}
    Most common label : {most_common_label}
    Positive amount : {positive_count}
    Negative amount : {negative_count}
    Neutral amount : {neutral_count}
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
    )
]

prompt = PromptTemplate.from_template("""
You are a financial analysis assistant. Your job is to analyze stock data and news sentiment for companies and provide a clear investment summary.

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
""")

#creating the agent
agent= create_react_agent(llm,tools,prompt)
agent_executor= AgentExecutor(agent=agent,tools=tools,verbose=True)


if __name__=="__main__":
    #the execution of the agent
    result=agent_executor.invoke({"input":"Analyze AAPL stock and provide an investment summary"})
    print(result)
