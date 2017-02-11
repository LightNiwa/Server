import hashlib
import os
import flask_login as login
import time
from flask import make_response
from flask import request
from flask import url_for
from flask import json, request
from flask_admin import BaseView, expose

from database import db_session, Article
from lightniwa import app, Tag
from lightniwa.admin.CKEditorForm import CKEditorForm


class TheWorld(BaseView):
    @expose('/')
    def index(self):
        form = CKEditorForm()
        return self.render('admin/theworld/index.html', form=form)

    @expose('/tag/<string:tag_name>', methods=['GET'])
    def tag(self, tag_name):
        tags = Tag.query.filter(Tag.name.like('%' + tag_name + '%')).all()
        resp = [tag.to_json() for tag in tags]
        return json.dumps(resp, ensure_ascii=False), 200, {'ContentType': 'application/json'}

    @expose('/post', methods=['POST'])
    def post(self):
        cover = request.files['cover']
        filename = hashlib.md5((str(time.time()) + cover.filename).encode()).hexdigest()\
                   + os.path.splitext(cover.filename)[1]
        path = os.path.join(app.root_path + app.config['UPLOAD_FOLDER'], filename)
        title = request.form.get('title')
        tags = request.form.get('tags')
        content = request.form.get('content')
        a = Article(title=title, content=content)
        a.cover = path
        a.tags = tags
        a.create_user_id = login.current_user.id
        a.create_time = int(time.time())
        cover.save(path)
        db_session.add(a)
        db_session.commit()
        return json.dumps(a.to_json(), ensure_ascii=False), 200, {'ContentType': 'application/json'}

    @expose('/ckupload/', methods=['POST'])
    def upload(self):
        print('ckupload')
        error = ''
        url = ''
        callback = request.args.get("CKEditorFuncNum")

        if request.method == 'POST' and 'upload' in request.files:
            fileobj = request.files['upload']
            fname, fext = os.path.splitext(fileobj.filename)
            rnd_name = '%s%s' % ('ltype', fext)

            filepath = os.path.join(app.config['UPLOAD_FOLDER'], rnd_name)

            dirname = os.path.dirname(filepath)
            if not os.path.exists(dirname):
                try:
                    os.makedirs(dirname)
                except:
                    error = 'ERROR_CREATE_DIR'
            elif not os.access(dirname, os.W_OK):
                error = 'ERROR_DIR_NOT_WRITEABLE'
            if not error:
                fileobj.save(filepath)
                url = url_for('static', filename='%s/%s' % ('upload', rnd_name))
        else:
            error = 'post error'

        res = """
                <script type="text/javascript">
                window.parent.CKEDITOR.tools.callFunction(%s, '%s', '%s');
                </script>
             """ % (callback, url, error)

        response = make_response(res)
        response.headers["Content-Type"] = "text/html"
        return response

    def is_accessible(self):
        return login.current_user.is_authenticated
