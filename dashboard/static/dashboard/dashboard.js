// Переключение темной и светлой тем
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


// Таймер Помодорро
updateCountdowns();

setInterval(updateCountdowns, 1000);


const workDurationInput = document.getElementById("work-duration");
const breakDurationInput = document.getElementById("break-duration");
const timerModeElement = document.getElementById("timer-mode");
const timerDisplay = document.getElementById("timer-display");

const timerStartButton = document.getElementById("timer-start");
const timerPauseButton = document.getElementById("timer-pause");
const timerResetButton = document.getElementById("timer-reset");

const pomodoroElement = document.querySelector(".pomodoro");

const savedWorkDuration = Number(
    localStorage.getItem("pomodoroWorkDuration")
);

const savedBreakDuration = Number(
    localStorage.getItem("pomodoroBreakDuration")
);

if (savedWorkDuration >= 1 && savedWorkDuration <= 120) {
    workDurationInput.value = savedWorkDuration;
}

if (savedBreakDuration >= 1 && savedBreakDuration <= 60) {
    breakDurationInput.value = savedBreakDuration;
}


let currentMode = "work";
let remainingSeconds = Math.round(Number(workDurationInput.value) * 60);
let isRunning = false;
let timerInterval = null;
let endTime = null;

function updateTimerDisplay() {
    const minutes = Math.floor(remainingSeconds / 60)
    const seconds = Math.floor(remainingSeconds % 60)
    timerDisplay.textContent =
        minutes.toString().padStart(2, "0") +
        ":" +
        seconds.toString().padStart(2, "0");
};
updateTimerDisplay();
updateControlButtons();
updateModeAppearance();

timerStartButton.addEventListener("click", () => {
    if (isRunning) {
        return;
    }

    const workSeconds = getDurationSeconds(
        workDurationInput,
        1,
        120
    );

    const breakSeconds = getDurationSeconds(
        breakDurationInput,
        1,
        60
    );

    if (workSeconds === null || breakSeconds === null) {
        alert(
            "Укажите время работы от 1 до 120 минут " +
            "и время отдыха от 1 до 60 минут."
        );
        return;
    }

    isRunning = true;
    updateTimerDisplay();
    updateControlButtons();
    endTime = Date.now() + remainingSeconds * 1000;

    timerInterval = setInterval(() => {
        remainingSeconds = Math.max(
            0,
            Math.ceil((endTime - Date.now()) / 1000)
        );

        updateTimerDisplay();

        if (remainingSeconds === 0) {
            switchMode();
        }
    }, 250);
});

timerPauseButton.addEventListener("click", () => {
    if (isRunning === false) {
        return;
    }

    clearInterval(timerInterval);
    endTime = null;
    timerInterval = null;
    isRunning = false;
    updateTimerDisplay();
    updateControlButtons();

});


timerResetButton.addEventListener("click", () => {
    clearInterval(timerInterval);
    endTime = null;
    timerInterval = null;
    isRunning = false;
    updateTimerDisplay();
    updateControlButtons();
    currentMode = "work"
    remainingSeconds = Math.round(Number(workDurationInput.value) * 60);
    timerModeElement.textContent = "Работа";
    updateTimerDisplay();
    updateModeAppearance();
});


function switchMode() {
    playNotificationSound()

    if (currentMode === "work") {
        currentMode = "break";

        remainingSeconds = Math.round(Number(breakDurationInput.value) * 60);
        timerModeElement.textContent = "Отдых";
    } else {
        currentMode = "work";

        remainingSeconds = Math.round(Number(workDurationInput.value) * 60);
        timerModeElement.textContent = "Работа";
    }

    endTime = Date.now() + remainingSeconds * 1000;
    updateTimerDisplay();
    updateModeAppearance();
}


workDurationInput.addEventListener("input", () => {
    const workSeconds = getDurationSeconds(
        workDurationInput,
        1,
        120
    );

    if (workSeconds !== null) {
        localStorage.setItem(
            "pomodoroWorkDuration",
            workDurationInput.value
        );
    }

    if (!isRunning && currentMode === "work") {
        remainingSeconds = workSeconds ?? 0;
        updateTimerDisplay();
    }
});

breakDurationInput.addEventListener("input", () => {
    const breakSeconds = getDurationSeconds(
        breakDurationInput,
        1,
        60
    );

    if (breakSeconds !== null) {
        localStorage.setItem(
            "pomodoroBreakDuration",
            breakDurationInput.value
        );
    }

    if (!isRunning && currentMode === "break") {
        remainingSeconds = breakSeconds ?? 0;
        updateTimerDisplay();
    }
});

// уведомление таймера
function playNotificationSound() {
    const audioContext = new AudioContext();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);

    oscillator.type = "sine";
    oscillator.frequency.value = 520;

    const currentTime = audioContext.currentTime;

    gainNode.gain.setValueAtTime(0.001, currentTime);
    gainNode.gain.exponentialRampToValueAtTime(
        0.12,
        currentTime + 0.1
    );
    gainNode.gain.exponentialRampToValueAtTime(
        0.001,
        currentTime + 0.7
    );

    oscillator.start(currentTime);
    oscillator.stop(currentTime + 0.7);
}


function getDurationSeconds(input, minimum, maximum) {
    const minutes = Number(input.value)

    if (
        !Number.isFinite(minutes) ||
        minutes < minimum ||
        minutes > maximum
    ) {
        input.focus();
        return null;
    }

    return Math.round(minutes * 60);
}

function updateControlButtons() {
    timerStartButton.disabled = isRunning;
    timerPauseButton.disabled = !isRunning;

    workDurationInput.disabled = isRunning;
    breakDurationInput.disabled = isRunning;
}

function updateModeAppearance() {
    pomodoroElement.dataset.mode = currentMode;
}