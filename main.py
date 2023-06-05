# Imports

from flask import Flask, render_template, redirect, url_for, flash, abort, request, jsonify
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship

from werkzeug.security import generate_password_hash, check_password_hash
from forms import CreatePostForm, CommentForm, ReplyForm

from mail_sender import SendMail
from functools import wraps
from datetime import date
import random


# admin
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # If id is not 1 then return abort with 403 error
        if current_user.id != 1:
            return abort(403)
        # Otherwise continue with the route function
        return f(*args, **kwargs)
    return decorated_function


# Flask App
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap(app)

# CONNECT TO DB
app.app_context().push()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


gravatar = Gravatar(
    app, size=100, rating='g', default='retro', force_default=False, force_lower=False, use_ssl=False, base_url=None
)


# CONFIGURE DB TABLES
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))

    posts = relationship('BlogPost', back_populates='author')
    comments = relationship("Comment", back_populates="comment_author")
    likes = relationship('Like', back_populates='like_author')
    reply = relationship('Reply', back_populates='reply_author')


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)

    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    author = relationship('User', back_populates='posts')

    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    about = db.Column(db.String(350), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    comments = relationship('Comment', back_populates='parent_post')
    likes = relationship('Like', back_populates='parent_post')
    reply = relationship('Reply', back_populates='parent_post')


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)

    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comments")

    post_id = db.Column(db.Integer, db.ForeignKey('blog_posts.id'))
    parent_post = relationship('BlogPost', back_populates='comments')

    reply = relationship('Reply', back_populates='parent_comment')


class Reply(db.Model):
    __tablename__ = 'replies'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)

    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    reply_author = relationship("User", back_populates="reply")

    post_id = db.Column(db.Integer, db.ForeignKey('blog_posts.id'))
    parent_post = relationship('BlogPost', back_populates='reply')

    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'))
    parent_comment = relationship('Comment', back_populates='reply')


class Like(db.Model):
    __tablename__ = 'likes'
    id = db.Column(db.Integer, primary_key=True)

    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    like_author = relationship('User', back_populates='likes')

    post_id = db.Column(db.Integer, db.ForeignKey('blog_posts.id'))
    parent_post = relationship('BlogPost', back_populates='likes')


db.create_all()



# LOGIN MANAGER
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



# Home Page - DONE
@app.route('/')
def home():

    page = request.args.get('page', 1, type=int)
    posts = BlogPost.query.all()

    main_blogs = BlogPost.query.order_by(
        BlogPost.date.desc()).paginate(page=page, per_page=3)
    
    try:
        mini_posts = random.sample(posts, k=4)
    except:
        mini_posts = posts
    
    try:
        post_lists = random.sample(posts, k=5)
    except:
        post_lists = posts
    
    return render_template(
        'index.html', 
        is_auth=current_user.is_authenticated, 
        main_blogs=main_blogs, 
        mini_blogs=mini_posts, 
        blog_list=post_lists
    )



# Login page - DONE
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        user_email = request.form['userEmail']
        user_password = request.form['userPassword']

        user = User.query.filter_by(email=user_email).first()

        if not user:
            flash('That email does not exists, please try again.')

        elif not check_password_hash(user.password, user_password):
            flash('Password incorrect ! please try again.')

        else:
            login_user(user)
            return redirect(url_for('home'))

    return render_template('login.html')



# Register Page - DONE
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_name = request.form['userName']
        new_user_email = request.form['userEmail']
        # new_user_password = request.form['userPassword']

        if User.query.filter_by(email=new_user_email).first():
            # User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login_or_register'))

        hash_and_salted_password = generate_password_hash(
            password=request.form['userPassword'],
            method='pbkdf2:sha256',
            salt_length=8
        )

        new_user = User(
            email=new_user_email,
            password=hash_and_salted_password,
            name=user_name
        )

        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        return redirect(url_for('home'))

    return render_template('register.html')



