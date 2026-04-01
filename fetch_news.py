import pandas as pd
import sqlite3

# In order to use the .env file, we need to load the environment variables
from dotenv import load_dotenv
import os

import requests

load_dotenv()
NEWS_API_KEY=os.getenv("NEWS_API_KEY")


pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)
pd.set_option("display.width", None)


companies = ["AAPL", "TSLA", "NVDA"]
all_data=[]
for company in companies:
    params ={"q":company,"language":"en","apiKey":NEWS_API_KEY}
    response = requests.get("https://newsapi.org/v2/everything",params=params)
    if(response.status_code!=200):
        print("While handling ",company," Error ",response.status_code, "occurred")
        continue
    articles=response.json()["articles"]
    for article in articles:
        article["Company"]=company
    all_data.extend(articles)

for article in all_data:
    article["source"]=article["source"]["name"]
all_data_df=pd.DataFrame(all_data)
conn=sqlite3.connect("finance_data.db")
all_data_df.to_sql("news_history", conn, if_exists="replace", index=False)

conn.close()
print("Finished Succesfully")
