from flask import Blueprint
from flask import json
from flask import render_template
from database import Article, User, db_session

mod = Blueprint('article', __name__, url_prefix='/article')


@mod.route('/<int:article_id>')
def index(article_id):
    article = Article.query.get(article_id)
    if not article:
        return render_template('404.html'), 404
    author = User.query.get(article.create_user_id)
    return render_template('article.html', article=article, author=author)


@mod.route('/<int:article_id>/like')
def like(article_id):
    article = Article.query.get(article_id)
    print(article.like)
    article.like += 1
    print(article.like)
    db_session.commit()
    return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}


