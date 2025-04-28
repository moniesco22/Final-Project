from flask import Flask
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import os
import urllib
from models import db
from routes import routes

# Initialize Flask app
app = Flask(__name__)

# Load environment variables
load_dotenv()

# Configure SQLAlchemy
params = urllib.parse.quote_plus(os.environ["SQLAZURECONNSTR_AZURE_SQL_CONNECTIONSTRING"])
app.config['SQLALCHEMY_DATABASE_URI'] = f'mssql+pyodbc:///?odbc_connect={params}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Configure upload settings
ALLOWED_EXTENSIONS = {'csv'}
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDERS'] = UPLOAD_FOLDER

# Register blueprints
app.register_blueprint(routes)

if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)