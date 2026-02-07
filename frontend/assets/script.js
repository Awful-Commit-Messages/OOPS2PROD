const logger_button = document.getElementById("logger_button");
let logger_button_toggle = false;

const main_page = document.getElementById("main_page")
const exit_button = document.getElementById("exit_button")

const start_button = document.getElementById("start_button")

logger_button.addEventListener("click", function () {
    logger_button_toggle = !logger_button_toggle;

    logger_display.style.display = logger_button_toggle ? "block" : "none";
    logger_button.innerText = logger_button_toggle
        ? "Logger (on)"
        : "Logger (off)";
});
function formatStartupInfo(data) {
    const lines = [];

    lines.push(`SCENARIO: ${data.scenario_name}`);
    lines.push(`NARRATOR: ${data.narrator_name}`);
    lines.push("");

    if (data.opening_scene) {
        lines.push("OPENING SCENE");
        lines.push("────────────");
        lines.push(data.opening_scene);
        lines.push("");
    }

    const state = data.state;
    if (state) {
        lines.push("WORLD STATE");
        lines.push("───────────");
        lines.push(`Role: ${state.player_role}`);
        lines.push(`Location: ${state.player_location}`);
        lines.push(`Tension: ${state.tension_level}`);
        lines.push(`Energy: ${state.scene_energy}`);
        lines.push("");

        if (state.situation_description) {
            lines.push("SITUATION");
            lines.push(state.situation_description);
            lines.push("");
        }

        if (state.npcs && Object.keys(state.npcs).length) {
            lines.push("CHARACTERS");
            lines.push("──────────");

            for (const npc of Object.values(state.npcs)) {
                lines.push(`${npc.name}`);
                lines.push(`  Personality: ${npc.personality}`);
                lines.push(`  Mood: ${npc.emotional_state}`);
                lines.push(`  Goal: ${npc.current_goal}`);
                lines.push(`  Urgency: ${npc.urgency_level}`);
                lines.push("");
            }
        }
    }

    lines.push("────────────");
    lines.push("SYSTEM READY");
    lines.push("");

    return lines.join("\n");
}
start_button.addEventListener("click", async function () {

    if (start_button.dataset.loading) return;
    start_button.dataset.loading = "true";

    inputEnabled = false;

    // Immediate visual feedback
    start_button.innerText = "Starting…";
    start_button.style.pointerEvents = "none";
    start_button.style.opacity = "0.85";
    start_button.classList.add("loading");

    let data;
    try {
        const res = await fetch("/api/start", {
            method: "POST",
            headers: { "Content-Type": "application/json" }
        });

        if (!res.ok) throw new Error("Start failed");
        data = await res.json();

    } catch (err) {
        start_button.innerText = "Start failed — retry";
        start_button.style.pointerEvents = "auto";
        start_button.dataset.loading = "";
        console.error(err);
        return;
    }

    // Now that we HAVE data — transition UI
    start_button.style.opacity = "0";

    setTimeout(async () => {
        start_button.style.display = "none";
        main_page.style.display = "flex";

        requestAnimationFrame(() => {
            main_page.style.opacity = "1";
        });

        textarea.value = "";

        // ── BOOT SEQUENCE ─────────────────────────────
        textarea.value += "Initializing narrative engine...\n\n";

        await ghostTypeTextarea(
            textarea,
            formatStartupInfo(data)
        );

        textarea.value += "Narrator:\n";
        await ghostTypeTextarea(
            textarea,
            data.narrator_intro
        );

        // ── ENTER SHELL MODE ──────────────────────────
        enterShellMode();

    }, 600); // slightly faster feels snappier
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
            enterShellMode();

        } catch (err) {
            stopThinking();
            textarea.value += "\n[error]";
            inputEnabled = true; // unlock on error
        }
    }
});

async function ghostTypeTextarea(textarea, text, speed = 18) {
    return new Promise(resolve => {
        let i = 0;

        function type() {
            if (i < text.length) {
                textarea.value += text[i++];
                textarea.scrollTop = textarea.scrollHeight;
                setTimeout(type, speed);
            } else {
                textarea.value += "\n\n";
                resolve();
            }
        }

        type();
    });
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

function enterShellMode() {
    textarea.value += "oops@2prod:~$\0 ";
    inputEnabled = true;

    textarea.selectionStart =
    textarea.selectionEnd =
        textarea.value.length;
}

