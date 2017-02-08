from flask_wtf import Form
from wtforms import TextAreaField, SubmitField, StringField
from flaskckeditor import CKEditor


class CKEditorForm(Form, CKEditor):
    title = StringField()
    editor = TextAreaField()
    done = SubmitField('done')
