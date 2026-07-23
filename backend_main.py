
import pandas as pd
import sqlite3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from agents import agent_executor


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # trust requests from React
    allow_methods=["*"],                       # allow any HTTP method (GET, POST...)
    allow_headers=["*"],                       # allow any headers
)

@app.get("/")
def read_root():
    return {"message": "Hello! This is Hadar's Smart AI Finance Consultant backend — still under development."}

@app.get("/stocks/{company}")
def get_stock_data(company: str):
    conn = sqlite3.connect("finance_data.db")
    stock_history=pd.read_sql(f"SELECT Date, Close, pct_change, Volume, Company FROM stock_history WHERE Company = '{company}'",conn)
    # stock_history = stock_history.where(pd.notnull(stock_history), None)
    stock_history = stock_history.fillna(0)
    conn.close()
    return stock_history.to_dict(orient="records")


@app.get("/sentiment/{company}")
def get_sentiment_data(company: str):
    conn = sqlite3.connect("finance_data.db")
    sentiment_data=pd.read_sql(f"SELECT title, source, publishedAt, sentiment_label, sentiment_score, Company FROM news_history WHERE Company = '{company}'",conn)
    conn.close()
    return sentiment_data.to_dict(orient="records")


@app.get("/analyze/{company}")
def get_analysis(company: str):
    result=agent_executor.invoke({"input":f"Analyze {company} stock and provide an investment summary"})
    return {"summary":result["output"]}


@app.get("/compare")
def compare_companies(a: str, b: str):
    result=agent_executor.invoke({"input":f"Compare {a} and {b} and provide an investment summary"})
    return {"summary":result["output"]}