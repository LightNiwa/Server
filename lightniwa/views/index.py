import os
from random import randint

from flask import Blueprint
from flask import render_template
from flask import send_from_directory

from database import Article, User, db_session

mod = Blueprint('/', __name__, url_prefix='/')


@mod.route('/')
def index():
    articles = db_session.query(Article, User) \
        .join(User, Article.create_user_id == User.id).order_by(Article.id.desc())
    return render_template('index.html', articles=articles)


@mod.route('tag/<int:tag_id>')
def articles(tag_id):
    articles = db_session.query(Article, User).filter(Article.tags.like('%' + str(tag_id) + '%'))\
        .join(User, Article.create_user_id == User.id).order_by(Article.id.desc())
    return render_template('articles.html', articles=articles)


@mod.route('avatar')
def avatar():
    path = os.path.abspath(os.path.join('lightniwa/static/image/flowersspringimg/'))
    files = os.listdir(path)
    position = randint(0, len(files))
    return add_header(send_from_directory(path, files[position]))


@mod.route('sign')
def sign():
    path = os.path.abspath(os.path.join('lightniwa/static/image/flowersspringev/'))
    files = os.listdir(path)
    position = randint(0, len(files))
    return add_header(send_from_directory(path, files[position]))


def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    # r.headers['Cache-Control'] = 'public, max-age=0'
    return r
