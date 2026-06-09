/* Клиентские сценарии рекрутинговой ИС «UnitHire».
   Небольшие улучшения интерфейса без внешних зависимостей. */
(function () {
    "use strict";

    // 1. Автоматическое скрытие сообщений об успехе через 5 секунд.
    document.addEventListener("DOMContentLoaded", function () {
        document.querySelectorAll(".alert-success").forEach(function (el) {
            setTimeout(function () {
                el.classList.remove("show");
            }, 5000);
        });
    });

    // 2. Счётчик символов для длинных текстовых полей (сопроводительное письмо,
    //    сообщение обратной связи) — подсказывает пользователю объём ввода.
    document.addEventListener("DOMContentLoaded", function () {
        document.querySelectorAll("textarea").forEach(function (area) {
            var hint = document.createElement("div");
            hint.className = "form-text text-end small";
            area.parentNode.appendChild(hint);
            var update = function () {
                hint.textContent = "Символов: " + area.value.length;
            };
            area.addEventListener("input", update);
            update();
        });
    });

    // 3. Подсветка активного пункта меню по текущему адресу страницы.
    document.addEventListener("DOMContentLoaded", function () {
        var path = window.location.pathname;
        document.querySelectorAll(".navbar-nav .nav-link").forEach(function (link) {
            if (link.getAttribute("href") === path) {
                link.classList.add("active", "fw-bold");
            }
        });
    });
})();
