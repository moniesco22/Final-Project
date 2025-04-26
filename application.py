import os
import pandas as pd

from flask import Flask, render_template, request
from sqlalchemy import create_engine, text

app = Flask(__name__)
db_user = "cloud-compute-final-server-admin"
db_pass = "tc$lLDGC7tBSzmI5"
from urllib.parse import quote_plus
db_pass = quote_plus(db_pass)
fallback = (f"mssql+pyodbc://{db_user}:{db_pass}@cloud-compute-final-server.database.windows.net:1433/cloud-compute-final-database?driver=ODBC+Driver+18+for+SQL+Server")
conn_str = os.getenv("SQLAZURECONNSTR_DefaultConnection", fallback)

# Create engine
engine = create_engine(conn_str)

@app.route("/")
def home():
    return "<h1>Welcome to CLV App!</h1><p>Go to /sample/10 or /search</p>"


# @app.route("/sample/<int:hshd_num>")
# def sample(hshd_num):
#     query = text("""
#         SELECT t.HSHD_NUM, t.BASKET_NUM, t.PURCHASE_, t.PRODUCT_NUM,
#                p.DEPARTMENT, p.COMMODITY
#         FROM transactions t
#         JOIN products p ON t.PRODUCT_NUM = p.PRODUCT_NUM
#         WHERE t.HSHD_NUM = :hshd
#         ORDER BY t.HSHD_NUM, t.BASKET_NUM, t.PURCHASE_, t.PRODUCT_NUM, p.DEPARTMENT, p.COMMODITY
#     """)
#     with engine.connect() as conn:
#         resultproxy = conn.execute(query, {"hshd": hshd_num})
#         results = resultproxy.fetchall()
#         columns = resultproxy.keys()  # <-- grab column names
#     return render_template("table.html", rows=results, columns=columns)


# @app.route("/register", methods=["GET", "POST"])
# def register():
#     if request.method == "POST":
#         username = request.form['username']
#         password = request.form['password']
#         email = request.form['email']
#         # Just display it for now (later you can save to database if you want)
#         return f"<h1>Registered: {username} ({email})</h1>"
#     return render_template("login.html")

# @app.route("/dashboard")
# def dashboard():
#     return render_template("dashboard.html")



@app.route("/reload_data")
def reload_data():
    try:
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS households"))
            conn.execute(text("DROP TABLE IF EXISTS products"))
            conn.execute(text("DROP TABLE IF EXISTS transactions"))
        print("Old tables dropped ✅")

        # Reload households
        df_households = pd.read_csv("400_households.csv")
        df_households.columns = df_households.columns.str.strip()
        df_households.to_sql("households", engine, if_exists="replace", index=False)
        print("Households reloaded ✅")

        # Reload products
        products_total_rows = sum(1 for _ in open("400_products.csv")) - 1
        uploaded_products = 0
        chunksize_products = 1000
        for chunk in pd.read_csv("400_products.csv", chunksize=chunksize_products):
            chunk.columns = chunk.columns.str.strip()
            chunk.to_sql("products", engine, if_exists="append", index=False)
            uploaded_products += len(chunk)
            percent = (uploaded_products / products_total_rows) * 100
            print(f"Products Reload Progress: {percent:.2f}%")

        # Reload transactions
        transactions_total_rows = sum(1 for _ in open("400_transactions.csv")) - 1
        uploaded_transactions = 0
        chunksize_transactions = 5000
        for chunk in pd.read_csv("400_transactions.csv", chunksize=chunksize_transactions):
            chunk.columns = chunk.columns.str.strip()
            chunk.to_sql("transactions", engine, if_exists="append", index=False)
            uploaded_transactions += len(chunk)
            percent = (uploaded_transactions / transactions_total_rows) * 100
            print(f"Transactions Reload Progress: {percent:.2f}%")

        return "<h1>Data Reload Completed Successfully ✅</h1><p>Check /dashboard to explore.</p>"

    except Exception as e:
        return f"<h1>Reload Failed ❌</h1><p>Error: {str(e)}</p>"

#@app.route("/search", methods=["GET", "POST"])
# def search():
#     results = []
#     columns = []
#     if request.method == "POST":
#         hshd_num = request.form.get("hshd")
#         if hshd_num:
#             query = text("""
#                 SELECT t.HSHD_NUM, t.BASKET_NUM, t.PURCHASE_, t.PRODUCT_NUM,
#                        p.DEPARTMENT, p.COMMODITY
#                 FROM transactions t
#                 JOIN products p ON t.PRODUCT_NUM = p.PRODUCT_NUM
#                 WHERE t.HSHD_NUM = :hshd
#                 ORDER BY t.HSHD_NUM, t.BASKET_NUM, t.PURCHASE_, t.PRODUCT_NUM, p.DEPARTMENT, p.COMMODITY
#             """)
#             with engine.connect() as conn:
#                 resultproxy = conn.execute(query, {"hshd": int(hshd_num)})

#                 results = resultproxy.fetchall()
#                 columns = resultproxy.keys()  # <-- get column names
#     return render_template("search.html", rows=results, columns=columns)

# @app.route("/demographics")
# def demographics():
#     query = text("""
#         SELECT h.HH_SIZE, h.CHILDREN, h.INCOME_RANGE, AVG(t.SPEND) as avg_spend
#         FROM households h
#         JOIN transactions t ON h.HSHD_NUM = t.HSHD_NUM
#         GROUP BY h.HH_SIZE, h.CHILDREN, h.INCOME_RANGE
#         ORDER BY h.HH_SIZE, h.CHILDREN, h.INCOME_RANGE
#     """)
#     with engine.connect() as conn:
#         results = conn.execute(query).fetchall()
#     return render_template("table.html", rows=results)

# @app.route("/spending_trends")
# def spending_trends():
#     query = text("""
#         SELECT YEAR, WEEK_NUM, SUM(SPEND) as total_spend
#         FROM transactions
#         GROUP BY YEAR, WEEK_NUM
#         ORDER BY YEAR, WEEK_NUM
#     """)
#     with engine.connect() as conn:
#         results = conn.execute(query).fetchall()
#     return render_template("table.html", rows=results)


if __name__ == "__main__":
    app.run(debug=True)
