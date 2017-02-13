from flask import redirect, request, url_for
from flask_admin import AdminIndexView, helpers, expose
from werkzeug.security import check_password_hash, generate_password_hash
from wtforms import form, fields, validators
import flask_login as login

from database import User, db_session


class AdminIndex(AdminIndexView):
    @expose('/')
    def index(self):
        if not login.current_user.is_authenticated:
            return redirect(url_for('.login_view'))
        return super(AdminIndex, self).index()

    @expose('/login/', methods=('GET', 'POST'))
    def login_view(self):
        print('login')
        form = LoginForm(request.form)
        msg = ''
        if helpers.validate_form_on_submit(form):
            try:
                if form.validate_login():
                    user = form.get_user()
                    login.login_user(user)
            except Exception:
                msg = 'Invalid user or password'
                pass

        if login.current_user.is_authenticated:
            return redirect(url_for('.index'))
        self._template_args['msg'] = msg
        self._template_args['form'] = form
        return super(AdminIndex, self).index()

    @expose('/register/', methods=('GET', 'POST'))
    def register_view(self):
        form = RegistrationForm(request.form)
        if helpers.validate_form_on_submit(form):
            user = User()

            form.populate_obj(user)
            # we hash the users password to avoid saving it as plaintext in the db,
            # remove to use plain text:
            user.password = generate_password_hash(form.password.data)

            db_session.add(user)
            db_session.commit()

            login.login_user(user)
            return redirect(url_for('.index'))
        link = '<p>Already have an account? <a href="' + url_for('.login_view') + '">Click here to log in.</a></p>'
        self._template_args['form'] = form
        self._template_args['link'] = link
        return super(AdminIndex, self).index()

    @expose('/logout/')
    def logout_view(self):
        login.logout_user()
        return redirect(url_for('.index'))


class LoginForm(form.Form):
    username = fields.StringField(validators=[validators.required()])
    password = fields.PasswordField(validators=[validators.required()])

    def validate_login(self):
        user = self.get_user()

        if user is None or not check_password_hash(user.password, self.password.data):
            raise validators.ValidationError('Invalid user or password')
        else:
            return True

    def get_user(self):
        return db_session.query(User).filter_by(username=self.username.data).first()


class RegistrationForm(form.Form):
    username = fields.StringField(validators=[validators.required()])
    email = fields.StringField()
    password = fields.PasswordField(validators=[validators.required()])

    def validate_login(self, field):
        if db_session.query(User).filter_by(username=self.username.data).count() > 0:
            raise validators.ValidationError('Duplicate username')