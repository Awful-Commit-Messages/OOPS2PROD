const logger_button = document.getElementById("logger_button");
let logger_button_toggle = false;

const main_page = document.getElementById("main_page")
const exit_button = document.getElementById("exit_button")

const start_button = document.getElementById("start_button")

logger_button.addEventListener("click", function () {
    const isHidden = logger_display.style.display === "none";

    logger_display.style.display = isHidden ? "block" : "none";
    logger_button.textContent = isHidden ? "Logger (on)" : "Logger (off)";
});

start_button.addEventListener("click", function () {

    fetch("/api/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            event: {
                message: "Hi I'd like to start a game please :)"
            }
        })
    });

    // fade out button
    start_button.style.opacity = "0";

    setTimeout(() => {
        // AFTER fade out finishes
        start_button.style.display = "none";

        // show main page (still invisible)
        main_page.style.display = "flex";

        // next frame so opacity transition actually runs
        setTimeout(() => {
            main_page.style.opacity = "1";
        }, 10);

    }, 1000); // matches fade-out duration

});

exit_button.addEventListener("click", function () {

    // fade out main page
    main_page.style.opacity = "0";

    setTimeout(() => {
        // AFTER fade out
        main_page.style.display = "none";

        // show start button (still invisible first if needed)
        start_button.style.display = "flex";

        // next tick so opacity transition runs
        setTimeout(() => {
            start_button.style.opacity = "1";
        }, 10);

    }, 1000); // matches fade duration

});

logger_button.addEventListener("click", function () {
    logger_button_toggle = !logger_button_toggle;

    logger_button.innerText = logger_button_toggle
        ? "Logger (on)"
        : "Logger (off)";
});

const textarea = document.getElementById("interface_area");

let inputEnabled = true;
textarea.value = "oops@2prod:~$\0 "

textarea.addEventListener("keydown", async (e) => {

    if (!inputEnabled) {
        e.preventDefault();
        return;
    }

    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();

        inputEnabled = false;

        splitString = textarea.value.split('\x00').filter(part => part.trim());
        const lastItem = splitString[splitString.length - 1];

        console.log(lastItem);

        textarea.value += "\n\n";
        const thinkingStart = textarea.value.length;

        textarea.value += "Thinking";
        const stopThinking = startThinkingDots(textarea, thinkingStart);

        try {
            const response = await sendPayload(lastItem + " \0");

            stopThinking();

            textarea.value += "\nNarrator: "
            await ghostTypeTextarea(textarea, response.message);

        } catch (err) {
            stopThinking();
            textarea.value += "\n[error]";
            inputEnabled = true; // unlock on error
        }
    }
});

async function ghostTypeTextarea(textarea, text, i = 0) {
    if (i < text.length) {
        textarea.value += text[i];
        textarea.scrollTop = textarea.scrollHeight;

        setTimeout(
            () => ghostTypeTextarea(textarea, text, i + 1),
            18
        );
    } else {
        textarea.value += "\n\n";
        textarea.value += "oops@2prod:~$\0 ";

        // 🔓 input is now allowed
        inputEnabled = true;

        // force cursor to end
        textarea.selectionStart = textarea.selectionEnd = textarea.value.length;
    }
}

async function sendPayload(message) {

    const res = await fetch("/api/play", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            event: {
                message: message
            }
        })
    });

    if (!res.ok) throw new Error("Request failed");

    const data = await res.json();
    //console.log("sending payload:", data);

    return data;
}

function startThinkingDots(textarea, startIndex) {
    const phrases = [
        "Interpreting the moment",
        "Reading between the lines",
        "Weaving the narrative",
        "Tracking tension",
        "Reconstructing intent",
        "Watching reactions carefully",
        "Letting the scene unfold",
        "This is getting interesting",
        "Something is taking shape"
    ];

    let phraseIndex = Math.floor(Math.random() * phrases.length);
    let currentPhrase = phrases[phraseIndex];
    let dots = 0;
    const maxDots = 3;

    let ticks = 0;

    const intervalId = setInterval(() => {
        ticks++;

        // advance dots smoothly
        dots = (dots + 1) % (maxDots + 1);

        // change phrase only every ~6–8 seconds
        if (ticks % 18 === 0) {
            phraseIndex = (phraseIndex + 1) % phrases.length;
            currentPhrase = phrases[phraseIndex];
            dots = 0;
        }

        textarea.value = textarea.value.slice(0, startIndex);
        textarea.value += currentPhrase + ".".repeat(dots);
        textarea.scrollTop = textarea.scrollHeight;
    }, 400);

    return () => {
        clearInterval(intervalId);
        textarea.value = textarea.value.slice(0, startIndex);
    };
}

let isDragging = false;
let startY = 0;
let startHeight = 0;

logger_resize_handle.addEventListener("mousedown", (e) => {
    isDragging = true;
    startY = e.clientY;
    startHeight = logger_display.offsetHeight;

    document.body.style.userSelect = "none";
});

document.addEventListener("mousemove", (e) => {
    if (!isDragging) return;

    const delta = startY - e.clientY;
    const newHeight = startHeight + delta;

    // clamp height
    if (newHeight < 80) return;
    if (newHeight > main_page.offsetHeight - 100) return;

    logger_display.style.flex = `0 0 ${newHeight}px`;
});

document.addEventListener("mouseup", () => {
    isDragging = false;
    document.body.style.userSelect = "";
});
