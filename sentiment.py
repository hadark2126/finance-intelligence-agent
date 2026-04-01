import pandas as pd
import sqlite3


pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)
pd.set_option("display.width", None)


conn=sqlite3.connect("finance_data.db")
news_df=pd.read_sql("SELECT * FROM news_history",conn)
# print(news_df)
print(news_df.columns.tolist())