document.addEventListener("DOMContentLoaded", function() {
    const preloader = document.getElementById("preloader");
    const mainContent = document.getElementById("main-content");
    const preloaderVideo = document.getElementById("preloader-video");

    // Обработчик события окончания видео
    preloaderVideo.addEventListener("ended", function() {
      console.log("Видео завершилось."); // Логирование окончания видео
      preloader.style.display = "none"; // Скрываем прелоадер
      mainContent.style.display = "block"; // Показываем основной контент
      setTimeout(() => {
        mainContent.classList.add("visible"); // Добавляем класс для анимации
      }, 50); // Задержка для срабатывания анимации
    });

    // Также устанавливаем таймер на 5 секунд, чтобы избежать зависания
    setTimeout(function() {
      console.log("Таймер истек."); // Логирование срабатывания таймера
      preloader.style.display = "none";
      mainContent.style.display = "block";
      mainContent.classList.add("visible"); // Добавляем класс для анимации
    }, 5000); // Установите время, соответствующее продолжительности видео
  });