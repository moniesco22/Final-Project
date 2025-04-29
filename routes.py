# Moved routes to a separate module
from flask import Blueprint, request, make_response, render_template, redirect, url_for, jsonify, Response, send_from_directory
from sqlalchemy import text
from models import db
from decorators import require_cookie
import time

routes = Blueprint('routes', __name__)

@routes.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        # Create response object
        resp = make_response(redirect(url_for('routes.dashboard')))
        
        # Set cookies with reasonable expiration time (30 days)
        resp.set_cookie('username', username, max_age=30*24*60*60)
        resp.set_cookie('email', email, max_age=30*24*60*60)
        
        return resp
    return render_template("login.html")

@routes.route("/sample/<int:hshd_num>")
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
    
    with db.session.connection() as conn:
        result = conn.execute(query, {"hshd": hshd_num})
        columns = [desc[0] for desc in result.cursor.description]
        rows = result.fetchall()
        
    return render_template("table.html", rows=rows, columns=columns)

@routes.route("/")
@require_cookie
def dashboard():
    return render_template("dashboard.html")

# Serve static files from the 'Create' directory
@routes.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(os.path.join(app.root_path, 'Create'), filename)

@routes.route("/dashboard_data")
@require_cookie
def dashboard_data():
    # Combine all queries into one JSON response
    queries = {
        "engagement": """
            SELECT YEAR, WEEK_NUM, SUM(SPEND) as total_spend, COUNT(DISTINCT HSHD_NUM) as unique_households
            FROM transactions
            GROUP BY YEAR, WEEK_NUM
            ORDER BY YEAR, WEEK_NUM
        """,
        "demographics": """
            SELECT h.L, h.AGE_RANGE, AVG(t.SPEND) as avg_spend
            FROM households h
            JOIN transactions t ON h.HSHD_NUM = t.HSHD_NUM
            GROUP BY h.L, h.AGE_RANGE
        """,
        "segmentation": """
            SELECT h.HSHD_NUM, h.L, h.AGE_RANGE, SUM(t.SPEND) as total_spend
            FROM households h
            JOIN transactions t ON h.HSHD_NUM = t.HSHD_NUM
            GROUP BY h.HSHD_NUM, h.L, h.AGE_RANGE
        """,
        "loyalty": """
            SELECT h.L, AVG(t.SPEND) as avg_spend, COUNT(t.BASKET_NUM) as purchase_frequency
            FROM households h
            JOIN transactions t ON h.HSHD_NUM = t.HSHD_NUM
            GROUP BY h.L
        """,
        "basket": """
            SELECT t.BASKET_NUM, STRING_AGG(p.COMMODITY, ', ') as products
            FROM transactions t
            JOIN products p ON t.PRODUCT_NUM = p.PRODUCT_NUM
            GROUP BY t.BASKET_NUM
        """,
        "seasonal": """
            SELECT MONTH(PURCHASE_) as month, SUM(SPEND) as total_spend
            FROM transactions
            GROUP BY MONTH(PURCHASE_)
        """,
        "brand": """
            SELECT p.BRAND_TY, AVG(t.SPEND) as avg_spend
            FROM transactions t
            JOIN products p ON t.PRODUCT_NUM = p.PRODUCT_NUM
            GROUP BY p.BRAND_TY
        """,
        "clv": """
            SELECT h.HSHD_NUM, SUM(t.SPEND) as total_spend
            FROM households h
            JOIN transactions t ON h.HSHD_NUM = t.HSHD_NUM
            GROUP BY h.HSHD_NUM
        """,
        "churn": """
            SELECT h.HSHD_NUM, MAX(t.PURCHASE_) as last_purchase_date
            FROM households h
            JOIN transactions t ON h.HSHD_NUM = t.HSHD_NUM
            GROUP BY h.HSHD_NUM
        """,
        "socioeconomic": """
            SELECT h.L, h.AGE_RANGE, AVG(t.SPEND) as avg_spend
            FROM households h
            JOIN transactions t ON h.HSHD_NUM = t.HSHD_NUM
            GROUP BY h.L, h.AGE_RANGE
        """,
        "regional": """
            SELECT t.STORE_R, AVG(t.SPEND) as avg_spend
            FROM transactions t
            GROUP BY t.STORE_R
        """,
        "demand": """
            SELECT p.COMMODITY, SUM(t.SPEND) as total_spend
            FROM transactions t
            JOIN products p ON t.PRODUCT_NUM = p.PRODUCT_NUM
            GROUP BY p.COMMODITY
        """
    }

    visualizations_data = {}
    with db.session.connection() as conn:
        for key, query in queries.items():
            result = conn.execute(text(query))
            visualizations_data[key] = [dict(row) for row in result.mappings()]

    return jsonify(visualizations_data)

@routes.route("/dashboard_progress")
@require_cookie
def dashboard_progress():
    def generate():
        progress_steps = [
            "engagement", "demographics", "segmentation", "loyalty",
            "basket", "seasonal", "brand", "clv",
            "churn", "socioeconomic", "regional", "demand"
        ]
        total_steps = len(progress_steps)

        for i, step in enumerate(progress_steps):
            # Simulate query execution time
            time.sleep(0.5)  # Replace with actual query execution if needed
            progress = int(((i + 1) / total_steps) * 100)
            yield f"data: {progress}\n\n"

    return Response(generate(), content_type="text/event-stream")

@routes.route("/reload_data")
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

@routes.route("/search", methods=["GET", "POST"])
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

@routes.route("/demographics")
@require_cookie
def demographics():
    query = text("""
    SELECT h.HH_SIZE, h.CHILDREN, h.INCOME_RANGE, AVG(t.SPEND) as avg_spend
    FROM households h
    JOIN transactions t ON h.HSHD_NUM = t.HSHD_NUM
    GROUP BY h.HH_SIZE, h.CHILDREN, h.INCOME_RANGE
    ORDER BY h.HH_SIZE, h.CHILDREN, h.INCOME_RANGE
    """)
    
    with db.session.connection() as conn:
        result = conn.execute(query)
        columns = [desc[0] for desc in result.cursor.description]
        rows = result.fetchall()
        
    return render_template("table.html", rows=rows, columns=columns)

@routes.route("/spending_trends")
@require_cookie
def spending_trends():
    query = text("""
        SELECT YEAR, WEEK_NUM, SUM(SPEND) as total_spend
        FROM transactions
        GROUP BY YEAR, WEEK_NUM
        ORDER BY YEAR, WEEK_NUM
    """)
    
    with db.session.connection() as conn:
        result = conn.execute(query)
        columns = [desc[0] for desc in result.cursor.description]
        rows = result.fetchall()
        
    return render_template("table.html", rows=rows, columns=columns)

@routes.route("/upload_data", methods=["GET", "POST"])
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