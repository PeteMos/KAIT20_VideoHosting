from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

@app.before_request
def create_tables():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['username'] = user.username
            return redirect(url_for('index'))
        else:
            flash('Неправильное имя пользователя или пароль!')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        password_confirm = request.form['password_confirm']

        if password != password_confirm:
            flash('Пароли не совпадают!')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='sha256')
        new_user = User(username=username, email=email, password=hashed_password)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Регистрация прошла успешно!')
            return redirect(url_for('login'))
        except:
            flash('Имя пользователя или email уже заняты!')
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/course/programming')
def course_programming():
    return render_template('course-programming.html')

@app.route('/course/web-development')
def course_web_development():
    return render_template('course-web-development.html')

@app.route('/course/design')
def course_design():
    return render_template('course-design.html')

@app.route('/course/javascript')
def course_javascript():
    return render_template('course-javascript.html')

@app.route('/course/machine-learning')
def course_machine_learning():
    return render_template('course-machine-learning.html')

@app.route('/course/mobile-development')
def course_mobile_development():
    return render_template('course-mobile-development.html')

@app.route('/course/cybersecurity')
def course_cybersecurity():
    return render_template('course-cybersecurity.html')

@app.route('/course/database')
def course_database():
    return render_template('course-database.html')

@app.route('/course/ux-ui-design')
def course_ux_ui_design():
    return render_template('course-ux-ui-design.html')

@app.route('/course/devops')
def course_devops():
    return render_template('course-devops.html')

@app.route('/course/graphic-design')
def course_graphic_design():
    return render_template('course-graphic-design.html')

@app.route('/course/digital-marketing')
def course_digital_marketing():
    return render_template('course-digital-marketing.html')

if __name__ == '__main__':
    app.run(debug=True)
