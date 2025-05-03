function getCookie(name) {
    let cookieArr = document.cookie.split(";");
    for (let i = 0; i < cookieArr.length; i++) {
        let cookiePair = cookieArr[i].split("=");
        if (name === cookiePair[0].trim()) {
            return decodeURIComponent(cookiePair[1]);
        }
    }
    return null;
}

let currentUsername = getCookie("username") || "Гость";
let likeCount = 0;
let dislikeCount = 0;
let userVote = null;

function togglePassword(passwordFieldId) {
    const passwordField = document.getElementById(passwordFieldId);
    const eyeIcon = passwordField.nextElementSibling.querySelector("i");

    if (passwordField.type === "password") {
        passwordField.type = "text"; 
        eyeIcon.classList.remove("fa-eye-slash");
        eyeIcon.classList.add("fa-eye");
    } else {
        passwordField.type = "password";
        eyeIcon.classList.remove("fa-eye");
        eyeIcon.classList.add("fa-eye-slash");
    }
}

function openModal(videoSrc, title, description, details) {
    document.getElementById("modalTitle").innerText = title;
    document.getElementById("videoDescription").innerText = description;
    document.getElementById("videoSource").src = videoSrc;
    document.getElementById('videoDetails').innerText = details;       // Устанавливаем детали
    document.getElementById('commentList').innerHTML = '';             // Очищаем список комментариев
    document.getElementById("modalVideo").load();        // Запускаем воспроизведение видео

    // Запрос количества лайков и дизлайков
    fetch('/video/votes', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ title: title })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('likeCount').innerText = data.likes;
        document.getElementById('dislikeCount').innerText = data.dislikes;
    });

    document.getElementById('videoModal').style.display = 'block'; // Открываем модальное окно
    // Загружаем комментарии для данного видео
    fetch(`/get_comments/${title}`)
        .then(response => response.json())
        .then(comments => {
            const commentList = document.getElementById('commentList');
            commentList.innerHTML = ''; // Очищаем список перед добавлением новых комментариев
            comments.forEach(comment => {
                const commentDiv = document.createElement('div');
                commentDiv.classList.add('comment');
                commentDiv.setAttribute('data-id', comment.id);
                commentDiv.innerHTML = `
                    <strong>${comment.username}</strong>: <span class="comment-text">${comment.text}</span>
                    ${comment.is_owner ? `<button class="delete-button" onclick="deleteComment(${comment.id})">Удалить</button>` : ''}
                    ${comment.is_owner ? `<button class="edit-button" onclick="openEditCommentModal(${comment.id}, '${comment.text.replace(/'/g, "\\'")}')">Изменить</button>` : ''}
                `;
                commentList.appendChild(commentDiv);
            });            
        });
        
    document.getElementById('videoModal').style.display = 'block'; // Открываем модальное окно

    userVote = null; // Обнуляем голос пользователя
    updateVoteButtons();
}

function closeModal() {
    console.log("closeModal вызвана");
    const modalVideo = document.getElementById('modalVideo');
    modalVideo.pause();
    modalVideo.currentTime = 0;
    document.getElementById('videoModal').style.display = "none";
}

function openEditModal(videoId, title, description) {
    document.getElementById('editVideoId').value = videoId;
    document.getElementById('editTitle').value = title;
    document.getElementById('editDescription').value = description;
    document.getElementById('editModal').style.display = "block";
}

function closeEditModal() {
    document.getElementById('editModal').style.display = "none";
}

function openEditModal(videoId, title, description) {
    document.getElementById('editVideoId').value = videoId;
    document.getElementById('editTitle').value = title;
    document.getElementById('editDescription').value = description;
    document.getElementById('editModal').style.display = "block";
}

function closeEditModal() {
    document.getElementById('editModal').style.display = "none";
}

function openEditCommentModal(commentId, currentText) {
    currentCommentId = commentId;
    document.getElementById('editCommentInput').value = currentText;
    document.getElementById('editCommentModal').style.display = 'block';
}

function closeEditCommentModal() {
    document.getElementById('editCommentModal').style.display = 'none';
}

function submitEditComment() {
    const updatedText = document.getElementById('editCommentInput').value;

    fetch(`/edit_comment/${currentCommentId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text: updatedText })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const commentDiv = document.querySelector(`.comment[data-id="${currentCommentId}"] .comment-text`);
            commentDiv.innerText = updatedText;
            closeEditCommentModal();
        } else {
            alert(data.error);
        }
    });
}

