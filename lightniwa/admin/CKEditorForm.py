from flask_wtf import Form
from wtforms import TextAreaField, SubmitField, StringField, FileField
from flaskckeditor import CKEditor


class CKEditorForm(Form, CKEditor):
    title = StringField()
    cover = FileField()
    tags = StringField()
    content = TextAreaField()
    done = SubmitField('done')
