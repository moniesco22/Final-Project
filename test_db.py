import os
from sqlalchemy import create_engine, text

# dw, these have been reset, I'm just too burnt out to replace all these gadakihglaijhlodji
# Replace with your actual username and password
username = "cloud-is-cool"   # your SQL server username
#password = "MyPassword123!"  # your SQL server password

# If your password contains special characters like "!", "@", "#", encode them
# Here's the password URL-encoded manually:
# "!" -> "%21"
# so MyPassword123! -> MyPassword123%21

password = "Supa%211111"

# Full connection string (important: no space between parts!)
conn = (
    f"mssql+pyodbc://{username}:{password}"
    "@final-server-2025.database.windows.net:1433/final-db"
    "?driver=ODBC+Driver+18+for+SQL+Server"
)

# Create the SQLAlchemy engine
engine = create_engine(conn)

# Run a simple query to count rows in each table
for table_name in ("households", "transactions", "products"):
    with engine.connect() as conn:
        count = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
        print(f"Table '{table_name}': {count} rows")
