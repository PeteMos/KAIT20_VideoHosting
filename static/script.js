let currentUsername = localStorage.getItem("username") || "Гость";
let likeCount = 0;
let dislikeCount = 0;
let userVote = null; 

    function togglePassword(passwordFieldId) {
        const passwordField = document.getElementById(passwordFieldId);
        const eyeIcon = passwordField.nextElementSibling.querySelector("i");

        if (passwordField.type === "password") {
            passwordField.type = "text";
            eyeIcon.classList.remove("fa-eye");
            eyeIcon.classList.add("fa-eye-slash");
        } else {
            passwordField.type = "password";
            eyeIcon.classList.remove("fa-eye-slash");
            eyeIcon.classList.add("fa-eye");
        }
    }


    function openModal(videoSrc, title, description, details) {
        const modalVideo = document.getElementById('modalVideo');
        const videoSource = document.getElementById('videoSource');

        videoSource.src = videoSrc;
        modalVideo.load();
        modalVideo.play();

        document.getElementById('modalTitle').innerText = title;
        document.getElementById('videoDescription').innerText = description;
        document.getElementById('videoDetails').innerText = details;
        document.getElementById('videoModal').style.display = "block";

        userVote = null;
        updateVoteButtons();
    }

    function closeModal() {
        const modalVideo = document.getElementById('modalVideo');
        modalVideo.pause();
        modalVideo.currentTime = 0;
        document.getElementById('videoModal').style.display = "none";
    }

    function likeVideo(event) {
        if (userVote === 'like') {
            likeCount = 0; 
            userVote = null; 
        } else {
            likeCount = 1; 
            dislikeCount = 0; 
            userVote = 'like'; 
        }
        updateVoteButtons();
    }

    function dislikeVideo(event) {
        if (userVote === 'dislike') {
            dislikeCount = 0; 
            userVote = null; 
        } else {
            dislikeCount = 1; 
            likeCount = 0; 
            userVote = 'dislike'; 
        }
        updateVoteButtons();
    }

    function updateVoteButtons() {
        document.getElementById('likeCount').innerText = likeCount;
        document.getElementById('dislikeCount').innerText = dislikeCount;

        const likeButton = document.getElementById('likeButton');
        const dislikeButton = document.getElementById('dislikeButton');

        if (userVote === 'like') {
            likeButton.style.backgroundColor = '#28a745'; 
            dislikeButton.style.backgroundColor = '#6f42c1'; 
        } else if (userVote === 'dislike') {
            dislikeButton.style.backgroundColor = '#dc3545'; 
            likeButton.style.backgroundColor = '#6f42c1'; 
        } else {
            likeButton.style.backgroundColor = '#6f42c1'; 
            dislikeButton.style.backgroundColor = '#6f42c1'; 
        }
    }

    function shareVideo() {
        const videoTitle = document.getElementById('modalTitle').innerText;
        const videoUrl = window.location.href;

        const shareOptions = `
            <div style="text-align:center; margin:20px; background-color: #6f42c1; color: white; border-radius: 10px; padding: 20px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);">
                <h3 style="margin-bottom: 15px;">Поделитесь видео "${videoTitle}"</h3>
                <p>Ссылка: <input type="text" value="${videoUrl}" id="shareLink" readonly style="width: 80%; margin-bottom: 15px; border-radius: 5px; padding: 5px;"></p>
                <button onclick="copyToClipboard()" style="margin-bottom: 15px; padding: 8px 12px; background-color: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer;">Копировать ссылку</button>
                <h4 style="margin-bottom: 10px;">Поделиться в:</h4>
                <div style="display: flex; justify-content: center; gap: 10px;">
                    <a href="https://vk.com/share.php?url=${encodeURIComponent(videoUrl)}" target="_blank">
                        <img src="https://infostart.ru/upload/iblock/707/707682290371aa2f184f45f41c5b1a20.png" alt="ВКонтакте" style="width: 40px; height: 40px; border-radius: 5px;">
                    </a>
                    <a href="https://api.whatsapp.com/send?text=${encodeURIComponent(videoUrl)}" target="_blank">
                        <img src="https://static.vecteezy.com/system/resources/previews/023/986/589/original/whatsapp-logo-whatsapp-logo-transparent-whatsapp-icon-transparent-free-free-png.png" alt="WhatsApp" style="width: 40px; height: 40px; border-radius: 5px;">
                    </a>
                    <a href="https://t.me/share/url?url=${encodeURIComponent(videoUrl)}" target="_blank">
                        <img src="https://www.leocdn.ru/uploadsForSiteId/200722/content/dfa2aedc-4c48-428e-bb7e-bb04ede78076.png" alt="Telegram" style="width: 40px; height: 40px; border-radius: 5px;">
                    </a>
                </div>
            </div>
        `;
        const shareWindow = window.open("", "Поделиться", "width=400,height=300");
        shareWindow.document.write(shareOptions);
        shareWindow.document.close();
    }

    function copyToClipboard() {
        const shareLink = document.getElementById('shareLink');
        shareLink.select();
        document.execCommand("copy");
        alert("Ссылка скопирована в буфер обмена!");
    }

    function submitComment() {
        const commentInput = document.getElementById('commentInput');
        const commentList = document.getElementById('commentList');
        const errorMessage = document.getElementById('error-message');

        if (currentUsername === "Гость") {
            errorMessage.innerHTML = 'Вы должны быть авторизованы для добавления комментариев! Пожалуйста, <a href="#">войдите</a> или <a href="#">зарегистрируйтесь</a>.';
            return;
        }

        if (commentInput.value.trim() === '') return;

        const newComment = document.createElement('div');
        newComment.classList.add('comment');
        newComment.innerHTML = `
            <span>${commentInput.value}</span>
            <button onclick="deleteComment(this)">Удалить</button>
        `;
        commentList.appendChild(newComment);
        commentInput.value = '';
        errorMessage.innerText = '';
    }

    function deleteComment(button) {
        const comment = button.parentElement;
        comment.remove();
    }

    function searchVideos() {
        const searchInput = document.getElementById('searchInput').value.toLowerCase();
        const videoCards = document.querySelectorAll('.video-card');

        videoCards.forEach(card => {
            const title = card.getAttribute('data-title').toLowerCase();
            const description = card.getAttribute('data-description').toLowerCase();
            const details = card.getAttribute('data-details').toLowerCase();

            card.style.display = (title.includes(searchInput) || description.includes(searchInput) || details.includes(searchInput)) ? '' : 'none';
        });
    }

    document.addEventListener('DOMContentLoaded', () => {
        const videoCount = 6; 
        for (let i = 1; i <= videoCount; i++) {
            const canvas = document.getElementById(`previewCanvas${i}`);
            const ctx = canvas.getContext('2d');
            const placeholderUrl = canvas.getAttribute('data-placeholder');
            const img = new Image();
            img.src = placeholderUrl;
            img.onload = () => {
                canvas.width = 320; 
                canvas.height = 180; 
                ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
            };
            img.onerror = () => {
                console.error('Ошибка загрузки изображения:', placeholderUrl);
            };
        }
    });

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
