import os
import flask_login as login
from flask import make_response
from flask import request
from flask import url_for
from flask_admin import BaseView, expose
from lightniwa import app
from lightniwa.admin.CKEditorForm import CKEditorForm


class TheWorld(BaseView):
    @expose('/')
    def index(self):
        form = CKEditorForm()
        return self.render('admin/theworld/index.html', form=form)

    @expose('/publish')
    def publish(self):
        return

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