import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask import make_response
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import datetime
import re
import jwt
import pytz

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['UPLOAD_FOLDER'] = 'uploads/videos'  # Папка для загрузки видео
db = SQLAlchemy(app)

# Вопросы по темам
questions_data = {
    "Основы программирования": [
        {"question": "Что такое переменная?", "options": ["Место для хранения данных", "Тип данных", "Операция"], "answer": "Место для хранения данных"},
        {"question": "Что такое функция?", "options": ["Набор инструкций", "Переменная", "Класс"], "answer": "Набор инструкций"},
        {"question": "Что такое цикл?", "options": ["Повторение блока кода", "Тип данных", "Условие"], "answer": "Повторение блока кода"},
        {"question": "Что такое массив?", "options": ["Структура данных", "Тип данных", "Функция"], "answer": "Структура данных"},
        {"question": "Что такое условный оператор?", "options": ["Оператор для выполнения условий", "Тип данных", "Функция"], "answer": "Оператор для выполнения условий"},
        {"question": "Что такое объект в ООП?", "options": ["Экземпляр класса", "Тип данных", "Переменная"], "answer": "Экземпляр класса"},
        {"question": "Что такое класс?", "options": ["Шаблон для создания объектов", "Тип данных", "Функция"], "answer": "Шаблон для создания объектов"},
        {"question": "Что такое библиотека?", "options": ["Набор функций", "Тип данных", "Переменная"], "answer": "Набор функций"},
        {"question": "Что такое компиляция?", "options": ["Преобразование кода", "Тип данных", "Функция"], "answer": "Преобразование кода"},
        {"question": "Что такое алгоритм?", "options": ["Последовательность шагов", "Тип данных", "Функция"], "answer": "Последовательность шагов"},
    ],

    "Основы дизайна": [
        {"question": "Что такое цветовая палитра?", "options": ["Набор цветов", "Тип шрифта", "Стиль"], "answer": "Набор цветов"},
        {"question": "Что такое компоновка?", "options": ["Расположение элементов", "Тип шрифта", "Цветовая схема"], "answer": "Расположение элементов"},
        {"question": "Что такое шрифт?", "options": ["Стиль текста", "Цвет", "Форма"], "answer": "Стиль текста"},
        {"question": "Что такое контраст?", "options": ["Разница между элементами", "Тип шрифта", "Цветовая палитра"], "answer": "Разница между элементами"},
        {"question": "Что такое визуальная иерархия?", "options": ["Упорядочение элементов", "Тип шрифта", "Цветовая палитра"], "answer": "Упорядочение элементов"},
        {"question": "Что такое отступ?", "options": ["Пространство вокруг элемента", "Тип шрифта", "Цвет"], "answer": "Пространство вокруг элемента"},
        {"question": "Что такое сетка в дизайне?", "options": ["Структура для размещения элементов", "Тип шрифта", "Цветовая палитра"], "answer": "Структура для размещения элементов"},
        {"question": "Что такое баланс в дизайне?", "options": ["Равновесие между элементами", "Тип шрифта", "Цвет"], "answer": "Равновесие между элементами"},
        {"question": "Что такое типографика?", "options": ["Искусство оформления текста", "Тип шрифта", "Цветовая палитра"], "answer": "Искусство оформления текста"},
        {"question": "Что такое брендирование?", "options": ["Создание уникального имиджа", "Тип шрифта", "Цветовая палитра"], "answer": "Создание уникального имиджа"},
    ],

    "Основы JavaScript": [
        {"question": "Что такое JavaScript?", "options": ["Язык программирования", "Тип данных", "Фреймворк"], "answer": "Язык программирования"},
        {"question": "Что такое переменная в JavaScript?", "options": ["Хранилище данных", "Тип данных", "Функция"], "answer": "Хранилище данных"},
        {"question": "Что такое массив в JavaScript?", "options": ["Список данных", "Тип данных", "Функция"], "answer": "Список данных"},
        {"question": "Что такое функция в JavaScript?", "options": ["Набор инструкций", "Тип данных", "Переменная"], "answer": "Набор инструкций"},
        {"question": "Что такое объект в JavaScript?", "options": ["Сложная структура данных", "Тип данных", "Функция"], "answer": "Сложная структура данных"},
        {"question": "Что такое событие в JavaScript?", "options": ["Действие пользователя", "Тип данных", "Функция"], "answer": "Действие пользователя"},
        {"question": "Что такое DOM?", "options": ["Модель объектов документа", "Тип данных", "Функция"], "answer": "Модель объектов документа"},
        {"question": "Что такое AJAX?", "options": ["Технология для асинхронных запросов", "Тип данных", "Функция"], "answer": "Технология для асинхронных запросов"},
        {"question": "Что такое Promise в JavaScript?", "options": ["Объект для обработки асинхронных операций", "Тип данных", "Функция"], "answer": "Объект для обработки асинхронных операций"},
        {"question": "Что такое ES6?", "options": ["Версия JavaScript", "Тип данных", "Функция"], "answer": "Версия JavaScript"},
    ],

    "Основы кибербезопасности": [
        {"question": "Что такое кибербезопасность?", "options": ["Защита компьютерных систем", "Тип данных", "Функция"], "answer": "Защита компьютерных систем"},
        {"question": "Что такое вредоносное ПО?", "options": ["Программное обеспечение для атаки", "Тип данных", "Функция"], "answer": "Программное обеспечение для атаки"},
        {"question": "Что такое фишинг?", "options": ["Метод обмана пользователей", "Тип данных", "Функция"], "answer": "Метод обмана пользователей"},
        {"question": "Что такое брандмауэр?", "options": ["Система защиты сети", "Тип данных", "Функция"], "answer": "Система защиты сети"},
        {"question": "Что такое шифрование?", "options": ["Метод защиты данных", "Тип данных", "Функция"], "answer": "Метод защиты данных"},
        {"question": "Что такое аутентификация?", "options": ["Процесс проверки личности", "Тип данных", "Функция"], "answer": "Процесс проверки личности"},
        {"question": "Что такое DDoS-атака?", "options": ["Атака на доступность", "Тип данных", "Функция"], "answer": "Атака на доступность"},
        {"question": "Что такое VPN?", "options": ["Сеть для защиты данных", "Тип данных", "Функция"], "answer": "Сеть для защиты данных"},
        {"question": "Что такое социальная инженерия?", "options": ["Метод манипуляции людьми", "Тип данных", "Функция"], "answer": "Метод манипуляции людьми"},
        {"question": "Что такое антивирус?", "options": ["Программа для защиты от вирусов", "Тип данных", "Функция"], "answer": "Программа для защиты от вирусов"},
    ],

    "Основы веб-разработки": [
        {"question": "Что такое HTML?", "options": ["Язык разметки", "Язык программирования", "Стиль"], "answer": "Язык разметки"},
        {"question": "Что такое CSS?", "options": ["Язык стилей", "Язык программирования", "Тип данных"], "answer": "Язык стилей"},
        {"question": "Что такое JavaScript в веб-разработке?", "options": ["Язык программирования для интерактивности", "Язык разметки", "Тип данных"], "answer": "Язык программирования для интерактивности"},
        {"question": "Что такое сервер?", "options": ["Компьютер, который обрабатывает запросы", "Тип данных", "Функция"], "answer": "Компьютер, который обрабатывает запросы"},
        {"question": "Что такое клиент?", "options": ["Устройство, отправляющее запросы", "Тип данных", "Функция"], "answer": "Устройство, отправляющее запросы"},
        {"question": "Что такое API?", "options": ["Интерфейс для взаимодействия программ", "Тип данных", "Функция"], "answer": "Интерфейс для взаимодействия программ"},
        {"question": "Что такое HTTP?", "options": ["Протокол передачи данных", "Тип данных", "Функция"], "answer": "Протокол передачи данных"},
        {"question": "Что такое HTTPS?", "options": ["Безопасная версия HTTP", "Тип данных", "Функция"], "answer": "Безопасная версия HTTP"},
        {"question": "Что такое веб-сервер?", "options": ["Система, обрабатывающая веб-запросы", "Тип данных", "Функция"], "answer": "Система, обрабатывающая веб-запросы"},
        {"question": "Что такое база данных?", "options": ["Хранилище данных", "Тип данных", "Функция"], "answer": "Хранилище данных"},
    ],

    "Разработка мобильных приложений": [
        {"question": "Что такое мобильное приложение?", "options": ["Программа для мобильных устройств", "Тип данных", "Язык программирования"], "answer": "Программа для мобильных устройств"},
        {"question": "Что такое кроссплатформенная разработка?", "options": ["Создание приложений для разных платформ", "Тип данных", "Язык программирования"], "answer": "Создание приложений для разных платформ"},
        {"question": "Что такое нативное приложение?", "options": ["Приложение, разработанное для конкретной платформы", "Тип данных", "Язык программирования"], "answer": "Приложение, разработанное для конкретной платформы"},
        {"question": "Что такое API?", "options": ["Интерфейс для взаимодействия между программами", "Тип данных", "Язык программирования"], "answer": "Интерфейс для взаимодействия между программами"},
        {"question": "Что такое UX/UI дизайн?", "options": ["Процесс проектирования пользовательского опыта и интерфейса", "Тип данных", "Язык программирования"], "answer": "Процесс проектирования пользовательского опыта и интерфейса"},
        {"question": "Что такое фреймворк?", "options": ["Набор инструментов для разработки приложений", "Тип данных", "Язык программирования"], "answer": "Набор инструментов для разработки приложений"},
        {"question": "Что такое тестирование приложений?", "options": ["Процесс проверки работоспособности приложения", "Тип данных", "Язык программирования"], "answer": "Процесс проверки работоспособности приложения"},
        {"question": "Что такое отзывчивый дизайн?", "options": ["Дизайн, адаптирующийся к размеру экрана", "Тип данных", "Язык программирования"], "answer": "Дизайн, адаптирующийся к размеру экрана"},
        {"question": "Что такое MVP?", "options": ["Минимально жизнеспособный продукт", "Тип данных", "Язык программирования"], "answer": "Минимально жизнеспособный продукт"},
        {"question": "Что такое публикация приложения?", "options": ["Процесс размещения приложения в магазине приложений", "Тип данных", "Язык программирования"], "answer": "Процесс размещения приложения в магазине приложений"},
    ],

    "UX/UI дизайн": [
        {"question": "Что такое UX-дизайн?", "options": ["Проектирование пользовательского опыта", "Тип данных", "Язык программирования"], "answer": "Проектирование пользовательского опыта"},
        {"question": "Что такое UI-дизайн?", "options": ["Проектирование пользовательского интерфейса", "Тип данных", "Язык программирования"], "answer": "Проектирование пользовательского интерфейса"},
        {"question": "Что такое прототипирование?", "options": ["Создание предварительной версии продукта", "Тип данных", "Язык программирования"], "answer": "Создание предварительной версии продукта"},
        {"question": "Что такое пользовательские тесты?", "options": ["Тестирование дизайна на реальных пользователях", "Тип данных", "Язык программирования"], "answer": "Тестирование дизайна на реальных пользователях"},
        {"question": "Что такое wireframe?", "options": ["Схематическое представление интерфейса", "Тип данных", "Язык программирования"], "answer": "Схематическое представление интерфейса"},
        {"question": "Что такое дизайн-система?", "options": ["Набор стандартов и компонентов для дизайна", "Тип данных", "Язык программирования"], "answer": "Набор стандартов и компонентов для дизайна"},
        {"question": "Что такое юзабилити?", "options": ["Удобство использования продукта", "Тип данных", "Язык программирования"], "answer": "Удобство использования продукта"},
        {"question": "Что такое визуальная иерархия?", "options": ["Организация элементов интерфейса по важности", "Тип данных", "Язык программирования"], "answer": "Организация элементов интерфейса по важности"},
        {"question": "Что такое цветовая палитра?", "options": ["Набор цветов, используемых в дизайне", "Тип данных", "Язык программирования"], "answer": "Набор цветов, используемых в дизайне"},
        {"question": "Что такое типографика?", "options": ["Искусство оформления текста", "Тип данных", "Язык программирования"], "answer": "Искусство оформления текста"},
    ],

    "Основы цифрового маркетинга": [
        {"question": "Что такое целевая аудитория?", "options": ["Группа людей, на которую направлен продукт", "Тип данных", "Язык программирования"], "answer": "Группа людей, на которую направлен продукт"},
        {"question": "Что такое SEO?", "options": ["Оптимизация для поисковых систем", "Тип данных", "Язык программирования"], "answer": "Оптимизация для поисковых систем"},
        {"question": "Что такое контент-маркетинг?", "options": ["Создание и распространение ценного контента", "Тип данных", "Язык программирования"], "answer": "Создание и распространение ценного контента"},
        {"question": "Что такое SMM?", "options": ["Маркетинг в социальных сетях", "Тип данных", "Язык программирования"], "answer": "Маркетинг в социальных сетях"},
        {"question": "Что такое PPC?", "options": ["Оплата за клик", "Тип данных", "Язык программирования"], "answer": "Оплата за клик"},
        {"question": "Что такое email-маркетинг?", "options": ["Рассылка рекламных писем по электронной почте", "Тип данных", "Язык программирования"], "answer": "Рассылка рекламных писем по электронной почте"},
        {"question": "Что такое брендинг?", "options": ["Создание уникального имиджа компании", "Тип данных", "Язык программирования"], "answer": "Создание уникального имиджа компании"},
        {"question": "Что такое аналитика?", "options": ["Сбор и анализ данных о поведении пользователей", "Тип данных", "Язык программирования"], "answer": "Сбор и анализ данных о поведении пользователей"},
        {"question": "Что такое воронка продаж?", "options": ["Модель, описывающая путь клиента к покупке", "Тип данных", "Язык программирования"], "answer": "Модель, описывающая путь клиента к покупке"},
        {"question": "Что такое уникальное торговое предложение (УТП)?", "options": ["Отличительная особенность, выделяющая продукт", "Тип данных", "Язык программирования"], "answer": "Отличительная особенность, выделяющая продукт"},
    ],

    "Основы работы с базами данных": [
        {"question": "Что такое реляционная база данных?", "options": ["База данных, основанная на таблицах", "Тип данных", "Функция"], "answer": "База данных, основанная на таблицах"},
        {"question": "Что такое SQL?", "options": ["Язык для работы с базами данных", "Язык программирования", "Тип данных"], "answer": "Язык для работы с базами данных"},
        {"question": "Что такое первичный ключ?", "options": ["Уникальный идентификатор записи", "Тип данных", "Функция"], "answer": "Уникальный идентификатор записи"},
        {"question": "Что такое индекс в базе данных?", "options": ["Структура для ускорения поиска", "Тип данных", "Функция"], "answer": "Структура для ускорения поиска"},
        {"question": "Что такое нормализация?", "options": ["Процесс оптимизации структуры базы данных", "Тип данных", "Функция"], "answer": "Процесс оптимизации структуры базы данных"},
        {"question": "Что такое транзакция?", "options": ["Набор операций, выполняемых как единое целое", "Тип данных", "Функция"], "answer": "Набор операций, выполняемых как единое целое"},
        {"question": "Что такое NoSQL?", "options": ["Нереляционная база данных", "Тип данных", "Функция"], "answer": "Нереляционная база данных"},
        {"question": "Что такое CRUD?", "options": ["Основные операции с данными: Создать, Читать, Обновить, Удалить", "Тип данных", "Функция"], "answer": "Основные операции с данными: Создать, Читать, Обновить, Удалить"},
        {"question": "Что такое внешние ключи?", "options": ["Связь между таблицами", "Тип данных", "Функция"], "answer": "Связь между таблицами"},
        {"question": "Что такое хранимая процедура?", "options": ["Набор SQL-команд, хранящихся в базе данных", "Тип данных", "Функция"], "answer": "Набор SQL-команд, хранящихся в базе данных"},
    ],

    "Машинное обучение": [
        {"question": "Что такое машинное обучение?", "options": ["Метод, позволяющий компьютерам обучаться на данных", "Тип данных", "Функция"], "answer": "Метод, позволяющий компьютерам обучаться на данных"},
        {"question": "Что такое обучающая выборка?", "options": ["Набор данных для обучения модели", "Тип данных", "Функция"], "answer": "Набор данных для обучения модели"},
        {"question": "Что такое переобучение?", "options": ["Когда модель слишком точно подстраивается под обучающую выборку", "Тип данных", "Функция"], "answer": "Когда модель слишком точно подстраивается под обучающую выборку"},
        {"question": "Что такое алгоритм?", "options": ["Набор правил для решения задачи", "Тип данных", "Функция"], "answer": "Набор правил для решения задачи"},
        {"question": "Что такое нейронная сеть?", "options": ["Модель, имитирующая работу человеческого мозга", "Тип данных", "Функция"], "answer": "Модель, имитирующая работу человеческого мозга"},
        {"question": "Что такое регрессия?", "options": ["Метод предсказания числовых значений", "Тип данных", "Функция"], "answer": "Метод предсказания числовых значений"},
        {"question": "Что такое классификация?", "options": ["Метод, позволяющий разделять данные на категории", "Тип данных", "Функция"], "answer": "Метод, позволяющий разделять данные на категории"},
        {"question": "Что такое алгоритм K-средних?", "options": ["Алгоритм кластеризации", "Тип данных", "Функция"], "answer": "Алгоритм кластеризации"},
        {"question": "Что такое обучение с учителем?", "options": ["Метод, где модель обучается на размеченных данных", "Тип данных", "Функция"], "answer": "Метод, где модель обучается на размеченных данных"},
        {"question": "Что такое обучение без учителя?", "options": ["Метод, где модель обучается на неразмеченных данных", "Тип данных", "Функция"], "answer": "Метод, где модель обучается на неразмеченных данных"},
    ],

    "Основы графического дизайна": [
        {"question": "Что такое графический дизайн?", "options": ["Процесс создания визуального контента", "Тип данных", "Функция"], "answer": "Процесс создания визуального контента"},
        {"question": "Что такое цветовая палитра?", "options": ["Набор цветов, используемых в дизайне", "Тип данных", "Функция"], "answer": "Набор цветов, используемых в дизайне"},
        {"question": "Что такое компоновка?", "options": ["Расположение элементов на странице", "Тип данных", "Функция"], "answer": "Расположение элементов на странице"},
        {"question": "Что такое типографика?", "options": ["Искусство оформления текста", "Тип данных", "Функция"], "answer": "Искусство оформления текста"},
        {"question": "Что такое векторная графика?", "options": ["Графика, основанная на математических формулах", "Тип данных", "Функция"], "answer": "Графика, основанная на математических формулах"},
        {"question": "Что такое растровая графика?", "options": ["Графика, состоящая из пикселей", "Тип данных", "Функция"], "answer": "Графика, состоящая из пикселей"},
        {"question": "Что такое макет?", "options": ["Предварительный план дизайна", "Тип данных", "Функция"], "answer": "Предварительный план дизайна"},
        {"question": "Что такое брендирование?", "options": ["Создание уникального имиджа для компании", "Тип данных", "Функция"], "answer": "Создание уникального имиджа для компании"},
        {"question": "Что такое визуальная иерархия?", "options": ["Способ организации элементов по важности", "Тип данных", "Функция"], "answer": "Способ организации элементов по важности"},
        {"question": "Что такое дизайн-мышление?", "options": ["Методология решения проблем с фокусом на пользователе", "Тип данных", "Функция"], "answer": "Методология решения проблем с фокусом на пользователе"},
    ],

    "Основы DevOps": [
        {"question": "Что такое мониторинг в DevOps?", "options": ["Отслеживание состояния систем и приложений", "Тип данных", "Функция"], "answer": "Отслеживание состояния систем и приложений"},
        {"question": "Что такое инфраструктура как код (IaC)?", "options": ["Подход к управлению инфраструктурой с помощью кода", "Тип данных", "Функция"], "answer": "Подход к управлению инфраструктурой с помощью кода"},
        {"question": "Что такое автоматизация в DevOps?", "options": ["Процесс упрощения задач с помощью инструментов", "Тип данных", "Функция"], "answer": "Процесс упрощения задач с помощью инструментов"},
        {"question": "Что такое Agile?", "options": ["Методология гибкой разработки", "Тип данных", "Функция"], "answer": "Методология гибкой разработки"},
        {"question": "Что такое управление версиями?", "options": ["Система отслеживания изменений в коде", "Тип данных", "Функция"], "answer": "Система отслеживания изменений в коде"},
        {"question": "Что такое DevSecOps?", "options": ["Интеграция безопасности в DevOps", "Тип данных", "Функция"], "answer": "Интеграция безопасности в DevOps"},
        {"question": "Что такое виртуализация?", "options": ["Создание виртуальных версий физических ресурсов", "Тип данных", "Функция"], "answer": "Создание виртуальных версий физических ресурсов"},
        {"question": "Что такое микросервисы?", "options": ["Архитектурный стиль, основанный на разбиении приложений на небольшие сервисы", "Тип данных", "Функция"], "answer": "Архитектурный стиль, основанный на разбиении приложений на небольшие сервисы"},
        {"question": "Что такое DevOps инструменты?", "options": ["Программное обеспечение для поддержки DevOps практик", "Тип данных", "Функция"], "answer": "Программное обеспечение для поддержки DevOps практик"},
        {"question": "Что такое тестирование в DevOps?", "options": ["Процесс проверки и валидации кода на всех этапах разработки", "Тип данных", "Функция"], "answer": "Процесс проверки и валидации кода на всех этапах разработки"},
    ],

}

