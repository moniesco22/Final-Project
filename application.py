from flask import Flask, request, make_response, render_template, redirect, url_for
from functools import wraps
import os
import pandas as pd
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy import text, create_engine
from werkzeug.utils import secure_filename
import urllib



# Initialize Flask app
app = Flask(__name__)

# Load environment variables
load_dotenv()

# Configure SQLAlchemy
params = urllib.parse.quote_plus(os.environ["SQLAZURECONNSTR_AZURE_SQL_CONNECTIONSTRING"])
app.config['SQLALCHEMY_DATABASE_URI'] = f'mssql+pyodbc:///?odbc_connect={params}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

#Configure upload settings 
ALLOWED_EXTENSIONS = {'csv'}
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDERS'] = UPLOAD_FOLDER


# Define models
class Household(db.Model):
    __tablename__ = 'households'
    HSHD_NUM = db.Column(db.Integer, primary_key=True)
    HH_SIZE = db.Column(db.String(50))
    CHILDREN = db.Column(db.String(50))
    INCOME_RANGE = db.Column(db.String(50))
    transactions = relationship('Transaction', backref='household')

class Product(db.Model):
    __tablename__ = 'products'
    PRODUCT_NUM = db.Column(db.Integer, primary_key=True)
    DEPARTMENT = db.Column(db.String(100))
    COMMODITY = db.Column(db.String(100))
    transactions = relationship('Transaction', backref='product')

class Transaction(db.Model):
    __tablename__ = 'transactions'
    HSHD_NUM = db.Column(db.Integer, db.ForeignKey('households.HSHD_NUM'))
    BASKET_NUM = db.Column(db.Integer)
    PURCHASE_ = db.Column(db.DateTime)
    PRODUCT_NUM = db.Column(db.Integer, db.ForeignKey('products.PRODUCT_NUM'))
    SPEND = db.Column(db.Float)
    __table_args__ = (
        db.PrimaryKeyConstraint('HSHD_NUM', 'BASKET_NUM', 'PURCHASE_', 'PRODUCT_NUM'),
    )

# Cookie protection decorator
def require_cookie(view_func):
    @wraps(view_func)
    def decorated_function(*args, **kwargs):
        if not check_user_cookie():
            return redirect(url_for('register'))
        return view_func(*args, **kwargs)
    return decorated_function

# Cookie checking function
def check_user_cookie():
    return 'username' in request.cookies

# Routes
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        # Create response object
        resp = make_response(redirect(url_for('index')))
        
        # Set cookies with reasonable expiration time (30 days)
        resp.set_cookie('username', username, max_age=30*24*60*60)
        resp.set_cookie('email', email, max_age=30*24*60*60)
        
        return resp
    return render_template("login.html")

@app.route("/sample/<int:hshd_num>")
@require_cookie
def sample(hshd_num):
    query = text("""
    SELECT t.HSHD_NUM, t.BASKET_NUM, t.PURCHASE_, t.PRODUCT_NUM, 
           p.DEPARTMENT, p.COMMODITY
    FROM transactions t
    JOIN products p ON t.PRODUCT_NUM = p.PRODUCT_NUM
    WHERE t.HSHD_NUM = :hshd
    ORDER BY t.HSHD_NUM, t.BASKET_NUM, t.PURCHASE_, t.PRODUCT_NUM, 
           p.DEPARTMENT, p.COMMODITY
    """)
    
    results = db.session.execute(query, {"hshd": hshd_num})
    columns = [desc[0] for desc in results.cursor.description]
    return render_template("table.html", rows=results.fetchall(), columns=columns)

@app.route("/")
@require_cookie
def dashboard():
    return render_template("dashboard.html")

