// Функция для прокрутки к верху страницы
function scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Отображение/скрытие кнопки "Вернуться наверх"
window.onscroll = function() {
    const button = document.querySelector('.back-to-top');
    if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
        button.style.display = "block"; // Показываем кнопку
    } else {
        button.style.display = "none"; // Скрываем кнопку
    }
};

// Обработчик события на кнопку
document.querySelector('.back-to-top').addEventListener('click', scrollToTop);

const currentYear = new Date().getFullYear();
document.getElementById('currentYear').textContent = currentYear;