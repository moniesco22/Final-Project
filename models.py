# Moved database models to a separate module
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship

db = SQLAlchemy()

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