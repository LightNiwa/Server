from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField, StringField, FileField
from flaskckeditor import CKEditor


class CKEditorForm(FlaskForm, CKEditor):
    title = StringField()
    cover = FileField()
    tags = StringField()
    content = TextAreaField()
    done = SubmitField('done')
