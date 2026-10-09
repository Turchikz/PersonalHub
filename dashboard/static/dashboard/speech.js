(() => {
    let generating = false;
    let activeAudio = null;
    const objectUrls = new Map();

    document.querySelectorAll(".countdown-speech-form").forEach((form) => {
        const button = form.querySelector(".speech-button");
        const status = form.querySelector(".speech-status");
        const audio = form.querySelector(".speech-audio");
        let manualPlayback = false;
        audio.hidden = true;

        audio.addEventListener("play", () => {
            if (activeAudio && activeAudio !== audio) activeAudio.pause();
            activeAudio = audio;
            status.textContent = "";
        });
        audio.addEventListener("ended", () => {
            if (activeAudio === audio) activeAudio = null;
            status.textContent = "";
        });
        audio.addEventListener("error", () => {
            status.textContent = "Не удалось воспроизвести аудио.";
        });

        form.addEventListener("submit", async (event) => {
            event.preventDefault();
            if (generating) {
                status.textContent = "Дождись завершения текущего запроса.";
                return;
            }
            if (manualPlayback) {
                try {
                    await audio.play();
                    manualPlayback = false;
                    button.textContent = "Озвучить";
                    status.textContent = "";
                } catch {
                    status.textContent = "Не удалось воспроизвести аудио. Попробуй ещё раз.";
                }
                return;
            }
            const token = form.querySelector('[name="csrfmiddlewaretoken"]')?.value;
            if (!token) {
                status.textContent = "Обнови страницу и попробуй ещё раз.";
                return;
            }

            generating = true;
            button.disabled = true;
            button.setAttribute("aria-busy", "true");
            button.textContent = "Подготовка…";
            status.textContent = "Создаём аудио…";
            if (activeAudio) activeAudio.pause();

            const controller = new AbortController();
            const timeout = window.setTimeout(() => controller.abort(), 70000);
            try {
                const response = await fetch(form.action, {
                    method: "POST",
                    credentials: "same-origin",
                    headers: { "X-CSRFToken": token, "Accept": "audio/wav" },
                    signal: controller.signal,
                });
                if (!response.ok) {
                    let message = "Не удалось озвучить событие.";
                    if (response.status === 403) message = "Обнови страницу и попробуй ещё раз.";
                    if (response.status === 404) message = "Событие не найдено.";
                    if (response.headers.get("Content-Type")?.includes("application/json")) {
                        const data = await response.json();
                        if (typeof data.error === "string") message = data.error;
                    }
                    throw new Error(message);
                }
                if (!response.headers.get("Content-Type")?.includes("audio/wav")) {
                    throw new Error("Сервер вернул неверный формат аудио.");
                }

                const blob = await response.blob();
                if (objectUrls.has(audio)) URL.revokeObjectURL(objectUrls.get(audio));
                const objectUrl = URL.createObjectURL(blob);
                objectUrls.set(audio, objectUrl);
                audio.src = objectUrl;
                status.textContent = "";
                try {
                    await audio.play();
                } catch {
                    manualPlayback = true;
                    status.textContent = "Нажми «Воспроизвести», чтобы прослушать.";
                }
            } catch (error) {
                status.textContent = error.name === "AbortError"
                    ? "Озвучивание заняло слишком много времени. Попробуй ещё раз."
                    : error instanceof TypeError
                        ? "Не удалось связаться с сервером. Попробуй ещё раз."
                        : error.message;
            } finally {
                window.clearTimeout(timeout);
                generating = false;
                button.disabled = false;
                button.removeAttribute("aria-busy");
                button.textContent = manualPlayback ? "Воспроизвести" : "Озвучить";
            }
        });
    });

    window.addEventListener("pagehide", (event) => {
        if (event.persisted) return;
        if (activeAudio) activeAudio.pause();
        objectUrls.forEach((url) => URL.revokeObjectURL(url));
        objectUrls.clear();
    });
})();
