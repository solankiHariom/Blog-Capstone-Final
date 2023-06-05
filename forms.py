from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField


##WTForm
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title :", validators=[DataRequired()], render_kw={"placeholder": "Blog Title"})
    subtitle = StringField("Subtitle :", validators=[DataRequired()], render_kw={"placeholder": "Blog Subtitle"})
    # author = StringField("Your Name", validators=[DataRequired()])
    img_url = StringField("Blog Image URL :", validators=[DataRequired(), URL()], render_kw={"placeholder": "Url for Image"})

    about = TextAreaField(
        "About Your Blog: ", 
        validators=[DataRequired()],
        render_kw={"placeholder": "Write about your blog in 3 to 4 lines...", "rows":4}
    )
    body = CKEditorField("Blog Content :", validators=[DataRequired()])
    submit = SubmitField("Submit Post")



class CommentForm(FlaskForm):
    comment = TextAreaField(
        " Write Comment : ", 
        validators=[DataRequired()],
        render_kw={"placeholder": "Write Your Comment Here...", "rows":3}
    )
    submit = SubmitField('Comment')



class ReplyForm(FlaskForm):
    reply = TextAreaField(
        "Reply : ", 
        validators=[DataRequired()],
        render_kw={"placeholder": "Your Reply...", "rows":2}
    )
    submit = SubmitField('Reply')