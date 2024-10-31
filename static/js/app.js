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

// Функция для переключения видимости пароля
function togglePassword(fieldId) {
    const passwordField = document.getElementById(fieldId);
    passwordField.type = passwordField.type === 'password' ? 'text' : 'password';
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
