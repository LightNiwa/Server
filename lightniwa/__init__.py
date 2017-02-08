from flask import Flask, render_template
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_assets import Environment, Bundle
import flask_login as login

app = Flask(__name__)
app.config.from_object('config')

from babel import dates
from database import db_session, Article, Book, Volume, Chapter, User, Anime
from lightniwa.admin.index import AdminIndex
from lightniwa.admin.moe import MoeView

assets = Environment(app)
css = Bundle('../node_modules/material-design-lite/material.min.css',
             'css/style.css',
             'css/font.css',
             output='css/mdl.m.css')
js = Bundle('../node_modules/material-design-lite/material.min.js',
            'js/base.js',
            output='js/mdl.m.js')
assets.register('css_base', css)
assets.register('js_base', js)
assets.init_app(app)

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@app.template_filter('datetime')
def format_datetime(value, format='medium'):
    if format == 'full':
        format="EEEE, d. MMMM y 'at' HH:mm"
    elif format == 'medium':
        format="EE dd.MM.y HH:mm"
    return dates.format_datetime(value, format)


def init_login():
    login_manager = login.LoginManager()
    login_manager.init_app(app)

    # Create user loader function
    @login_manager.user_loader
    def load_user(user_id):
        return db_session.query(User).get(user_id)

init_login()


class AuthModelView(ModelView):
    def is_accessible(self):
        if login.current_user.is_authenticated:
            self.can_create = login.current_user and login.current_user.level >= 2
            self.can_view_details = login.current_user and login.current_user.level >= 2
            self.can_edit = login.current_user and login.current_user.level >= 3
            self.can_delete = login.current_user and login.current_user.level >= 4
        return login.current_user.is_authenticated and self.can_view_details


admin = Admin(app, name='LightNiwa', index_view=AdminIndex(), base_template='admin/login.html', template_mode='bootstrap3')
admin.add_view(AuthModelView(Article, db_session, endpoint='article/super'))
admin.add_view(AuthModelView(Anime, db_session, endpoint='anime'))
admin.add_view(AuthModelView(Book, db_session, endpoint='book'))
admin.add_view(AuthModelView(Volume, db_session, endpoint='volume'))
admin.add_view(AuthModelView(Chapter, db_session, endpoint='chapter'))
admin.add_view(AuthModelView(User, db_session, endpoint='user'))
admin.add_view(MoeView(name='Moe', endpoint='moe'))

from lightniwa.views import index
from lightniwa.views import article
app.register_blueprint(index.mod)
app.register_blueprint(article.mod)

from lightniwa.api import core
app.register_blueprint(core.mod)