function submitEdit() {
    const videoId = document.getElementById('editVideoId').value;
    const title = document.getElementById('editTitle').value;
    const description = document.getElementById('editDescription').value;

    fetch(`/edit_video/${videoId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ title: title, description: description })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Обновляем заголовок и описание в интерфейсе
            const videoItem = document.querySelector(`.video-item[data-id="${videoId}"]`); // Предполагается, что у вас есть атрибут data-id
            videoItem.querySelector('h3').innerText = title;
            videoItem.querySelector('p:nth-of-type(1) span').innerText = description; // Обновляем описание
            closeEditModal(); // Закрываем модальное окно
        } else {
            alert(data.error);
        }
    });
}


function filterVideos() {
    const input = document.getElementById('searchInput');
    const filter = input.value.toLowerCase();
    const videoList = document.getElementById('videoList');
    const videos = videoList.getElementsByClassName('video-item');
    const gifPlaceholder = document.getElementById('gifPlaceholder');
    let hasVisibleVideos = false;

    for (let i = 0; i < videos.length; i++) {
        const title = videos[i].getElementsByTagName('h3')[0];
        const description = videos[i].getElementsByTagName('p')[0];
        if (title || description) {
            const titleText = title.textContent || title.innerText;
            const descriptionText = description.textContent || description.innerText;

            if (titleText.toLowerCase().indexOf(filter) > -1 || descriptionText.toLowerCase().indexOf(filter) > -1) {
                videos[i].style.display = "";
                hasVisibleVideos = true; // Найдено подходящее видео
            } else {
                videos[i].style.display = "none";
            }
        }
    }

    // Управляем видимостью GIF в зависимости от наличия видео
    if (hasVisibleVideos) {
        gifPlaceholder.style.display = "none";
    } else {
        gifPlaceholder.style.display = "block"; // Показываем GIF, если нет видео
    }
}

function vote(title, voteType) {
    fetch('/video/vote', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ title: title, vote_type: voteType })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Обновить интерфейс при успешном голосовании
            updateVoteCounts(title);
        } else {
            alert(data.error);
        }
    });
}

function likeVideo(event) {
    if (userVote === 'like') {
        // Убираем лайк
        likeCount = 0; 
        userVote = null; 
        vote(document.getElementById('modalTitle').innerText, null); // Убираем голос
    } else {
        likeCount = 1; 
        dislikeCount = 0; 
        userVote = 'like'; 
        vote(document.getElementById('modalTitle').innerText, 'like'); // Ставим лайк
    }
    updateVoteButtons();
}

function dislikeVideo(event) {
    if (userVote === 'dislike') {
        // Убираем дизлайк
        dislikeCount = 0; 
        userVote = null; 
        vote(document.getElementById('modalTitle').innerText, null); // Убираем голос
    } else {
        dislikeCount = 1; 
        likeCount = 0; 
        userVote = 'dislike'; 
        vote(document.getElementById('modalTitle').innerText, 'dislike'); // Ставим дизлайк
    }
    updateVoteButtons();
}

function updateVoteCounts(title) {
    fetch('/video/votes', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ title: title })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('likeCount').innerText = data.likes;
        document.getElementById('dislikeCount').innerText = data.dislikes;
    });
}

function updateVoteButtons() {
    document.getElementById('likeCount').innerText = likeCount;
    document.getElementById('dislikeCount').innerText = dislikeCount;

    const likeButton = document.getElementsByClassName('like-icon')[0];
    const dislikeButton = document.getElementsByClassName('dislike-icon')[0];

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
    const commentInput = document.getElementById("commentInput").value;
    const videoTitle = document.getElementById("modalTitle").innerText; // Получаем название видео из модального окна

    if (!commentInput || !videoTitle) {
        alert("Название видео или текст комментария отсутствует.");
        return;
    }

    fetch('/submit_comment', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            video_title: videoTitle,  // Убедитесь, что это 'video_title'
            comment: commentInput      // Используйте commentInput вместо commentText
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Добавляем новый комментарий на страницу
            const newComment = document.createElement('div');
            newComment.classList.add('comment');
            newComment.setAttribute('data-id', data.comment_id); // Устанавливаем ID комментария для редактирования
            newComment.innerHTML = `
                <strong>${data.username}</strong>: <span class="comment-text">${data.text}</span>
                <button class="delete-button" onclick="deleteComment(${data.comment_id})">Удалить</button>
                <button class="edit-button" onclick="openEditCommentModal(${data.comment_id}, '${data.text.replace(/'/g, "\\'")}')">Изменить</button>
            `;
            document.getElementById('commentList').appendChild(newComment);
            document.getElementById("commentInput").value = ''; // Очищаем поле ввода
            document.getElementById('error-message').innerText = ''; // Очищаем сообщение об ошибке
        } else {
            document.getElementById('error-message').innerText = data.error; // Показываем ошибку, если она есть
        }
    })
    .catch(error => {
        console.error('Ошибка:', error);
        document.getElementById('error-message').innerText = 'Произошла ошибка при отправке комментария.';
    });
}


function deleteComment(commentId) {
    // Подтверждение удаления комментария
    if (confirm('Вы уверены, что хотите удалить этот комментарий?')) {
        fetch(`/delete_comment/${commentId}`, {
            method: 'POST',
        })
        .then(response => {
            if (response.ok) {
                // Удаляем комментарий из DOM
                document.querySelector(`.comment[data-id="${commentId}"]`).remove();
            } else {
                alert('Ошибка при удалении комментария.');
            }
        })
        .catch(error => {
            console.error('Ошибка:', error);
            alert('Произошла ошибка при удалении комментария.');
        });
    }
}

function searchVideos() {
    const searchInput = document.getElementById('searchInput').value.toLowerCase();
    const videoCards = document.querySelectorAll('.video-card');
    const gifPlaceholder = document.getElementById('gifPlaceholder');

    let hasVisibleVideos = false; // Флаг для проверки наличия видимых видео

    videoCards.forEach(card => {
        const title = card.getAttribute('data-title').toLowerCase();
        const description = card.getAttribute('data-description').toLowerCase();
        const details = card.getAttribute('data-details').toLowerCase();

        if (title.includes(searchInput) || description.includes(searchInput) || details.includes(searchInput)) {
            card.style.display = ''; // Показываем видео
            hasVisibleVideos = true; // Устанавливаем флаг в true
        } else {
            card.style.display = 'none'; // Скрываем видео
        }
    });

    // Если нет видимых видео, показываем GIF
    if (!hasVisibleVideos) {
        gifPlaceholder.style.display = 'block'; // Показываем заглушку
    } else {
        gifPlaceholder.style.display = 'none'; // Скрываем заглушку
    }
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

document.querySelector('input[type="file"]').addEventListener('change', function(event) {
    const file = event.target.files[0];
    if (file) {
        const videoElement = document.createElement('video');
        videoElement.src = URL.createObjectURL(file);

        videoElement.onloadedmetadata = function() {
            const duration = videoElement.duration; // Получаем длительность в секундах
            const hours = Math.floor(duration / 3600); // Вычисляем часы
            const minutes = Math.floor((duration % 3600) / 60); // Вычисляем минуты
            const seconds = Math.floor(duration % 60); // Вычисляем секунды

            // Форматируем длительность в чч:мм:сс
            const formattedDuration = `${hours}:${minutes < 10 ? '0' : ''}${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
            document.getElementById('duration').value = formattedDuration; // Устанавливаем значение в поле
        };
    }
});

function formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function setDuration(input) {
    const file = input.files[0];
    if (file) {
        const video = document.createElement('video');
        video.src = URL.createObjectURL(file);
        video.addEventListener('loadedmetadata', function() {
            const durationInSeconds = Math.floor(video.duration);
            document.getElementById('duration').value = formatDuration(durationInSeconds);
        });
    }
}

document.querySelector('.file-input').addEventListener('change', function() {
    const label = this.nextElementSibling;
    if (this.files.length > 0) {
        label.textContent = this.files[0].name; // Отображаем имя файла
    } else {
        label.textContent = 'Выберите файл'; // Сброс текста
    }
    
    // Применяем шрифт к label
    label.style.fontFamily = '"PT Serif Caption", serif';
});

function updateFileName(input) {
    const fileNameInput = document.getElementById('file-name'); // Получаем элемент для отображения имени файла
    if (input.files.length > 0) {
        fileNameInput.value = input.files[0].name; // Отображаем имя файла в текстовом поле
    } else {
        fileNameInput.value = 'Выберите файл'; // Сброс текста
    }
}

// Добавляем обработчик события на текстовое поле, чтобы открыть диалог выбора файла
document.getElementById('videoUploadForm').addEventListener('submit', function(event) {
    event.preventDefault();
    const title = this.title.value;
    const description = this.description.value;
    const durationInput = this.description.value;
    const course = this.course.value; 
    const fileInput = this.video_file;

    const videoCard = document.createElement('div');
    videoCard.className = 'video-card';

    // Создаем элемент video
    const videoElement = document.createElement('video');
    videoElement.controls = true;
    videoElement.src = URL.createObjectURL(fileInput.files[0]);
    videoElement.style.width = '100%';

    // Получаем длительность видео
    videoElement.onloadedmetadata = function() {
        const duration = videoElement.duration; // Получаем длительность в секундах
        const minutes = Math.floor(duration / 60);
        const seconds = Math.floor(duration % 60);
        durationInput.value = `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`; // Форматируем длительность
    };

    // Добавляем кнопку удаления
    const deleteButton = document.createElement('button');
    deleteButton.innerText = 'Удалить видео';
    deleteButton.style.marginTop = '10px'; 
    deleteButton.style.fontFamily = '"PT Serif Caption", serif';
    deleteButton.onclick = function() {
        if (confirm("Вы уверены, что хотите удалить это видео?")) {
            videoCard.remove(); // Удаляем карточку видео
        }
    };

    videoCard.innerHTML = `<strong>Курс:</strong> ${course}<br>
                        <strong>Название:</strong> ${title}<br>
                        <strong>Описание:</strong> ${description}<br>
                        <strong>Длительность:</strong> ${durationInput.value}<br>`;
    videoCard.appendChild(videoElement);
    videoCard.appendChild(deleteButton);

    document.getElementById('videoList').appendChild(videoCard);
    document.getElementById('uploadedVideos').style.display = 'block';

    this.reset(); // Сброс формы после добавления
});