from flask import Flask, render_template, request, url_for, current_app, send_from_directory, redirect, flash
import os
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_required, login_user, current_user, logout_user
import layoutXLM
import pytesseract
from PIL import Image
from werkzeug.security import generate_password_hash,  check_password_hash
from wtforms import StringField, SubmitField, TextAreaField,  BooleanField, PasswordField
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError


pytesseract.pytesseract.tesseract_cmd = r'D:\диплом\сайт_для_диплома\tesseract-ocr\tesseract.exe'
layout_model = layoutXLM.initialize_model()
layout_processor = layoutXLM.initialize_processor()

UPLOAD_FOLDER = 'down'
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = '1337'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1337@localhost/flask_app_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = '/login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.query(Users).get(user_id)

class LoginForm(FlaskForm):
    username = StringField("Логин", validators=[DataRequired()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    remember = BooleanField("Запомни меня")
    submit = SubmitField('Войти')

class RegistrationForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password2 = PasswordField(
        'Повторите пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')
    def validate_username(self, username):
        user = Users.query.filter_by(login=username.data).first()
        if user is not None:
            raise ValidationError('Данный логин уже занят')
        
class InformationForm(FlaskForm):
    FIO = StringField("ФИО", validators=[DataRequired()])
    phone = StringField("номер телефона", validators=[DataRequired()])
    post = StringField("должность", validators=[DataRequired()])
    submit = SubmitField('Обновить информацию')
    


class Users(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer(), primary_key=True)
    login = db.Column(db.Text())
    password_hash = db.Column(db.Text())
    FIO = db.Column(db.Text())
    phone = db.Column(db.Text())
    post = db.Column(db.Text())

    def __repr__(self):
        return '<User %r>' % (self.nickname)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self,  password):
        return check_password_hash(self.password_hash, password)


@app.route("/", methods=['GET', 'POST'])
@login_required
def index():
    if request.method == "GET":
        return render_template("index.html", current_user = current_user)
    else:
        file = request.files["file_send"]
        
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], "img1.png"))
        im = Image.open('D:\диплом\сайт_для_диплома\down\img1.png')
        layoutXLM.work_with_im(im, layout_processor, layout_model, 0, current_user.FIO, current_user.phone, current_user.post)
        return redirect("/two")

@app.route("/two", methods=['GET', 'POST'])
def two():
    if request.method == "GET":
        return render_template("result.html", current_user = current_user)
    else:
        file = request.files["file_send"]
        
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], "img1.png"))
        im = Image.open('D:\диплом\сайт_для_диплома\down\img1.png')
        layoutXLM.work_with_im(im, layout_processor, layout_model, 1, current_user.FIO, current_user.phone, current_user.post)
        return render_template("result.html")

@app.route('/download/<path:filename>', methods=['GET', 'POST'])
def download(filename):
    uploads = os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER'])
    return send_from_directory(directory=uploads, path = filename)

@app.route('/login/', methods=['post',  'get'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.query(Users).filter(Users.login == form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect('/')

        flash("Неправильный логин/пароль", 'error')
        return redirect(url_for('login'))
    return render_template('login.html', form=form, current_user = current_user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect('/index')
    form = RegistrationForm()
    if form.validate_on_submit():
        user = Users(login=form.username.data, password_hash=generate_password_hash(form.password.data))
        db.session.add(user)
        db.session.commit()
        flash('Регистрация прошла успешно')
        return redirect(url_for('login'))
    return render_template('register.html', form=form, current_user = current_user)

@app.route('/info', methods=['GET', 'POST'])
@login_required
def info():
    form = InformationForm()
    if form.validate_on_submit():
        current_user.FIO = form.FIO.data
        current_user.phone = form.phone.data
        current_user.post = form.post.data
        db.session.add(current_user)
        db.session.commit()
        flash('Данные успешно обновленны')
        return redirect('/')
    return render_template('info.html', form=form, current_user = current_user)

@app.route('/logout/')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True, port=80)