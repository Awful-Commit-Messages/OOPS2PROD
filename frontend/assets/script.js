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

start_button.addEventListener("click", async function () {

    // lock input immediately
    inputEnabled = false;

    const res = await fetch("/api/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" }
    });

    const data = await res.json();

    // fade out button
    start_button.style.opacity = "0";

    setTimeout(async () => {
        start_button.style.display = "none";
        main_page.style.display = "flex";

        setTimeout(() => {
            main_page.style.opacity = "1";
        }, 10);

        // clear terminal and type intro
        textarea.value = "";
        textarea.value += "Narrator:\n";

        await ghostTypeTextarea(textarea, data.narrator_intro);

        if (data.suggested_actions?.length) {
            textarea.value += "\n— You could try —\n";

            for (const action of data.suggested_actions) {
                textarea.value += "• " + action + "\n";
            }

            textarea.value += "\n";
        }

        textarea.value += "oops@2prod:~$\0 ";
        inputEnabled = true;

        textarea.selectionStart = textarea.selectionEnd = textarea.value.length;

    }, 1000);
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
            await ghostTypeTextarea(textarea, response.narration);
            appendToLogger(response);

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
startHeight = logger_display.getBoundingClientRect().height;

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

    if (newHeight < 80) return;
    if (newHeight > main_page.offsetHeight - 100) return;

    logger_display.style.flex = `0 0 ${newHeight}px`;
});

document.addEventListener("mouseup", () => {
    isDragging = false;
    document.body.style.userSelect = "";
});
function appendToLogger(data) {

    const entry = document.createElement("div");
    entry.style.padding = "14px";
    entry.style.borderBottom = "1px solid rgba(125,211,252,0.25)";
    entry.style.fontSize = "12px";
    entry.style.lineHeight = "1.45";
    entry.style.whiteSpace = "pre-wrap";
    entry.style.fontFamily = "monospace";
    entry.style.color = "#7dd3fc";
    entry.style.wordBreak = "break-word";

    const lines = [];

    // Header
    const turn = data.state?.moment_count ?? "?";
    lines.push(`TURN ${turn}`);
    lines.push("────────────────────────");

    // NPC RESPONSES
    if (data.npc_responses?.length) {
        lines.push("\nNPC RESPONSES");
        for (const npc of data.npc_responses) {
            lines.push(`- ${npc.npc_name}`);
            if (npc.dialogue) lines.push(`  Dialogue: "${npc.dialogue}"`);
            if (npc.action) lines.push(`  Action: ${npc.action}`);
            if (npc.emotional_state) lines.push(`  Emotion: ${npc.emotional_state}`);
            if (npc.urgency_change !== undefined)
                lines.push(`  Urgency Δ: ${npc.urgency_change > 0 ? "+" : ""}${npc.urgency_change}`);
        }
    }

    // SCENE STATUS
    if (data.scene_status) {
        lines.push("\nSCENE STATUS");
        const s = data.scene_status;
        if (s.energy_assessment) lines.push(`Energy: ${s.energy_assessment}`);
        if (s.approaching_ending)
            lines.push(`Ending: ${s.ending_type}`);
    }

    // WORLD STATE
    if (data.state) {
        lines.push("\nWORLD STATE");
        if (data.state.tension_level !== undefined)
            lines.push(`Tension: ${data.state.tension_level}`);
        if (data.state.scene_energy)
            lines.push(`Scene Energy: ${data.state.scene_energy}`);
        if (data.state.player_location)
            lines.push(`Location: ${data.state.player_location}`);
    }

    // EXTERNAL EVENT
    if (data.external_event) {
        lines.push("\nEXTERNAL EVENT");
        lines.push(data.external_event);
    }

    // GM DEBUG (collapsed mentally but readable)
    if (data.debug) {
        lines.push("\nGM DEBUG");

        if (data.debug.gm_objective_truth) {
            lines.push("Objective Truth:");
            lines.push(indentBlock(data.debug.gm_objective_truth, 2));
        }

        if (data.debug.narrator_noticed?.length) {
            lines.push("Narrator Noticed:");
            for (const item of data.debug.narrator_noticed) {
                lines.push(`  - ${item}`);
            }
        }

        if (data.debug.narrator_missed?.length) {
            lines.push("Narrator Missed:");
            for (const item of data.debug.narrator_missed) {
                lines.push(`  - ${item}`);
            }
        }
    }

    entry.textContent = lines.join("\n");
    logger_display.appendChild(entry);

    // Only auto-scroll if logger is open
    if (logger_display.style.display !== "none") {
        logger_display.scrollTop = logger_display.scrollHeight;
    }

}
function indentBlock(text, spaces) {
    const pad = " ".repeat(spaces);
    return text
        .split("\n")
        .map(line => pad + line)
        .join("\n");
}
