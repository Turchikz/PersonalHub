
const savedTheme = localStorage.getItem("theme");

if (savedTheme === "dark" || savedTheme === "light") {
    document.documentElement.dataset.theme = savedTheme;
}

const themeToggle = document.getElementById("theme-toggle");

themeToggle.addEventListener("click", () => {
    const currentTheme = document.documentElement.dataset.theme;

    if (currentTheme === "dark") {
        document.documentElement.dataset.theme = "light";
    } else {
        document.documentElement.dataset.theme = "dark";
    }

    localStorage.setItem(
        "theme",
        document.documentElement.dataset.theme
    );
});

const eventCards = document.querySelectorAll(".event-card");

function updateCountdowns() {
    eventCards.forEach((card) => {
    const targetDate = new Date(card.dataset.target);
    const currentDate = new Date();

    const timeDifference = Math.max(0, targetDate.getTime() - currentDate.getTime());

    const days = Math.floor(timeDifference / (1000 * 60 * 60 * 24));
    const hours = Math.floor((timeDifference / (1000 * 60 * 60)) % 24);
    const minutes = Math.floor((timeDifference / (1000 * 60)) % 60);
    const seconds = Math.floor((timeDifference / 1000) % 60);
    card.querySelector(".days").textContent = days.toString().padStart(2, "0");
    card.querySelector(".hours").textContent = hours.toString().padStart(2, "0");
    card.querySelector(".minutes").textContent = minutes.toString().padStart(2, "0");
    card.querySelector(".seconds").textContent = seconds.toString().padStart(2, "0");
});
}

updateCountdowns();

setInterval(updateCountdowns, 1000);