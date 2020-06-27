from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "Users"
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=True)

class Book(db.Model):
    __tablename__ = "Books"
    book_id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String, nullable=False)
    title = db.Column(db.String, nullable=False)
    author = db.Column(db.String, nullable=False)
    year = db.Column(db.Integer, nullable=False)

class Review(db.Model):
    __tablename__ = "Reviews"
    review_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("Users.user_id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("Books.book_id"), nullable=False)
    review_rate = db.Column(db.Integer, nullable=False)
    review_content = db.Column(db.Text, nullable=True)
