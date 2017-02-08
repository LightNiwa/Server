import os

from flask import flash
from flask import json
from flask import make_response
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_admin import BaseView, expose
from sqlalchemy import func
from werkzeug.utils import secure_filename
from lightniwa import app

from config import ALLOWED_EXTENSIONS
from database import db_session, Book, Volume
from lightniwa.admin.CKEditorForm import CKEditorForm


class MoeView(BaseView):
    @expose('/')
    def index(self):
        form = CKEditorForm()
        return self.render('admin/moe/index.html', form=form)

    @expose('/note')
    def note(self):
        return self.render('admin/moe/note.html')

    @expose('/post', methods=['POST'])
    def post(self):
        print('post')
        name = request.form.get('name')
        print(name)
        desc = request.form.get('desc')
        print(desc)
        editor = request.form.get('editor')
        print(editor)
        return self.render('admin/moe/index.html')

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


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS
