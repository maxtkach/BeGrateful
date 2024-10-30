let currentDate = new Date(2024, 9);

function renderCalendar() {
    const calendarElement = document.getElementById("calendar");
    const titleElement = document.getElementById("calendar-title");

    calendarElement.innerHTML = "";

    const weekdays = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"];
    weekdays.forEach(day => {
        const dayDiv = document.createElement("div");
        dayDiv.textContent = day;
        dayDiv.classList.add("weekday");
        calendarElement.appendChild(dayDiv);
    });

    const firstDay = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
    const lastDay = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);

    titleElement.textContent = `${firstDay.toLocaleString('uk-UA', { month: 'long' })} ${currentDate.getFullYear()}`;

    let startDay = firstDay.getDay();
    startDay = (startDay === 0 ? 7 : startDay);

    for (let i = 1; i < startDay; i++) { 
        const emptyDiv = document.createElement("div");
        calendarElement.appendChild(emptyDiv);
    }

    for (let day = 1; day <= lastDay.getDate(); day++) {
        const dayDiv = document.createElement("div");
        dayDiv.textContent = day;

        dayDiv.addEventListener("click", () => {
            const selectedDate = new Date(currentDate.getFullYear(), currentDate.getMonth(), day);
            const formattedDate = `${selectedDate.getFullYear()}-${(selectedDate.getMonth() + 1).toString().padStart(2, '0')}-${selectedDate.getDate().toString().padStart(2, '0')}`;
            console.log(`Перенаправление на: ${formattedDate}`);
            window.location.href = `/gratitudes/${formattedDate}`;
        });

        dayDiv.classList.add("calendar-day");
        calendarElement.appendChild(dayDiv);
    }
}

document.getElementById("prev-month").addEventListener("click", () => {
    currentDate.setMonth(currentDate.getMonth() - 1);
    renderCalendar();
});

document.getElementById("next-month").addEventListener("click", () => {
    currentDate.setMonth(currentDate.getMonth() + 1);
    renderCalendar();
});
const toggleCalendarButton = document.getElementById('toggle-calendar');
const toggleListButton = document.getElementById('toggle-list');
const underline = document.querySelector('.underline');

// Функция для обновления позиции подчеркивания
function moveUnderline(button) {
    const rect = button.getBoundingClientRect();
    const containerRect = document.getElementById('toggle-container').getBoundingClientRect();
    underline.style.width = `${rect.width}px`;
    underline.style.transform = `translateX(${rect.left - containerRect.left}px)`;
}

toggleCalendarButton.addEventListener('click', function(e) {
    e.preventDefault();
    document.getElementById('calendar-container').style.display = 'block';
    document.getElementById('gratitude-list-container').style.display = 'none';

    toggleCalendarButton.classList.add('active');
    toggleListButton.classList.remove('active');

    moveUnderline(toggleCalendarButton);
});

toggleListButton.addEventListener('click', function(e) {
    e.preventDefault();
    document.getElementById('calendar-container').style.display = 'none';
    document.getElementById('gratitude-list-container').style.display = 'block';

    toggleListButton.classList.add('active');
    toggleCalendarButton.classList.remove('active');

    moveUnderline(toggleListButton);
});

// Начальная позиция подчеркивания
moveUnderline(toggleCalendarButton);


renderCalendar();