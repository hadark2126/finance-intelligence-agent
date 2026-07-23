import pandas as pd
import sqlite3
from transformers import pipeline


pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)
pd.set_option("display.width", None)


conn=sqlite3.connect("finance_data.db")
news_df=pd.read_sql("SELECT * FROM news_history",conn)
# # print(news_df)
# print(news_df.columns.tolist())
sentiment_pipeline = pipeline("text-classification", model="ProsusAI/finbert")

labels=[]
scores=[]
for title in news_df["title"]:
    result=sentiment_pipeline(title)
    labels.append(result[0]['label'])
    scores.append(result[0]['score'])

news_df["sentiment_label"]=labels
news_df["sentiment_score"]=scores

# print(news_df[["title", "Company", "sentiment_label", "sentiment_score"]])

news_df.to_sql("news_history", conn, if_exists="replace", index=False)

conn.close()

print("Finished Succesfully")


# test_headline = "Apple hits record revenue in Q1"
# print(sentiment_pipeline(test_headline))

# test_headline = "Tesla faces massive recall amid safety concerns"
# print(sentiment_pipeline(test_headline))