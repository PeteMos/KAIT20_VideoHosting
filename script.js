document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById("videoModal");
    const modalVideo = document.getElementById("modalVideo");
    const videoSource = document.getElementById("videoSource");
    const modalTitle = document.getElementById("modalTitle");

    const videoCards = document.querySelectorAll('.video-card');

    videoCards.forEach(card => {
        const openModalBtn = card.querySelector('.open-modal');
        openModalBtn.addEventListener('click', () => {
            const videoSrc = card.getAttribute('data-video-src');
            const videoTitle = card.getAttribute('data-video-title');

            videoSource.src = videoSrc;
            modalTitle.textContent = videoTitle;
            modalVideo.load(); // Загрузить новое видео
            modal.style.display = "block"; // Показать модальное окно
        });
    });

    const closeModalBtn = document.querySelector('.close');
    closeModalBtn.addEventListener('click', () => {
        modal.style.display = "none"; // Скрыть модальное окно
        modalVideo.pause(); // Остановить видео
    });

    window.addEventListener('click', (event) => {
        if (event.target === modal) {
            modal.style.display = "none"; // Скрыть модальное окно
            modalVideo.pause(); // Остановить видео
        }
    });

    const likeBtn = modal.querySelector('.like-btn');
    const dislikeBtn = modal.querySelector('.dislike-btn');
    const likeCount = modal.querySelector('.like-count');
    const dislikeCount = modal.querySelector('.dislike-count');
    const commentInput = modal.querySelector('textarea');
    const submitCommentBtn = modal.querySelector('.submit-comment');
    const commentList = modal.querySelector('.comment-list');

    let likes = 0;
    let dislikes = 0;

    likeBtn.addEventListener('click', () => {
        likes++;
        likeCount.textContent = `${likes} лайков`;
    });

    dislikeBtn.addEventListener('click', () => {
        dislikes++;
        dislikeCount.textContent = `${dislikes} дизлайков`;
    });

    submitCommentBtn.addEventListener('click', () => {
        const commentText = commentInput.value;
        if (commentText) {
            const li = document.createElement('li');
            li.textContent = commentText;
            commentList.appendChild(li);
            commentInput.value = '';
        }
    });
});
