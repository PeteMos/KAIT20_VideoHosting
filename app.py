from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import re
import jwt
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

@app.before_request
def create_tables():
    db.create_all()

@app.route('/')
def index():
    full_name = session.get('username')
    return render_template('index.html', username=full_name)

@app.route('/images/<path:filename>')
def images(filename):
    return send_from_directory('images', filename)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        
        # Проверяем, является ли ввод email
        if re.match(r"[^@]+@[^@]+\.[^@]+", login):
            user = User.query.filter_by(email=login).first()
        else:
            user = User.query.filter_by(username=login).first()

        # Проверяем, существует ли пользователь и правильный ли пароль
        if user and check_password_hash(user.password, password):
            session['username'] = user.username 
            flash('Вы успешно вошли в систему.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверный email или пароль', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']  # Получаем username из формы
        login = request.form['login']
        password = request.form['password']
        password_confirm = request.form['password_confirm']

        if not username:  # Проверяем, что username не пустой
            flash('Имя пользователя не может быть пустым.')
            return redirect(url_for('register'))

        if password != password_confirm:
            flash('Пароли не совпадают. Пожалуйста, попробуйте снова.')
            return redirect(url_for('register'))

        existing_user = User.query.filter((User .email == login) | (User .username == username)).first()
        if existing_user:
            flash('Пользователь с указанным email или именем пользователя уже существует. Пожалуйста, используйте другой.')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)

        # Создаем нового пользователя без поля full_name
        new_user = User(username=username, email=login, password=hashed_password)

        try:
            db.session.add(new_user)
            db.session.commit()
            session['username'] = new_user.username  # Сохраняем имя пользователя в сессии
            flash('Регистрация прошла успешно! Вы успешно вошли в систему.')
            return redirect(url_for('index'))  # Перенаправление на главную страницу
        except Exception as e:
            db.session.rollback()  # Откат транзакции в случае ошибки
            print(f'Ошибка при регистрации: {e}')  # Вывод ошибки в консоль
            flash(f'Произошла ошибка при регистрации: {e}. Пожалуйста, попробуйте позже.')
            return redirect(url_for('register'))

    return render_template('register.html')

def generate_reset_token(email):
    token = jwt.encode({'reset_password': email, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)}, app.config['SECRET_KEY'], algorithm='HS256')
    return token

def verify_reset_token(token):
    try:
                email = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    return email

@app.route('/reset-password-request', methods=['GET', 'POST'])
def reset_password_request():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            token = generate_reset_token(user.email)
            # Здесь можно добавить код для отправки email с токеном
            # Например, с использованием Flask-Mail
            flash('Инструкции по сбросу пароля отправлены на ваш email.', 'info')
        else:
            flash('Если такой email существует в нашей базе, вы получите инструкции по сбросу пароля.', 'info')
        
        return redirect(url_for('login'))
    
    return render_template('reset-password-request.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = verify_reset_token(token)
    if email is None:
        flash('Недействительный или истекший токен', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash('Пароли не совпадают. Пожалуйста, попробуйте снова.', 'error')
            return redirect(url_for('reset_password', token=token))

        user = User.query.filter_by(email=email).first()
        if user:
            user.password = generate_password_hash(new_password)
            db.session.commit()
            flash('Пароль успешно сброшен!', 'success')
            return redirect(url_for('login'))
        else:
            flash('Пользователь не найден.', 'error')
            return redirect(url_for('login'))

    return render_template('reset-password.html', token=token)

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Вы вышли из системы.', 'info')
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