# TODO: add replyform when click reply, add replies to comments to page 
# TODO: add edit comment or reply option if can. 
# Single Post View 
@app.route("/post/<int:post_id>", methods=['GET', 'POST'])
def show_post(post_id):

    requested_post = BlogPost.query.get(post_id)
    comment_form = CommentForm()
    # reply_form = ReplyForm()

    if comment_form.validate_on_submit():

        if current_user.is_authenticated == False:
            flash('You need to LogIn or Register to comment.')
            return redirect(url_for('login'))

        new_comment = Comment(
            text=comment_form.comment.data,
            comment_author=current_user,
            parent_post=requested_post
        )

        db.session.add(new_comment)
        db.session.commit()

        return redirect(url_for('show_post', post_id=post_id))

    # if reply_form.validate_on_submit():

    #     if current_user.is_authenticated == False:
    #         flash('You need to LogIn or Register to comment.')
    #         return redirect(url_for('login'))
        

    #     new_reply = Reply(
    #         text=reply_form.reply.data,
    #         reply_author = current_user,
    #         parent_post  = requested_post,
    #         parent_comment =  ''
         
    #     )

    #     db.session.add(new_comment)
    #     db.session.commit()

    return render_template('post.html', blog=requested_post, is_auth=current_user.is_authenticated, form=comment_form)



@app.route("/delete-comment")
@admin_only
def delete_comment():
    comment_id=request.args.get('comment_id')
    current_post_id = request.args.get('post_id')
    comment_to_delete = Comment.query.get(comment_id)
    db.session.delete(comment_to_delete)
    db.session.commit()
    return redirect(url_for('show_post', post_id=current_post_id))



# Add New Post Page - DONE
@app.route("/new-post", methods=['GET', 'POST'])
@admin_only
def new_post():
    create_post_form = CreatePostForm()

    if create_post_form.validate_on_submit():
        new_post = BlogPost(
            title=create_post_form.title.data,
            subtitle=create_post_form.subtitle.data,
            body=create_post_form.body.data,
            img_url=create_post_form.img_url.data,
            about=create_post_form.about.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("home"))

    return render_template('new_post.html', form=create_post_form, is_auth=current_user.is_authenticated)



# Edit Post Page - DONE
@app.route("/edit-post/<int:post_id>", methods=['GET', 'POST'])
@admin_only
def edit_post(post_id):
    # create_post_form = CreatePostForm()
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body,
        about=post.about
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user
        post.about = edit_form.about.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template('new_post.html', form=edit_form, is_edit=True, is_auth=current_user.is_authenticated)



# Like post when click on like - DONE
@app.route('/like-post/<post_id>', methods=['POST'])
@login_required
def like(post_id):
    post = BlogPost.query.get(post_id)
    like = Like.query.filter_by(
        author_id=current_user.id, post_id=post_id).first()

    if not post:
        return jsonify({'error': 'Post does not exist.'}, 400)
    elif like:
        db.session.delete(like)
        db.session.commit()
    else:
        like = Like(author_id=current_user.id, post_id=post_id)
        db.session.add(like)
        db.session.commit()

    return jsonify({"likes": len(post.likes), "liked": current_user.id in map(lambda x: x.author_id, post.likes)})
    # return redirect(url_for('home'))



# TODO: make attractive about page like https://www.yellowleafhammocks.com/pages/about-us
# About Page - DONE
@app.route('/about')
def about():
    return render_template('about.html', is_auth=current_user.is_authenticated)



# Contact Page - DONE
@app.route('/contact', methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        user_data_dict = {
            'Name': request.form['UserName'],
            'Email': request.form['Email'],
            'Phone': request.form['Phone'],
            'Message': request.form['Message'],
        }
        print(user_data_dict)

        SendMail().send_mail(data_dict=user_data_dict)

        return render_template('contact.html', msg_sent=True)

    return render_template('contact.html', msg_sent=False, is_auth=current_user.is_authenticated)



# Delete button in Home Page for admin  - DONE
@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('home'))



# Logout - DONE
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))



# Start App
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
