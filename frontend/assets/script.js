const logger_button = document.getElementById("logger_button");
let logger_button_toggle = false;

const main_page = document.getElementById("main_page")
const exit_button = document.getElementById("exit_button")

exit_button.addEventListener("click", function () {

    main_page.style.opacity = "0"
    setTimeout(() => {
        main_page.style.display = "none";
    }, 1000);

    start_button.style.display = ""
    start_button.style.opacity = "1"

})

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

        textarea.value += "\n";
        const thinkingStart = textarea.value.length;

        textarea.value += "Thinking";
        const stopThinking = startThinkingDots(textarea, thinkingStart);

        try {
            const response = await sendPayload(lastItem + " \0");

            stopThinking();

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
            50
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
    let dots = 0;
    const maxDots = 6;

    const intervalId = setInterval(() => {
        dots = (dots + 1) % (maxDots + 1);

        // keep everything BEFORE "Thinking"
        textarea.value = textarea.value.slice(0, startIndex);

        textarea.value += "Thinking" + ".".repeat(dots);
        textarea.scrollTop = textarea.scrollHeight;
    }, 369);

    return () => {
        clearInterval(intervalId);
        // remove "Thinking..." after done thinking
        textarea.value = textarea.value.slice(0, startIndex);
    };
}

