from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False) 
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

@app.before_request
def create_tables():
    db.create_all()

@app.route('/')
def index():
    full_name = session.get('username')  # Получаем имя пользователя из сессии
    return render_template('index.html', username=full_name)  # Передаем имя пользователя в шаблон

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form['login']  # Получаем значение из поля 'login'
        password = request.form['password']
        
        # Проверяем, является ли ввод email или номером телефона
        if re.match(r"[^@]+@[^@]+\.[^@]+", login):  # Это email
            user = User.query.filter_by(email=login).first()
        else:  # Это телефон
            user = User.query.filter_by(username=login).first()

        if user and check_password_hash(user.password, password):  # Проверяем пароль
            session['username'] = user.full_name  # Сохраняем имя пользователя в сессии
            flash('Вы успешно вошли в систему.', 'success')  # Сообщение об успешном входе
            return redirect(url_for('index'))  # Перенаправляем на главную страницу
        else:
            flash('Неверный email или пароль', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name']  # Получаем полное имя
        login = request.form['login']
        password = request.form['password']
        password_confirm = request.form['password_confirm']

        # Проверка на наличие имени и фамилии
        if not re.match(r'^\S+\s+\S+$', full_name):
            flash('Полное имя должно содержать как минимум имя и фамилию.')
            return redirect(url_for('register'))

        if password != password_confirm:
            flash('Пароли не совпадают. Пожалуйста, попробуйте снова.')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)  # Хэшируем пароль

        # Проверяем, является ли ввод email или номером телефона
        if re.match(r"[^@]+@[^@]+\.[^@]+", login):  # Это email
            existing_user = User.query.filter_by(email=login).first()
        else:  # Это телефон
            existing_user = User.query.filter_by(username=login).first()

        if existing_user:
            flash('Пользователь с указанным email или номером телефона уже существует. Пожалуйста, используйте другой.')
            return redirect(url_for('register'))

        new_user = User(full_name=full_name, username=login, email=login if re.match(r"[^@]+@[^@]+\.[^@]+", login) else None, password=hashed_password)

        try:
            db.session.add(new_user)
            db.session.commit()
            session['username'] = new_user.full_name  # Сохраняем полное имя пользователя в сессии
            flash('Регистрация прошла успешно! Вы успешно вошли в систему.')  # Сообщение об успешной регистрации
            return redirect(url_for('index'))  # Перенаправляем на главную страницу
        except Exception as e:
            flash('Произошла ошибка при регистрации. Пожалуйста, попробуйте позже.')
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password_request():
    if request.method == 'POST':
        email = request.form['email']
        # Здесь можно добавить логику для сброса пароля
        flash('Инструкции по сбросу пароля отправлены на ваш email.', 'info')
        return redirect(url_for('login'))
    return render_template('reset-password.html')

@app.route('/logout')
def logout():
    session.pop('username', None)  # Удаляем имя пользователя из сессии
    flash('Вы вышли из системы.', 'info')  # Сообщение об успешном выходе
    return redirect(url_for('index'))

# Остальные маршруты для курсов...
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
