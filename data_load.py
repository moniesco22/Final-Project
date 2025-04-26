import pandas as pd
from sqlalchemy import create_engine, text
import urllib
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get credentials from environment variables
db_servername = os.getenv("DB_SERVERNAME")
db_name = os.getenv("DB_NAME")
db_port = os.getenv("DB_PORT")
db_username = os.getenv("DB_USERNAME")
db_password = os.getenv("DB_PASSWORD")

# Connection string
conn_str = (
    f"mssql+pyodbc://{db_username}:{db_password}"
    f"@{db_servername}.database.windows.net:{db_port}/{db_name}"
    "?driver=ODBC+Driver+18+for+SQL+Server"
)

# Create engine
engine = create_engine(conn_str)


engine = create_engine(conn_str)

# Drop old tables first to avoid duplication
with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS households"))
    conn.execute(text("DROP TABLE IF EXISTS products"))
    conn.execute(text("DROP TABLE IF EXISTS transactions"))
print("Old tables dropped ✅")

# Upload households
df_households = pd.read_csv("400_households.csv")
df_households.columns = df_households.columns.str.strip()
df_households.to_sql("households", engine, if_exists="replace", index=False)
print("Uploaded households ✅")

# Upload products with progress tracking
products_file = "400_products.csv"
products_total_rows = sum(1 for _ in open(products_file)) - 1  # minus 1 for header
chunksize_products = 1000

print("Uploading products...")
uploaded_products = 0
for chunk in pd.read_csv(products_file, chunksize=chunksize_products):
    chunk.columns = chunk.columns.str.strip()
    chunk.to_sql("products", engine, if_exists="append", index=False)
    uploaded_products += len(chunk)
    percent = (uploaded_products / products_total_rows) * 100
    print(f"Products Upload Progress: {percent:.2f}%")
print("Uploaded all products ✅")

# Upload transactions with progress tracking
transactions_file = "400_transactions.csv"
transactions_total_rows = sum(1 for _ in open(transactions_file)) - 1  # minus 1 for header
chunksize_transactions = 5000

print("Uploading transactions...")
uploaded_transactions = 0
for chunk in pd.read_csv(transactions_file, chunksize=chunksize_transactions):
    chunk.columns = chunk.columns.str.strip()
    chunk.to_sql("transactions", engine, if_exists="append", index=False)
    uploaded_transactions += len(chunk)
    percent = (uploaded_transactions / transactions_total_rows) * 100
    print(f"Transactions Upload Progress: {percent:.2f}%")
print("Uploaded all transactions ✅")
