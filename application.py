import os

from flask import Flask, session, render_template, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

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


@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response


@app.route("/")
def welcome():
    return render_template("welcome.html")


@app.route("/signup", methods=["POST"])
def signup():
    check = 1
    return render_template("registration.html", check=check)


@app.route("/RegistrationSuccess", methods=["POST"])
def success():
    name = request.form.get("name")
    if db.execute("SELECT * FROM userdetails WHERE name=:name", {"name": name}).rowcount > 0:
        check = -1
        return render_template("registration.html", check=check)
    password = request.form.get("password")
    nick = request.form.get("nick")

    if any(x.isalpha() for x in name) and any(y.isalnum() for y in password):
        if any(not(z.isspace()) for z in nick):
            db.execute("INSERT INTO userdetails (name,password,nick) VALUES (:name,:password,:nick)", {
                       "name": name, "password": password, "nick": nick})
            db.commit()
            nonick = False
            return render_template("success.html", nonick=nonick)
        else:
            nonick = True
            db.execute("INSERT INTO userdetails (name,password) VALUES (:name,:password)", {
                       "name": name, "password": password})
            db.commit()
            return render_template("success.html", nonick=nonick)
    else:
        check = 0
        return render_template("registration.html", check=check)


@app.route("/home", methods=["POST"])
def home():
    name = request.form.get("name")
    password = request.form.get("password")
    if db.execute("SELECT * FROM userdetails WHERE name=:name AND password=:password", {"name": name, "password": password}).rowcount == 0:
        invalid = True
        return render_template("signin.html", invalid=invalid)
    else:
        user = db.execute("SELECT id,name,nick FROM userdetails WHERE name=:name",
                          {"name": name}).fetchone()

        session["user"] = {"logged in": True, "id": user.id, "name": user.name, "nick": user.nick}
        titles = []
        authors = []
        isbns = []
        return render_template("home.html", titles=titles, authors=authors, isbns=isbns, user=session["user"])


@app.route("/signin", methods=["POST"])
def signin():
    invalid = False
    return render_template("signin.html", invalid=invalid)


@app.route("/")
def exit():
    session["user"]["logged in"] = False
    return render_template("welcome.html")


@app.route("/search", methods=["POST"])
def search():
    result = request.form.get("search")
    result = '%'+result+'%'
    titles = db.execute("SELECT * FROM books WHERE title LIKE :result", {"result": result})
    authors = db.execute("SELECT * FROM books WHERE author LIKE :result", {"result": result})
    isbns = db.execute("SELECT * FROM books WHERE isbn LIKE :result", {"result": result})

    return render_template("home.html", titles=titles, authors=authors, isbns=isbns, user=session["user"])


@app.route("/bookdetails/<string:book_id>")
def book(book_id):
    book = db.execute("SELECT * FROM books WHERE id=:id", {"id": book_id}).fetchone()
    reviews = db.execute("SELECT * FROM reviews WHERE book_id=:book_id",
                         {"book_id": book_id}).fetchall()
    reviewdone = False
    return render_template("book.html", book=book, reviews=reviews, reviewdone=reviewdone)


@app.route("/review/update/<int:book_id>", methods=["POST"])
def update(book_id):
    review = request.form.get("review")
    stars = request.form.get("stars")
    x = session["user"]["id"]
    if db.execute("SELECT * FROM reviews WHERE user_id=:user_id AND book_id=:book_id", {"user_id": x, "book_id": book_id}).rowcount == 0:
        db.execute("INSERT INTO reviews (book_id, user_id, review, stars) VALUES (:book_id, :user_id, :review, :stars)", {
            "book_id": book_id, "user_id": x, "review": review, "stars": stars})
        db.commit()
        reviewdone = False
    else:
        reviewdone = True
    book = db.execute("SELECT * FROM books WHERE id=:id", {"id": book_id}).fetchone()
    reviews = db.execute("SELECT * FROM reviews WHERE book_id=:book_id",
                         {"book_id": book_id}).fetchall()
    return render_template("book.html", book=book, reviews=reviews, reviewdone=reviewdone)
