import yfinance as yf
import pandas as pd
import sqlite3

pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)
pd.set_option("display.width", None)


companies = ["AAPL", "TSLA", "NVDA"]
all_data=[]
for company in companies:
    stock=yf.Ticker(company)
    company_history=stock.history(period="5d")
    company_history["Company"]=company
    company_history["pct_change"] = company_history["Close"].pct_change() * 100
    all_data.append(company_history)

all_data_df=pd.concat(all_data)
conn=sqlite3.connect("finance_data.db")

# yfinance returns the Date as an index column , hence we want index=True in order to include the Date column.
all_data_df.to_sql("stock_history", conn, if_exists="replace", index=True)

print(all_data_df)
conn.close()
print("Finished Succesfully")