@app.route("/reload_data")
def reload_data():
    try:
        # Drop tables
        db.session.execute(text("DROP TABLE IF EXISTS households"))
        db.session.execute(text("DROP TABLE IF EXISTS products"))
        db.session.execute(text("DROP TABLE IF EXISTS transactions"))
        db.session.commit()
        
        print("Old tables dropped ✅")
        
        # Reload households
        df_households = pd.read_csv("400_households.csv")
        df_households.columns = df_households.columns.str.strip()
        df_households.to_sql("households", db.engine, if_exists="replace", index=False)
        print("Households reloaded ✅")
        
        # Reload products
        products_total_rows = sum(1 for _ in open("400_products.csv")) - 1
        uploaded_products = 0
        chunksize_products = 1000
        
        for chunk in pd.read_csv("400_products.csv", chunksize=chunksize_products):
            chunk.columns = chunk.columns.str.strip()
            chunk.to_sql("products", db.engine, if_exists="append", index=False)
            uploaded_products += len(chunk)
            percent = (uploaded_products / products_total_rows) * 100
            print(f"Products Reload Progress: {percent:.2f}%")
        
        # Reload transactions
        transactions_total_rows = sum(1 for _ in open("400_transactions.csv")) - 1
        uploaded_transactions = 0
        chunksize_transactions = 5000
        
        for chunk in pd.read_csv("400_transactions.csv", chunksize=chunksize_transactions):
            chunk.columns = chunk.columns.str.strip()
            chunk.to_sql("transactions", db.engine, if_exists="append", index=False)
            uploaded_transactions += len(chunk)
            percent = (uploaded_transactions / transactions_total_rows) * 100
            print(f"Transactions Reload Progress: {percent:.2f}%")
            
        db.session.commit()
        return "<h1>Data Reload Completed Successfully ✅</h1><p>Check /dashboard to explore.</p>"
        
    except Exception as e:
        db.session.rollback()
        return f"<h1>Reload Failed ❌</h1><p>Error: {str(e)}</p>"

@app.route("/search", methods=["GET", "POST"])
@require_cookie
def search():
    results = []
    columns = []
    
    if request.method == "POST":
        hshd_num = request.form.get("hshd")
        if hshd_num:
            query = text("""
                SELECT t.HSHD_NUM, t.BASKET_NUM, t.PURCHASE_, t.PRODUCT_NUM, 
                       p.DEPARTMENT, p.COMMODITY
                FROM transactions t
                JOIN products p ON t.PRODUCT_NUM = p.PRODUCT_NUM
                WHERE t.HSHD_NUM = :hshd
                ORDER BY t.HSHD_NUM, t.BASKET_NUM, t.PURCHASE_, t.PRODUCT_NUM, 
                       p.DEPARTMENT, p.COMMODITY
            """)
            
            results = db.session.execute(query, {"hshd": int(hshd_num)})
            columns = [desc[0] for desc in results.cursor.description]
            return render_template("search.html", rows=results.fetchall(), columns=columns)
    
    return render_template("search.html")

@app.route("/demographics")
@require_cookie
def demographics():
    query = text("""
        SELECT h.HH_SIZE, h.CHILDREN, h.INCOME_RANGE, AVG(t.SPEND) as avg_spend
        FROM households h
        JOIN transactions t ON h.HSHD_NUM = t.HSHD_NUM
        GROUP BY h.HH_SIZE, h.CHILDREN, h.INCOME_RANGE
        ORDER BY h.HH_SIZE, h.CHILDREN, h.INCOME_RANGE
    """)
    
    results = db.session.execute(query)
    return render_template("table.html", rows=results.fetchall(), 
                         columns=[desc[0] for desc in results.cursor.description])

@app.route("/spending_trends")
@require_cookie
def spending_trends():
    query = text("""
        SELECT YEAR, WEEK_NUM, SUM(SPEND) as total_spend
        FROM transactions
        GROUP BY YEAR, WEEK_NUM
        ORDER BY YEAR, WEEK_NUM
    """)
    
    results = db.session.execute(query)
    return render_template("table.html", rows=results.fetchall(),
                         columns=[desc[0] for desc in results.cursor.description])

@app.route("/upload_data", methods=["GET", "POST"])
def upload_data():
    if request.method == "POST":
        file = request.files.get('file')
        data_type = request.form.get('data_type')  # New households / transactions / products
        
        if file and data_type:
            try:
                # Read the uploaded CSV into a DataFrame
                df = pd.read_csv(file)
                df.columns = df.columns.str.strip()
                
                # Drop existing table and replace it
                if data_type == "households":
                    db.session.execute(text("DROP TABLE IF EXISTS households"))
                    db.session.commit()
                    df.to_sql("households", db.engine, if_exists="replace", index=False)
                    
                elif data_type == "products":
                    db.session.execute(text("DROP TABLE IF EXISTS products"))
                    db.session.commit()
                    df.to_sql("products", db.engine, if_exists="replace", index=False)
                    
                elif data_type == "transactions":
                    db.session.execute(text("DROP TABLE IF EXISTS transactions"))
                    db.session.commit()
                    df.to_sql("transactions", db.engine, if_exists="replace", index=False)
                    
                db.session.commit()
                return render_template("upload_result.html", success=True, data_type=data_type)
            except Exception as e:
                db.session.rollback()
                return render_template("upload_result.html", success=False, error=str(e))
        
        return render_template("upload_result.html", success=False, error="Missing file or data type.")
    
    return render_template("upload_data.html")

if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)