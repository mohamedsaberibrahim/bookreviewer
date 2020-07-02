import os
import requests
from flask import Flask, session, render_template, jsonify, request, redirect, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from  sqlalchemy.sql.expression import func, select

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    try:
        if session['id']:
            return redirect(url_for('homepage'))
    except KeyError:
        return render_template("index.html")


@app.route("/signin", methods=["POST"])
def signin():
    name = request.form.get("name")

    password = request.form.get("password")

    user = db.execute("SELECT * FROM users WHERE username = :name", {"name": name}).fetchone()

    if user is None:
        return render_template("index.html", signinFormError="No such user named {}! Please Sign up!".format(name))

    elif user.password != password:
        return render_template("index.html", signinFormError="Invalid password!")

    else:
        session['id'] = user.user_id
        session['username'] = user.username
        return redirect(url_for('homepage'))


@app.route("/signup", methods=["POST"])
def signup():
    
    mail = request.form.get("Email")

    user = db.execute("SELECT * FROM users WHERE email = :mail", {"mail": mail}).fetchone()

    if user:
        return render_template("index.html", signupFormError="There is already an account with e-mail: {}!".format(mail))

    name = request.form.get("name")

    user = db.execute("SELECT * FROM users WHERE username = :name", {"name": name}).fetchone()

    if user:
        return render_template("index.html", signupFormError="There is already an account with username {}!".format(name))

    password = request.form.get("password")
    password_check = request.form.get("password_check")

    if password_check != password:
        return render_template("index.html", signupFormError="Not matched passwords!")
    db.execute("INSERT INTO users (username, password, email) VALUES (:username, :password, :email)",
            {"username": name, "password": password, "email":mail})
    db.commit()
    return render_template("index.html", signupFormInfo="Signed up successfully, Please Sign in!")

@app.route("/homepage")
def homepage():
    try:
        if session['id']:
            books = db.execute("SELECT * FROM books ORDER BY random() LIMIT 10").fetchall()
            return render_template("homepage.html", Books=books, username=session['username'], title="Recommendations")
    except KeyError:
        return render_template("index.html")
    
@app.errorhandler(404)
@app.errorhandler(405)
def page_not_found(e):
    # note that we set the 404 status explicitly
    try:
        if session['id']:
            return render_template("homepage.html", username=session['username'], title="Error! Not found (this page does not exist).")
    except KeyError:
        return render_template("index.html")

@app.route("/logout", methods=["GET"])
def logout():
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('index'))


@app.route("/searchresults", methods=["POST"])
def search():
    search_by = request.form.get("search_type")
    
    search_word = request.form.get("search_word")
    if search_by != 'year':
        books = db.execute("SELECT * FROM books where {} Like '%{}%'".format(search_by, search_word)).fetchall()
    else:
        books = db.execute("SELECT * FROM books where {} = '{}'".format(search_by, search_word)).fetchall()
    return render_template("homepage.html", Books=books, username=session['username'],
     title="Search results of books with {}: {}".format(search_by, search_word))

@app.route("/books/<int:book_id>")
def book(book_id):
    try:
        if session['id']:
            book = db.execute("SELECT * FROM books where book_id = '{}'".format(book_id)).fetchone()
            if book is not None:
                reviews = db.execute("SELECT * FROM reviews where book_id = :id",{"id": book.book_id}).fetchall()
                goodreadsData = api_getdata(book)
                addReviewError = request.args.get('addReviewError') if request.args.get('addReviewError') is not None else ""
                return render_template("book.html", book_data=book, goodreadsData=goodreadsData,
                reviews=reviews, username=session['username'], addReviewError=addReviewError)
            else:
                return render_template("homepage.html", username=session['username'], title="Error! Not found (this page does not exist).")
    except KeyError:
        return render_template("index.html")


def api_getdata(book):
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "MJmjs7DVNjXsh7aWKwnx2A", "isbns": book.isbn})
    if res.status_code != 200:
        reviews_count = False
        average_rating = False
    else:
        data = res.json()
        print(data)
        reviews_count = data['books'][0]['work_ratings_count']
        average_rating = data['books'][0]['average_rating']
    goodreadsData = {'reviews_count': reviews_count, 'average_rating': average_rating}
    return goodreadsData


@app.route("/addreview/<int:book_id>", methods=["POST"])
def addreview(book_id):
    try:
        if session['id']:
            review_rate = request.form.get("optradio")
            review_content = request.form.get("review_content")
            reviews = db.execute("SELECT * FROM reviews where book_id = :id and user_id = :user_id",
            {"id": book_id, "user_id": session['id']}).fetchall()
            if not reviews:
                db.execute("INSERT INTO reviews (user_id, book_id, review_rate, review_content) VALUES (:user_id, :book_id, :review_rate, :review_content)",
                        {"user_id": session['id'], "book_id": book_id, "review_rate":review_rate, "review_content":review_content})
                db.commit()
                return redirect(url_for('book', book_id=book_id))
            else:
                return redirect(url_for('book', book_id=book_id,
                 addReviewError="You already have a review for this book!"))
    except KeyError:
        return render_template("index.html")

@app.route("/myreviews")
def getuserreviews():
    try:
        if session['id']:
            reviews = db.execute("SELECT books.book_id, books.title, reviews.review_content, reviews.review_rate FROM reviews left join  books ON reviews.book_id=books.book_id where user_id = :id",{"id": session['id']}).fetchall()
            return render_template("reviews.html", reviews=reviews, username=session['username'])
    except KeyError:
        return render_template("index.html")

@app.route("/api/<string:isbn>", methods =["GET"])
def books_api(isbn):
    # Make sure book exists.
    
    book = db.execute("SELECT * FROM books where isbn = '{}'".format(isbn)).fetchone()
    if book is None:
        return jsonify({"error": "Invalid book_id"}), 422

    average_score_output = db.execute("SELECT AVG(review_rate) FROM reviews where book_id = {}".format(book.book_id)).fetchall()
    review_count = db.execute("SELECT COUNT(*) FROM reviews where book_id = {}".format(book.book_id)).fetchall()
    if average_score_output[0][0] is None:
        average_score_api = 0 
    else:
        average_score_api = average_score_output[0][0]
    return jsonify({
            "title": book.title,
            "author": book.author,
            "year": book.year,
            "isbn": book.isbn,
            "review_count": str(review_count[0][0]),
            "average_score": str(average_score_api)
        }), 200