@app.route('/test')
def test():
    return render_template('test.html', questions_data=questions_data, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

ROLE_TRANSLATIONS = {
    'student': 'Студент',
    'teacher': 'Преподаватель',
    'admin': 'Администратор',
}

# Создаем папку для загрузки видео, если она не существует
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Модель пользователя
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False) 

# Модель видео
class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    duration = db.Column(db.String(10), nullable=False)
    author = db.Column(db.String(80), nullable=False)
    course = db.Column(db.String(100), nullable=False)
    filename = db.Column(db.String(150), nullable=False)

# Модель для хранения результатов тестов
class TestResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    course = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

@app.before_request
def create_tables():
    db.create_all()

# Декоратор для проверки роли
def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'username' not in session or session.get('role') != role:
                flash('У вас нет прав для доступа к этой странице.', 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/')
def index():
    username = session.get('username') or request.cookies.get('username', 'Гость')
    role = session.get('role') or request.cookies.get('role', 'Пользователь')
    if not username or not role:
        # Логика для обработки отсутствия данных
        print("Cookies не найдены, используем значения по умолчанию.")
    return render_template('index.html', username=username, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/images/<path:filename>')
def images(filename):
    return send_from_directory('images', filename)

def get_user_from_db(login):
    # Проверяем, является ли ввод email
    if re.match(r"[^@]+@[^@]+\.[^@]+", login):
        return User.query.filter_by(email=login).first()
    else:
        return User.query.filter_by(username=login).first()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        
        user = get_user_from_db(login)

        if user and check_password_hash(user.password, password):
            session['username'] = user.username
            session['role'] = user.role

            # Сохранение в cookies
            response = make_response(redirect(url_for('index')))
            response.set_cookie('username', user.username)
            response.set_cookie('role', user.role)
            return response
            
        else:
            flash('Неверный email или пароль', 'error')
    
    return render_template('login.html', ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/register', methods=['GET', 'POST'])
@role_required('admin')  # Добавляем проверку роли
def register():
    if request.method == 'POST':
        username = request.form['username']
        login = request.form['login']  # Это email
        password = request.form['password']
        password_confirm = request.form['password_confirm']
        role = request.form['role']

        # Проверка на пустые поля
        if not username:
            flash('Имя пользователя не может быть пустым.', 'error')
            return redirect(url_for('register'))

        if not login or not re.match(r"[^@]+@[^@]+\.[^@]+", login):
            flash('Введите корректный email.', 'error')
            return redirect(url_for('register'))

        if not password or not password_confirm:
            flash('Пароль и подтверждение пароля обязательны.', 'error')
            return redirect(url_for('register'))

        if password != password_confirm:
            flash('Пароли не совпадают. Пожалуйста, попробуйте снова.', 'error')
            return redirect(url_for('register'))

        existing_user = User.query.filter((User .email == login) | (User .username == username)).first()
        if existing_user:
            flash('Пользователь с указанным email или именем пользователя уже существует. Пожалуйста, используйте другой.', 'error')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)

        # Создаем нового пользователя с выбранной ролью
        new_user = User(username=username, email=login, password=hashed_password, role=role)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Регистрация прошла успешно!', 'success')
            return redirect(url_for('index'))  # Перенаправление на главную страницу
        except Exception as e:
            db.session.rollback()  # Откат транзакции в случае ошибки
            print(f'Ошибка при регистрации: {e}')  # Вывод ошибки в консоль
            flash('Произошла ошибка при регистрации. Пожалуйста, попробуйте позже.', 'error')
            return redirect(url_for('register'))

    return render_template('register.html', ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)


def generate_reset_token(email):
    token = jwt.encode({'reset_password': email, 'exp':
    datetime.datetime.utcnow() + datetime.timedelta(hours=1)}, app.config['SECRET_KEY'], algorithm='HS256')
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
            flash('Инструкции по сбросу пароля отправлены на ваш email.', 'info')
        else:
            flash('Если такой email существует в нашей базе, вы получите инструкции по сбросу пароля.', 'info')
        
        return redirect(url_for('login'))
    
    return render_template('reset-password-request.html', ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

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

@app.route('/change-password', methods=['GET', 'POST'])
def change_password():
    # Проверка авторизации пользователя
    if 'username' not in session:
        return redirect(url_for('login'))  # Перенаправление на страницу входа, если не авторизован

    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        user = User.query.filter_by(username=session.get('username')).first()

        if user and check_password_hash(user.password, current_password):
            if new_password == confirm_password:
                user.password = generate_password_hash(new_password)
                db.session.commit()
                flash('Пароль успешно изменен!', 'success')
                return redirect(url_for('index'))  # Возврат после успешного изменения пароля
            else:
                flash('Новые пароли не совпадают.', 'error')
        else:
            flash('Неверный текущий пароль.', 'error')

    # Возврат шаблона для GET-запроса или после неудачи в POST
    return render_template('change-password.html', ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    
    # Удаление cookies
    response = make_response(redirect(url_for('index')))
    response.set_cookie('username', '', expires=0)
    response.set_cookie('role', '', expires=0)
    
    flash('Вы вышли из системы.', 'info')
    return response

@app.route('/add_video', methods=['GET', 'POST'])
@role_required('teacher')
def add_video():
    if request.method == 'POST':
        video_title = request.form['title']
        video_description = request.form['description']
        video_duration = request.form['duration']
        video_author = request.form['author']
        video_course = request.form['course']
        video_file = request.files.get('video_file')

        # Проверка, что файл был загружен и имеет допустимый формат
        if video_file and allowed_file(video_file.filename):
            filename = secure_filename(video_file.filename)
            video_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # Сохраняем информацию о видео в базе данных
            new_video = Video(title=video_title, description=video_description,
                              duration=video_duration, author=video_author,
                              course=video_course, filename=filename)
            db.session.add(new_video)
            db.session.commit()

            flash('Видео успешно добавлено!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Пожалуйста, загрузите корректный видеофайл.', 'error')

    return render_template('add_video.html', current_user=session, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

def allowed_file(filename):
    allowed_extensions = {'mp4', 'avi', 'mov', 'mkv'}  # Добавьте нужные форматы
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@app.route('/submit_test', methods=['POST'])
def submit_test():
    data = request.get_json()
    username = data.get('username')
    course = data.get('course')
    score = data.get('score')

    # Установка времени в московском часовом поясе
    moscow_tz = pytz.timezone('Europe/Moscow')
    timestamp = datetime.datetime.now(moscow_tz)  # Получаем текущее московское время

    try:
        # Сохранение результата в базе данных
        new_result = TestResult(username=username, course=course, score=score, timestamp=timestamp)
        db.session.add(new_result)
        db.session.commit()
        return jsonify({"result_id": new_result.id}), 200  # Возвращаем ответ в формате JSON
    except Exception as e:
        db.session.rollback()  # Откат транзакции в случае ошибки
        print(f'Ошибка при сохранении результата: {e}')  # Вывод ошибки в консоль
        return jsonify({"error": "Не удалось сохранить результат."}), 500

@app.route('/student_result/<int:result_id>')
def show_student_result(result_id):
    result = TestResult.query.get(result_id)
    if result:
        total_questions = len(questions_data[result.course])  # Получаем общее количество вопросов для курса
        return render_template('student_result.html', result=result, total_questions=total_questions, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)
    else:
        flash('Результат не найден.', 'error')
        return redirect(url_for('index'))  # Или на другую страницу

@app.route('/results')
@role_required('teacher')  # Проверка роли
def results():
    results = TestResult.query.all()  # Извлечение всех результатов из базы данных
    return render_template('results.html', results=results, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/delete_result/<int:result_id>', methods=['POST'])
@role_required('teacher')  # Проверка роли
def delete_result(result_id):
    result = TestResult.query.get(result_id)
    if result:
        db.session.delete(result)
        db.session.commit()
        flash('Результат успешно удален!', 'success')
    else:
        flash('Результат не найден.', 'error')
    return redirect(url_for('results'))

@app.route('/course/programming')
def course_programming():
    if 'username' not in session:
        flash('Вы должны быть авторизованы для просмотра видео.', 'error')
        return redirect(url_for('login'))  # Перенаправляем на страницу входа
    course_title = "Основы программирования"
    return render_template('course-programming.html', page_title=course_title, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/course/web-development')
def course_web_development():
    if 'username' not in session:
        flash('Вы должны быть авторизованы для просмотра видео.', 'error')
        return redirect(url_for('login'))
    course_title = "Веб-разработка"
    return render_template('course-web-development.html', page_title=course_title, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/course/design')
def course_design():
    if 'username' not in session:
        flash('Вы должны быть авторизованы для просмотра видео.', 'error')
        return redirect(url_for('login'))
    course_title = "Основы дизайна"
    return render_template('course-design.html', page_title=course_title, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/course/javascript')
def course_javascript():
    if 'username' not in session:
        flash('Вы должны быть авторизованы для просмотра видео.', 'error')
        return redirect(url_for('login'))
    course_title = "Основы JavaScript"
    return render_template('course-javascript.html', page_title=course_title, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/course/machine-learning')
def course_machine_learning():
    if 'username' not in session:
        flash('Вы должны быть авторизованы для просмотра видео.', 'error')
        return redirect(url_for('login'))
    course_title = "Введение в машинное обучение"
    return render_template('course-machine-learning.html', page_title=course_title, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/course/mobile-development')
def course_mobile_development():
    if 'username' not in session:
        flash('Вы должны быть авторизованы для просмотра видео.', 'error')
        return redirect(url_for('login'))
    course_title = "Разработка мобильных приложений"
    return render_template('course-mobile-development.html', page_title=course_title, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/course/cybersecurity')
def course_cybersecurity():
    if 'username' not in session:
        flash('Вы должны быть авторизованы для просмотра видео.', 'error')
        return redirect(url_for('login'))
    course_title = "Основы кибербезопасности"
    return render_template('course-cybersecurity.html', page_title=course_title, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/course/database')
def course_database():
    if 'username' not in session:
        flash('Вы должны быть авторизованы для просмотра видео.', 'error')
        return redirect(url_for('login'))
    course_title = "Работа с базами данных"
    return render_template('course-database.html', page_title=course_title, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/course/ux-ui-design')
def course_ux_ui_design():
    if 'username' not in session:
        flash('Вы должны быть авторизованы для просмотра видео.', 'error')
        return redirect(url_for('login'))
    course_title = "UX/UI дизайн"
    return render_template('course-ux-ui-design.html', page_title=course_title, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/course/devops')
def course_devops():
    if 'username' not in session:
        flash('Вы должны быть авторизованы для просмотра видео.', 'error')
        return redirect(url_for('login'))
    course_title = "Основы DevOps"
    return render_template('course-devops.html', page_title=course_title, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/course/graphic-design')
def course_graphic_design():
    if 'username' not in session:
        flash('Вы должны быть авторизованы для просмотра видео.', 'error')
        return redirect(url_for('login'))
    course_title = "Основы графического дизайна"
    return render_template('course-graphic-design.html', page_title=course_title, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/course/digital-marketing')
def course_digital_marketing():
    if 'username' not in session:
        flash('Вы должны быть авторизованы для просмотра видео.', 'error')
        return redirect(url_for('login'))
    course_title = "Основы цифрового маркетинга"
    return render_template('course-digital-marketing.html', page_title=course_title, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

if __name__ == '__main__':
    app.run(debug=True)