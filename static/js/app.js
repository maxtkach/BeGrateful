document.addEventListener('DOMContentLoaded', function() {
    const friendsModal = document.getElementById('friendsModal');
    const closeFriendsModalBtn = document.getElementById('closeFriendsModalBtn');
    const friendsIcon = document.getElementById('friendsIcon');
    
    // Открытие модального окна друзей
    friendsIcon.addEventListener('click', function(event) {
        event.preventDefault();
        friendsModal.style.display = 'block';
    });

    // Закрытие модального окна
    function closeModal(modal) {
        modal.style.display = 'none';
    }

    // Закрытие модальных окон при клике вне их содержимого
    window.addEventListener('click', function(event) {
        if (event.target === friendsModal) {
            closeModal(friendsModal);
        } else if (event.target === modal) { // Предполагаем, что modal определен глобально
            closeModal(modal);
        }
    });

    closeFriendsModalBtn.addEventListener('click', function() {
        closeModal(friendsModal);
    });

     // Editable Profile Description
     const editDescriptionButton = document.querySelector('.edit-btn[data-field="profileDescription"]');
     const descriptionSpan = document.getElementById('profileDescription');
     const descriptionInput = document.getElementById('profileDescriptionInput');
 
     editDescriptionButton.addEventListener('click', function () {
         if (descriptionSpan.style.display !== 'none') {
             descriptionSpan.style.display = 'none';
             descriptionInput.style.display = 'inline';
             this.textContent = 'Зберегти';
         } else {
             descriptionSpan.style.display = 'inline';
             descriptionInput.style.display = 'none';
             this.textContent = 'Редагувати';
 
             const newValue = descriptionInput.value;
             sendUpdatedValueToServer('description', newValue); // Sending the updated value to the server
         }
     });
 
// Открытие модального окна
    const modal = document.getElementById("editProfileModal");
    const btn = document.getElementById("editProfileButton");
    const closeEditBtn = document.getElementsByClassName("close")[0];
     
    btn.onclick = function() {
        modal.style.display = "block";
    }
    
    closeEditBtn.onclick = function() {
        closeModal(modal);
        clearPasswordFields();
    }
    
    // Закрытие модального окна при нажатии вне его
    window.onclick = function(event) {
        if (event.target == modal) {
            closeModal(modal);
        }
    }
    

    // Delete Gratitude
    const deleteButtons = document.querySelectorAll('.delete-gratitude');

    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const gratitudeId = this.dataset.id; // Получаем ID благодарности
            
            if (confirm('Вы уверены, что хотите удалить эту благодарность?')) {
                deleteGratitude(gratitudeId);
            }
        });
    });
});


function togglePassword(clickedIcon) {
    const passwordFields = [document.getElementById('password'), document.getElementById('confirm_password')];
    const isPasswordVisible = passwordFields[0].type === 'text';
    const icons = document.querySelectorAll('.toggle-password img');

    // Переключаем тип обоих полей
    passwordFields.forEach(field => {
        field.type = isPasswordVisible ? 'password' : 'text';
    });

    // Добавляем анимацию к иконкам
    icons.forEach(icon => {
        icon.classList.add('animating');
        
        // Меняем иконку после небольшого тайм-аута для эффекта исчезновения
        setTimeout(() => {
            icon.src = isPasswordVisible ? "/static/icons/eye-icon.svg" : "/static/icons/eye-closed.svg";
        }, 200); // Половина продолжительности анимации

        // Убираем класс анимации после её завершения
        icon.addEventListener('animationend', () => {
            icon.classList.remove('animating');
        }, { once: true });
    });
}

function deleteGratitude(gratitudeId) {
    fetch(`/delete_gratitude/${gratitudeId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({}), 
    })
    .then(response => {
        if (response.ok) {
            const listItem = document.querySelector(`.global_gratitude[data-id='${gratitudeId}']`);
            if (listItem) {
                listItem.remove();
            }
        } else {
            alert('Ошибка при удалении благодарности.'); 
        }
    })
    .catch(error => {
        console.error('Ошибка:', error);
    });
    
}

function sendUpdatedValueToServer(field, newValue) {
    fetch(`/update_profile`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ field: field, value: newValue }),
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => {
                alert(`Ошибка: ${err.error}`);
            });

        }
        alert('Профіль успішно оновлено.');
    })
    .catch(error => {
        console.error('Ошибка:', error);
        alert('Системна помилка. Спробуйте ще раз пізніше.');
    });
}


document.querySelector('.icon-hide-profile').addEventListener('click', function() {
    const leftSide = document.querySelector('.left-side');
    const profileTopElements = document.querySelector('.profile-top-elements');
    const icon = document.querySelector('.icon-hide-profile');

    if (icon.classList.contains('flipped')) {
        // Возвращаем стили к исходному состоянию
        leftSide.style.width = '30%'; // Вернуть к исходному размеру
        profileTopElements.style.gap = '50%'; // Устанавливаем нужный начальный gap
        icon.style.transform = 'scaleX(1)'; // Вернуть иконку в начальное положение
        icon.classList.remove('flipped');
    } else {
        // Изменяем стили
        leftSide.style.width = '19%';
        profileTopElements.style.gap = '20%';
        icon.style.transform = 'scaleX(-1)';
        icon.classList.add('flipped');
    }
});

