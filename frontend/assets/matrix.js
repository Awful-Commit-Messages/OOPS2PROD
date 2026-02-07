// Canvas setup
const c = document.getElementById("matrix");
const ctx = c.getContext("2d");

// Characters
const letters = [
    "ｱ","ｲ","ｳ","ｴ","ｵ","ｶ","ｷ","ｸ","ｹ","ｺ","ｻ","ｼ","ｽ","ｾ","ｿ",
    "ﾀ","ﾁ","ﾂ","ﾃ","ﾄ","ﾅ","ﾆ","ﾇ","ﾈ","ﾉ","ﾊ","ﾋ","ﾌ","ﾍ","ﾎ",
    "ﾏ","ﾐ","ﾑ","ﾒ","ﾓ","ﾔ","ﾕ","ﾖ","ﾗ","ﾘ","ﾙ","ﾚ","ﾛ",
    "人","心","木","土",
    "ㅂ","ㅈ","ㄷ","ㄱ","ㅅ","ㅇ","ㅁ","ㄴ","ㅎ","ㅋ","ㅌ","ㅊ","ㅍ",
    "山","川","子",
    "ا","ب","ت","ث","ج","ح","خ","د","ر","س","ص","م","ن","و","ي",
    "α","β","γ","δ","ε","λ","μ","π","σ","Ω",
    "Ж","Ф","И","Л","Ц","Ч","Я","Ю","Ш",
    "∑","∏","√","∞","≈","≠","≤","≥","∂","∆","∫",
    "¤","§","¶","†","‡","•","◊","◆","▲","▼",
    "0","1","2","3","4","5","6","7","8","9",
    "+","-","=","<",">","|","/","\\","*","%"
];

const letterCount = letters.length;

// Special vertical text
const specialText = "Wright State Hackathon";
const specialChars = specialText.split("");

// Tunables
const fontSize = 15;
const SPECIAL_CHANCE = 0.001;
const SPECIAL_LINGER_FRAMES = 88; // 88 miles per hour great scott!

// Colors
const GREEN = "#0F0";
const RED = "rgb(255,0,0)";

let columns;
let drops;
let xPositions;
let specialActive;
let specialIndex;
let specialLinger;

// Resize
function resizeCanvas() {
    const dpr = Math.min(window.devicePixelRatio || 1, 1.5);

    c.width = window.innerWidth * dpr;
    c.height = window.innerHeight * dpr;
    c.style.width = window.innerWidth + "px";
    c.style.height = window.innerHeight + "px";

    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    columns = (c.width / dpr / fontSize) | 0;

    drops = new Uint16Array(columns);
    xPositions = new Uint16Array(columns);
    specialActive = new Uint8Array(columns);
    specialIndex = new Int16Array(columns).fill(-1);

    // each column gets its own linger list
    specialLinger = new Array(columns);

    for (let i = 0; i < columns; i++) {
        drops[i] = (Math.random() * c.height / fontSize) | 0;
        xPositions[i] = i * fontSize;
        specialLinger[i] = [];
    }
}

resizeCanvas();
window.addEventListener("resize", resizeCanvas);

// Timing
const frameDelay = 35;
let lastTime = 0;

function draw(time) {
    if (time - lastTime < frameDelay) {
        requestAnimationFrame(draw);
        return;
    }
    lastTime = time;

    // Global fade
    ctx.fillStyle = "rgba(0,0,0,0.08)";
    ctx.fillRect(0, 0, c.width, c.height);

    ctx.font = fontSize + "px monospace";

    for (let i = 0; i < columns; i++) {
        const x = xPositions[i];
        const y = drops[i] * fontSize;

        // Trigger special text
        if (!specialActive[i] && Math.random() < SPECIAL_CHANCE) {
            specialActive[i] = 1;
            specialIndex[i] = 0;
        }

        if (specialActive[i]) {
            const idx = specialIndex[i];

            if (idx < specialChars.length) {
                ctx.fillStyle = RED;
                ctx.fillText(specialChars[idx], x, y);

                // push this char into linger list
                specialLinger[i].push({
                    char: specialChars[idx],
                    y: y,
                    life: SPECIAL_LINGER_FRAMES
                });

                specialIndex[i]++;
            } else {
                specialActive[i] = 0;
                specialIndex[i] = -1;
            }
        } else {
            ctx.fillStyle = GREEN;
            ctx.fillText(
                letters[(Math.random() * letterCount) | 0],
                x,
                y
            );
        }

        // draw and decay lingering special chars
        const lingerList = specialLinger[i];
        for (let j = lingerList.length - 1; j >= 0; j--) {
            const l = lingerList[j];
            ctx.fillStyle = RED;
            ctx.fillText(l.char, x, l.y);
            l.life--;
            if (l.life <= 0) {
                lingerList.splice(j, 1);
            }
        }

        if (y > c.height && Math.random() > 0.97) {
            drops[i] = 0;
        }

        drops[i]++;
    }

    requestAnimationFrame(draw);
}

requestAnimationFrame(draw);
