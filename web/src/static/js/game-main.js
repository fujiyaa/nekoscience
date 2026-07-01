const { decode } = MessagePack;

const DEBUG_PROFILER_RENDER = true;
const DEBUG_PROFILER_FX = true;
const DEBUG_PROFILER_UPDATE = true;
const DEBUG_PROFILER_MAP = true;
const DEBUG_CONSOLE_LOG = true; 
const DEBUG_PACKET_SIZE_IN_CHAT = true; 

const DEFAULT_SOUNDS = {
    draw: "https://www.myinstants.com/media/sounds/snapchat-messages.mp3",
    blast: "https://www.myinstants.com/media/sounds/duck-button.mp3",
    error: "https://www.myinstants.com/media/sounds/typing-error.mp3",
    erase: "https://www.myinstants.com/media/sounds/yahoo-messenger-message-sound.mp3",
    sign: "https://www.myinstants.com/media/sounds/pop-message.mp3",
    structure: "https://www.myinstants.com/media/sounds/mlbb-new-message-notification.mp3"
};
if (localStorage.getItem("game_volume") === null) {
    localStorage.setItem("game_volume", "0");
}

function openSettings() {
    const el = document.getElementById("settings-overlay");
    if (!el) return;

    el.style.display = "flex";

    const btn = document.getElementById("save-sounds-btn");
    if (btn) btn.disabled = false;

    requestAnimationFrame(loadSoundsToInputs);
    updateVolumeUI();
}

function closeSettings() {
    const el = document.getElementById("settings-overlay");
    if (!el) return;

    el.style.display = "none";

    const buttons = document.querySelectorAll(".volume-bar button");
    buttons.forEach(btn => {
        btn.classList.remove('basic-flash');
    });
}

function saveSounds() {
    const drawEl = document.getElementById("sound-draw");
    const blastEl = document.getElementById("sound-blast");
    const errorEl = document.getElementById("sound-error");
    const eraseEl = document.getElementById("sound-erase");
    const signEl = document.getElementById("sound-sign");
    const structureEl = document.getElementById("sound-structure");
    

    const sounds = {
        draw: drawEl ? drawEl.value.trim() : "",
        blast: blastEl ? blastEl.value.trim() : "",
        error: errorEl ? errorEl.value.trim() : "",
        erase: eraseEl ? eraseEl.value.trim() : "",
        sign: signEl ? signEl.value.trim() : "",
        structure: structureEl ? structureEl.value.trim() : "",
    };

    localStorage.setItem("game_sounds", JSON.stringify(sounds));
    closeSettings();
}



function loadSounds() {
    const saved = JSON.parse(localStorage.getItem("game_sounds") || "{}");

    return {
        draw: saved.draw || DEFAULT_SOUNDS.draw,
        blast: saved.blast || DEFAULT_SOUNDS.blast,
        error: saved.error || DEFAULT_SOUNDS.error,
        erase: saved.erase || DEFAULT_SOUNDS.erase,
        sign: saved.sign || DEFAULT_SOUNDS.sign,
        structure: saved.structure || DEFAULT_SOUNDS.structure,
    };
}

function loadSoundsToInputs() {
    const s = loadSounds();

    const draw = document.getElementById("sound-draw");
    const blast = document.getElementById("sound-blast");
    const error = document.getElementById("sound-error");
    const erase = document.getElementById("sound-erase");
    const sign = document.getElementById("sound-sign");
    const structure = document.getElementById("sound-structure");

    if (draw) draw.value = s.draw;
    if (blast) blast.value = s.blast;
    if (error) error.value = s.error;
    if (erase) erase.value = s.erase;
    if (sign) sign.value = s.sign;
    if (structure) structure.value = s.structure;
}

function resetSounds() {
    localStorage.removeItem("game_sounds");
    loadSoundsToInputs();
    setVolume(0);
    closeSettings();
}

function getVolume() {
    return parseFloat(localStorage.getItem("game_volume") || "0");
}

function setVolume(v, btnElement) {
    localStorage.setItem("game_volume", v.toString());
    updateVolumeUI();
}

function previewSound(inputId) {
    const input = document.getElementById(inputId);
    if (!input) return;

    const url = input.value.trim();

    if (!url.startsWith("http")) return;

    const s = loadSounds();
    const volume = getVolume();

    if (volume <= 0) return;

    const audio = new Audio(url);
    audio.volume = volume;
    audio.play().catch(() => {});
    updateVolumeUI();
}

function playSound(key) {
    const s = loadSounds();
    const volume = getVolume();

    if (!s[key]) return;
    if (volume <= 0) return;

    const audio = new Audio(s[key]);
    audio.volume = volume;
    audio.play().catch(() => {});
}

function updateVolumeUI() {
    const v = getVolume();
    const buttons = document.querySelectorAll(".volume-bar button");
    const map = [0, 0.25, 0.5, 0.75, 1];

    buttons.forEach((btn, i) => {
        const isActive = (map[i] === parseFloat(v));
        btn.style.borderColor = isActive ? "rgba(255,255,255,0.6)" : "rgba(255,255,255,0.15)";

        if (isActive) {
            triggerAnimation(btn, 'basic-flash');
        }
    });    
}


window.addEventListener('load', () => {
    if (DEBUG_CONSOLE_LOG) {
        console.log("Очистка...");
    }
    // localStorage.clear(); 
    sessionStorage.clear();
});
window.onerror = function(message, source, lineno, colno, error) {
    alert("JS: " + message);
};

let kickedByNewSession = false;
let socket;
const wsProtocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
const wsUrl = `${wsProtocol}${window.location.host}/ws/game`;

let currentTool = "draw";

let SIZE = 0;  
let CELL = 0;  

let grid = [];               
let serverContours = {};
let serverLeaderboard = [];
let players = {}; 

let hoveredCellX = -1;
let hoveredCellY = -1;

let floatingTexts = [];
let particles = []; 
let gridAnimationTime = 0;

let isDragging = false; 
let hasMoved = false; 
let startX = 0; let startY = 0; 
let mouseStartX = 0; let mouseStartY = 0;
let lastMouseX = 0; let lastMouseY = 0;

let animationsEnabled = true;
let lastGridHash = "";
let minimapDirty = true;
let leaderboardDirty = true;
let lastLeaderboardHash = "";

window.Telegram.WebApp.ready();
const initData = window.Telegram.WebApp.initData;
let isAuthorized = false;
let pingInterval = null;

let savedAuthToken = localStorage.getItem('auth_token') || "";

const UI = {
    overlays: {
        auth: document.getElementById("auth-overlay"),
        loading: document.getElementById("loading-overlay"),
        reconnect: document.getElementById("reconnect-overlay"),
        kicked: document.getElementById("kicked-overlay")        
    },
    
    toggle: (overlay, show = true) => {
        overlay.style.display = show ? "flex" : "none";
    },

    showReconnect: (show = true) => UI.toggle(UI.overlays.reconnect, show),
    showAuth: (show = true) => UI.toggle(UI.overlays.auth, show),
    showLoading: (show = true) => UI.toggle(UI.overlays.loading, show),
    showKicked: (show = true) => UI.toggle(UI.overlays.kicked, show)
};

let pingTimer = null;
let pongTimeout = null;
const PING_INTERVAL = 20000;
const PONG_DEADLINE = 10000;

function schedulePing() {
    if (pingTimer) clearTimeout(pingTimer);
    
    pingTimer = setTimeout(() => {
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(MessagePack.encode({ type: "ping" }));
            
            pongTimeout = setTimeout(() => {
                console.error("WS: no pong");
                socket.close();
            }, PONG_DEADLINE);
        }
    }, PING_INTERVAL);
}

function submitAuth() {
    const code = document.getElementById("auth-code-input").value;
    if (code.length < 6) {
        alert("Должно быть 6 цифр");
        return;
    }

    savedAuthToken = code;
    localStorage.setItem('auth_token', code);

    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(MessagePack.encode({ 
            type: "external_auth",
            token: code
        }));
    } else {
        alert("Нет интернета");
    }
}

function connect() {
    if (socket) {
        socket.onclose = null;
        socket.close();
    }
    if (pingInterval) clearInterval(pingInterval);

    socket = new WebSocket(wsUrl);
    socket.binaryType = "arraybuffer";

    socket.onopen = () => {
        if (DEBUG_CONSOLE_LOG) {                            
            console.log("WS: Подключено");
        }
        
        schedulePing();

        if (initData && initData.length > 0) {
            socket.send(MessagePack.encode({
                type: "auth", 
                initData: initData
            }));
        } else {
            if (savedAuthToken) {
                if (DEBUG_CONSOLE_LOG) {
                    console.log("WS: Авторизация сохраненным кодом");
                }
                socket.send(MessagePack.encode({
                    type: "external_auth",
                    token: savedAuthToken
                }));
            } else {
                if (DEBUG_CONSOLE_LOG) {
                    console.log("WS: Нет кода авторизации");
                }
                UI.showAuth(true);
            }
        }
    };

    socket.onmessage = (event) => {
        try {
            clearTimeout(pongTimeout);
            schedulePing();

            if (DEBUG_PACKET_SIZE_IN_CHAT) {
                const buffer = new Uint8Array(event.data);

                addChatMessage(
                    `inbound: ${(buffer.byteLength / 1024).toFixed(2)} KB`, 
                    'info',
                    5000,
                    true
                )
            }

            const messages = [...MessagePack.decodeMulti(event.data)];

            for (const message of messages) {
                if (message.type === "pong") return;                

                if (DEBUG_CONSOLE_LOG) {
                    console.group("WS MESSAGE");
                    console.log("Parsed:", message);
                    console.groupEnd();
                }            

                if (isAuthorized) {
                    if (message.type === "init" || message.type === "update") {

                        UI.showLoading(false);
                        UI.showReconnect(false);

                        if (message.type === "init") {
                            processInit(message);
                        } else {
                            processUpdate(message);
                        }
                        
                        requestRender();
                    }
                }

                if (message.type === "auth_success") {
                    window.currentPlayer = message.player_id; 
                    isAuthorized = true;
                    UI.showAuth(false);
                    UI.showReconnect(false);
                    UI.showLoading(true);
                    if (DEBUG_CONSOLE_LOG) {                    
                        console.log("WS: Авторизован");
                    }
                    if (socket && socket.readyState === WebSocket.OPEN) {
                        socket.send(MessagePack.encode({ 
                            type: "get_init"
                        }));
                    } else {
                        alert("Нет интернета");
                    }
                    return;
                } else if (message.type === "error") {
                    isAuthorized = false;

                    alert("Неправильный код авторизации");

                    return;
                } else if (message.type === "session_replaced") {
                    isAuthorized = false;
                    kickedByNewSession = true;

                    UI.showKicked(true);

                    socket.close();
                    return;
                }                
            }
        } catch (e) {
            console.error("WS: Ошибка обработки сообщения:", e);
        }
    };

    socket.onclose = (event) => {
        if (pingTimer) clearTimeout(pingTimer);

        if (kickedByNewSession) {
            if (DEBUG_CONSOLE_LOG) {
                console.log("WS: Соединение закрыто (есть новая сессия)");
            }
            return;
        }
    
        if (DEBUG_CONSOLE_LOG) {
            console.warn("WS: Соединение закрыто. Переподключение...");
        }
        isAuthorized = false;
        UI.showReconnect(true);
        if (pingInterval) clearInterval(pingInterval);
        
        const retryTime = (event.code === 1006) ? 10000 : 5000;
        setTimeout(connect, retryTime);
    };
    
    socket.onerror = (err) => console.error("WS: Ошибка сокета:", err);
}

let prevGrid = null;
let gridEvents = [];
let gridSweeps = [];
let explosions = [];

function processInit(message) {
    const serverData = message.data;

    if (serverData){

        const newLbHash = hashLeaderboard(serverData.leaderboard);
        const newGridHash = hashGrid(serverData.grid);

        if (newLbHash !== lastLeaderboardHash) {
            serverLeaderboard = serverData.leaderboard;
            leaderboardDirty = true;
            lastLeaderboardHash = newLbHash;
        }

        // if (isUpdate) {
        //     prevGrid = grid;
        // }

        if (newGridHash !== lastGridHash) {
            grid = serverData.grid;
            minimapDirty = true;
            lastGridHash = newGridHash;
            worldDirty = true;
        }

        if (serverData.config) {
            SIZE = serverData.config.size;
            CELL = serverData.config.cell;
        }

        if (serverData.contours) {
            serverData.contours.forEach((contourObj) => {                
                serverContours[contourObj.id] = {
                    id: contourObj.id,
                    playerId: contourObj.playerId,
                    path: contourObj.path
                };
            });
        }  

        if (serverData.players) {       
            for (let pId in serverData.players) {
                players[pId] = serverData.players[pId];            
            }

            const currentPId = String(window.currentPlayer);
            const p = players[currentPId];

            if (!p) return;

            const c = p.cooldowns;
            const now = Date.now();

            function applyCooldown(btn, cd) {
                const remainingMs = Math.max(0, cd.endsAt - now);
                
                if (remainingMs > 0 && cd.duration > 0) {
                    const totalSec = cd.duration / 1000;
                    const elapsedSec = (cd.duration - remainingMs) / 1000;
                    
                    startCooldown(btn, totalSec, elapsedSec);
                }
            }

            applyCooldown(btnDraw, c.draw);
            applyCooldown(btnErase, c.erase);
            applyCooldown(btnBlast, c.blast);
            applyCooldown(btnSign, c.sign);
            applyCooldown(btnStructure, c.structure);
            applyCooldown(btnTier2Draw, c.tier2draw);
            applyCooldown(btnTier2Erase, c.tier2erase);
            applyCooldown(btnTier2Blast, c.tier2blast);
        }

        if (message.type === "init") {
            centerMap();
        }
    }   
    
    if (message.events) { processEvents(message.events); }
}

function processUpdate(message) {
    if (message.updated_contours) {
        Object.entries(message.updated_contours).forEach(([idStr, contourData]) => {
            const contourId = parseInt(idStr);

            if (contourData === null) {
                delete serverContours[contourId];
                return;
            }

            if (serverContours[contourId]) {
                Object.assign(serverContours[contourId], contourData);
            } else {
                serverContours[contourId] = {
                    id: contourId,
                    ...contourData
                };
            }           

            if (animationsEnabled) {
                createGridSweep(serverContours[contourId]);
            }            
        });
        worldDirty = true;
    }    

    if (message.events) { processEvents(message.events); }
}

function processEvents(events) {    
    events.forEach(event => {
        if (animationsEnabled) {
            if (event.cords) {
                if (window.currentPlayer != event.cords.player_id) {
                    const halfCell = CELL / 2
                    createExplosion(
                        event.cords.x  * CELL + halfCell, 
                        event.cords.y  * CELL + halfCell, 
                        event.cords.player_id
                    );
                }
                
                triggerHighlight(
                    event.cords.x, 
                    event.cords.y, 
                    event.cords.radius,
                    event.cords.player_id
                );

                triggerAnimation("minimap-container", "basic-flash", event.cords.player_id);
            }
            if (event.msg) {                
                switch(event.msg_to) {
                    case window.currentPlayer:
                    case 'all':
                        addChatMessage(event.msg, event.msg_level);
                        if (event.msg_level == 'warn') {
                            playSound('error')
                        }
                        break;
                }  
            }
        }

        if (event.sfx) {
            playSound(event.sfx)
        }
    });

    const toolEvent = events.find(e => e.tool);
    const cordsEvent = events.find(e => e.cords);

    if (toolEvent && cordsEvent) {
        const tool = toolEvent.tool;
        const { x, y, player_id, contour_id, structure_radius, blast_radius, data, radius } = cordsEvent.cords;
        
        switch(tool) {
            case "blast":
            case "tier2blast": {
                const r = blast_radius;
                const r2 = r * r;
                let immuneTypes = ["Stone"];
                if (tool === "blast") {
                    immuneTypes.push("T2Dot", "Sign");
                }
                for (let dy = -r; dy <= r; dy++) {
                    for (let dx = -r; dx <= r; dx++) {
                        const nx = x + dx;
                        const ny = y + dy;

                        if (ny >= 0 && ny < grid.length && nx >= 0 && nx < grid[0].length && 
                            (dx * dx + dy * dy <= r2)) {
                            
                            const cell = grid[ny][nx];
                            const typeId = cell.type?.id;

                            if (!immuneTypes.includes(typeId)) {
                                cell.contour_id = 0;
                                cell.player_id = null;
                                cell.type = null;
                            }
                        }
                    }
                }
                explosions.push({
                    x: x,
                    y: y,
                    radius: blast_radius,
                    playerId: player_id,
                    t: 0
                });
                break;
            }
            case "sign": {
                if (grid[y] && grid[y][x]) {
                    grid[y][x].player_id = player_id;
                    grid[y][x].contour_id = contour_id;
                    grid[y][x].type = {
                        data: data,
                        id: 'Sign'
                    };                    
                }                    
                break;
            }                 
            case "draw":
            case "tier2draw": {
                const cell_type_id = (tool === "draw") ? "Dot" : "T2Dot";

                if (grid[y] && grid[y][x]) {
                    grid[y][x].player_id = player_id;
                    grid[y][x].contour_id = contour_id;
                    grid[y][x].type = {
                        data: null,
                        id: cell_type_id
                    };
                }

                if (tool == "tier2draw") {
                    createGridEvents([{ x: x, y: y }], player_id);
                }                    
                break;
            }
            case "erase":
            case "tier2erase": {
                if (grid[y] && grid[y][x]) {
                    grid[y][x].contour_id = 0;
                    grid[y][x].player_id = null;
                    grid[y][x].type = null;
                }

                if (tool == "tier2erase") {
                    createGridEvents([{ x: x, y: y }], player_id);
                }  
                break;
            }          
            case "structure": {
                const radius = structure_radius;
                const startX = Math.max(0, x - radius);
                const endX = Math.min(grid[0].length - 1, x + radius);
                const startY = Math.max(0, y - radius);
                const endY = Math.min(grid.length - 1, y + radius);
                const pointsToUpdate = [];

                for (let nx = startX; nx <= endX; nx++) {
                    for (let ny = startY; ny <= endY; ny++) {
                        if (Math.abs(nx - x) + Math.abs(ny - y) === radius) {
                            const cell = grid[ny][nx];
                            
                            cell.contour_id = contour_id;
                            cell.player_id = player_id;
                            cell.type = { id: "T2Dot", data: null };

                            pointsToUpdate.push({ x: nx, y: ny });
                        }
                    }
                }
                createGridEvents(pointsToUpdate, player_id);
                break;                
            }
        }
        worldDirty = true;
        minimapDirty = true;
    }
    
}

const btnDraw = document.getElementById("tool-draw");
const btnErase = document.getElementById("tool-erase");
const btnBlast = document.getElementById("tool-blast");
const btnStructure = document.getElementById("tool-structure");
const btnSign = document.getElementById("tool-sign");
const btnTier2Draw = document.getElementById("tool-tier2draw");
const btnTier2Erase = document.getElementById("tool-tier2erase");
const btnTier2Blast = document.getElementById("tool-tier2blast");

const canvas = document.getElementById("c");
const ctx = canvas.getContext("2d");

const fxCanvas = document.getElementById("fx");
const fxCtx = fxCanvas.getContext("2d");

const minimapCanvas = document.getElementById("minimap");
const mctx = minimapCanvas.getContext("2d");

const minimapFxCanvas = document.getElementById("minimap-fx");
const mFxCtx = minimapFxCanvas.getContext("2d");

const minimapCacheCanvas = document.createElement("canvas");
const minimapCacheCtx = minimapCacheCanvas.getContext("2d");

const worldCanvas = document.createElement("canvas");
const worldCtx = worldCanvas.getContext("2d");

let worldDirty = true;


const GLOW_CONFIG = {
    alpha: [0.04, 0.12, 0.35, 1.0],
    contourWidths: [16, 12, 8, 4],
    pointRadii: [1.8, 1.53, 1.27, 1.0]
};

const maxZoom = 0.05; const minZoom = 2.5;
let zoom = 0.3; let offsetX = 0; let offsetY = 0;

function toggleAnimations() {
    animationsEnabled = !animationsEnabled;
    pointSpriteCache.clear();
    worldDirty = true;
    requestRender();

    if (!animationsEnabled) {
        mFxCtx.clearRect(0, 0, SIZE, SIZE);
        fxCtx.clearRect(0, 0, fxCanvas.width, fxCanvas.height);

        addChatMessage(
            'FX откл. Внимание: обычно FX-кнопка почти не влияет на производительность, но множество визуальных эффектов будет не видно', 
            'warn',
            10000,
            true
        )
    } else {
        addChatMessage('FX вкл', 'good')
    }
    
}

function worldToScreen(x, y) {
    return {
        x: x * zoom + offsetX,
        y: y * zoom + offsetY
    };
}

function resizeCanvas() {
    const w = window.innerWidth;
    const h = window.innerHeight;

    canvas.width = w;
    canvas.height = h;

    worldCanvas.width = w;
    worldCanvas.height = h;

    fxCanvas.width = w;
    fxCanvas.height = h;

    worldDirty = true;
    requestRender()
}

window.addEventListener('resize', resizeCanvas);

function centerMap() {
    offsetX = (window.innerWidth - SIZE * CELL * zoom) / 2;
    offsetY = (window.innerHeight - SIZE * CELL * zoom) / 2;
}

function inBounds(x,y) { return x>=0 && y>=0 && x<SIZE && y<SIZE; }

const colorCache = {
    rgb: {},
    hsl: {}
};

function getBaseColorParams(id) {
    const base = (id * 137.5) % 360;
    const seed = Math.sin(id * 999) * 1000;
    const noise = seed - Math.floor(seed);

    return {
        hue: (base + (noise - 0.5) * 20 + 360) % 360,
        sat: 65 + noise * 15,
        light: 45 + noise * 20
    };
}

function getStableRGB(id) {
    if (!id || id === 0) return { r: 255, g: 255, b: 255 };
    if (colorCache.rgb[id]) return colorCache.rgb[id];

    const params = getBaseColorParams(id);
    const rgb = hslToRgb(params.hue, params.sat, params.light);
    
    colorCache.rgb[id] = rgb;
    return rgb;
}

if (typeof randomColorCache === 'undefined') {
    window.randomColorCache = { rgba: {} };
}

function getStableRGBA(id) {
    if (!id || id === 0) return "rgba(255, 255, 255, ";

    if (!randomColorCache.rgba[id]) {
        const params = getBaseColorParams(id);
        const variants = [];

        for (let i = 0; i < 5; i++) {
            const offset = (Math.random() * 30 - 15);
            const variantLight = Math.max(0, Math.min(100, params.light + offset));
            
            const rgb = hslToRgb(params.hue, params.sat, variantLight);
            variants.push(`rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, `);
        }
        
        randomColorCache.rgba[id] = variants;
    }

    const randomIndex = Math.floor(Math.random() * 5);
    return randomColorCache.rgba[id][randomIndex];
}

function getStableColor(id) {
    if (!id || id === 0) return "hsl(0, 0%, 100%)";
    if (colorCache.hsl[id]) return colorCache.hsl[id];

    const params = getBaseColorParams(id);
    const hsl = `hsl(${params.hue.toFixed(1)}, ${params.sat.toFixed(1)}%, ${params.light.toFixed(1)}%)`;
    
    colorCache.hsl[id] = hsl;
    return hsl;
}

function colorFor(id, alpha = 1) {
    const rgb = getStableRGB(id);
    return `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${alpha})`;
}

function hslToRgb(h, s, l) {
    s /= 100; l /= 100;
    const k = n => (n + h / 30) % 12;
    const a = s * Math.min(l, 1 - l);
    const f = n => l - a * Math.max(-1, Math.min(k(n) - 3, Math.min(9 - k(n), 1)));
    return {
        r: Math.round(255 * f(0)),
        g: Math.round(255 * f(8)),
        b: Math.round(255 * f(4))
    };
}

function getVisibleBounds() {
    const pad = 3;

    const invZoom = 1 / zoom;
    const invCell = 1 / CELL;

    const left = -offsetX * invZoom * invCell;
    const top = -offsetY * invZoom * invCell;

    const right = (canvas.width - offsetX) * invZoom * invCell;
    const bottom = (canvas.height - offsetY) * invZoom * invCell;

    return {
        startX: Math.max(0, Math.floor(left) - pad),
        startY: Math.max(0, Math.floor(top) - pad),
        endX: Math.min(SIZE - 1, Math.ceil(right) + pad),
        endY: Math.min(SIZE - 1, Math.ceil(bottom) + pad)
    };
}

function getGridParams(x, y, time, zoom, min, max) {

    if (!animationsEnabled) {
        return {
            width: 0.2 * zoom,
            color: 120
        };
    }

    const wave1 = Math.sin(time + (x + y) * 0.2);
    const wave2 = Math.sin(time * 0.5 + (x - y) * 0.5) * 0.7;

    const pulse = (wave1 + wave2 + 1.5) / 3.0;

    return {
        width: Math.max(0, (min + pulse * (max - min)) * zoom),
        color: Math.floor(255 * (1 - pulse))
    };
}

function drawGrid(target = ctx, bounds) {
    if (!SIZE) return;

    target.save();

    target.setTransform(
        zoom, 0,
        0, zoom,
        offsetX, offsetY
    );

    target.strokeStyle = "rgb(30,30,30)";
    const gridBase = 1;
    const zoomFactor = Math.sqrt(zoom);
    target.lineWidth = gridBase / zoomFactor;

    target.beginPath();
    for (let x = bounds.startX; x <= bounds.endX + 1; x++) {
        const wx = x * CELL;
        target.moveTo(wx, bounds.startY * CELL);
        target.lineTo(wx, (bounds.endY + 1) * CELL);
    }
    target.stroke();

    target.beginPath();
    for (let y = bounds.startY; y <= bounds.endY + 1; y++) {
        const wy = y * CELL;
        target.moveTo(bounds.startX * CELL, wy);
        target.lineTo((bounds.endX + 1) * CELL, wy);
    }
    target.stroke();

    target.restore();
}

function drawServerContour(target = ctx, bounds, contourObj) {
    const points = contourObj.path;
    if (!points || points.length === 0) return;

    const startX = bounds.startX;
    const endX = bounds.endX;
    const startY = bounds.startY;
    const endY = bounds.endY;

    let visible = false;
    for (let i = 0; i < points.length; i++) {
        const p = points[i];
        if (p.x >= startX && p.x <= endX && p.y >= startY && p.y <= endY) {
            visible = true;
            break;
        }
    }
    if (!visible) return;

    const halfCell = CELL * 0.5;
    const playerId = contourObj.playerId;

    if (playerId == 0) return;

    const fillColor = colorFor(playerId, 0.12);

    target.beginPath();

    let p0 = points[0];
    let x0 = p0.x * CELL + halfCell;
    let y0 = p0.y * CELL + halfCell;

    let s0 = worldToScreen(x0, y0);
    target.moveTo(s0.x, s0.y);

    for (let i = 1; i < points.length; i++) {
        const p = points[i];

        const sx = p.x * CELL + halfCell;
        const sy = p.y * CELL + halfCell;

        const s = worldToScreen(sx, sy);
        target.lineTo(s.x, s.y);
    }

    target.closePath();
    target.fillStyle = fillColor;
    target.fill();

    if (!animationsEnabled) {
        const i = 3;
        target.lineWidth = GLOW_CONFIG.contourWidths[i] * zoom;
        target.strokeStyle = colorFor(playerId, GLOW_CONFIG.alpha[i]);
        target.stroke();
        return;
    }

    for (let i = 0; i < 4; i++) {
        target.lineWidth = GLOW_CONFIG.contourWidths[i] * zoom;
        target.strokeStyle = colorFor(playerId, GLOW_CONFIG.alpha[i]);
        target.stroke();
    }

    // target.fillStyle = 'white';
    // target.font = `${12 * zoom}px Arial`;
    // target.textAlign = 'center';

    // for (let i = 0; i < points.length; i++) {
    //     const p = points[i];
    //     const sx = p.x * CELL + halfCell;
    //     const sy = p.y * CELL + halfCell;
    //     const s = worldToScreen(sx, sy);
        
    //     target.fillText(contourObj.id, s.x, s.y - 10 * zoom);
    // }
}

function forEachVisiblePoint(bounds, callback) {
    if (!grid || grid.length === 0) return;

    const halfCell = CELL * 0.5;

    const startX = bounds.startX;
    const endX = bounds.endX;
    const startY = bounds.startY;
    const endY = bounds.endY;

    for (let y = startY; y <= endY; y++) {
        const row = grid[y];
        if (!row) continue;

        for (let x = startX; x <= endX; x++) {
            const cell = row[x];

            if (!cell || cell.contour_id === 0 || !cell.type)
                continue;

            callback(cell, x, y, x * CELL + halfCell, y * CELL + halfCell);
        }
    }
}

const stoneSpriteCache = new Map();

function getStoneSprite(size) {
    const key = `stone_${size}`;
    if (stoneSpriteCache.has(key)) return stoneSpriteCache.get(key);

    const canvas = typeof OffscreenCanvas !== "undefined"
        ? new OffscreenCanvas(size, size)
        : document.createElement("canvas");

    canvas.width = size;
    canvas.height = size;

    const ctx = canvas.getContext("2d");
    ctx.fillStyle = "rgb(29, 29, 29)";
    ctx.fillRect(0, 0, size, size);

    stoneSpriteCache.set(key, canvas);
    return canvas;
}

function drawStones(target = ctx, bounds) {
    const cellSize = Math.ceil(CELL * zoom);
    const halfSize = cellSize / 2;

    const sprite = getStoneSprite(cellSize);

    forEachVisiblePoint(bounds, (cell, x, y, worldX, worldY) => {
        if (cell.type?.id !== "Stone") return;

        const screen = worldToScreen(worldX, worldY);

        target.drawImage(
            sprite,
            screen.x - halfSize,
            screen.y - halfSize
        );
    });
}


const pointSpriteCache = new Map();

function getPointSprite(playerId, type = "Dot") {
    const key = `${playerId}_${type}_${animationsEnabled}`;

    let sprite = pointSpriteCache.get(key);
    if (sprite) return sprite;

    const size = CELL * 2;
    const canvas = typeof OffscreenCanvas !== "undefined"
        ? new OffscreenCanvas(size, size)
        : document.createElement("canvas");

    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext("2d");
    const center = size / 2;

    const baseRadius = CELL * 0.15;

    const drawCircle = (radius, fillStyle, strokeStyle = null, lineWidth = 0) => {
        ctx.beginPath();
        ctx.arc(center, center, radius, 0, Math.PI * 2);
        if (fillStyle) {
            ctx.fillStyle = fillStyle;
            ctx.fill();
        }
        if (strokeStyle) {
            ctx.strokeStyle = strokeStyle;
            ctx.lineWidth = lineWidth;
            ctx.stroke();
        }
    };

    if (animationsEnabled) {
        const radii = GLOW_CONFIG.pointRadii;
        const alphas = GLOW_CONFIG.alpha;
        for (let i = 0; i < 4; i++) {
            drawCircle(baseRadius * radii[i], colorFor(playerId, alphas[i]));
            
            if (type === "T2Dot") {
                drawCircle(baseRadius * radii[i] * 2, null, `rgba(255, 255, 255, ${alphas[i] * 0.5})`, 1);
            }
        }
    } else {
        drawCircle(baseRadius, colorFor(playerId, 1));
        
        if (type === "T2Dot") {
            drawCircle(baseRadius * 2, null, "white", 3);
        }
    }

    pointSpriteCache.set(key, canvas);
    return canvas;
}

function drawDots(target = ctx, bounds) {
    const baseDrawSize = CELL * 2 * zoom;

    forEachVisiblePoint(bounds, (cell, x, y, worldX, worldY) => {
        if (cell.type.id !== "Dot" && cell.type.id !== "T2Dot") return;

        const screen = worldToScreen(worldX, worldY);        
        const sprite = getPointSprite(cell.player_id, cell.type.id);

        target.drawImage(
            sprite,
            screen.x - baseDrawSize / 2,
            screen.y - baseDrawSize / 2,
            baseDrawSize,
            baseDrawSize
        );
    });
}

const signSpriteCache = new Map();

function getSignSprite(text, fontSize) {
    const key = `${text}_${fontSize}`;

    if (signSpriteCache.has(key)) return signSpriteCache.get(key);

    const width = text.length * (fontSize * 0.6); 
    const height = fontSize * 1.5;

    const canvas = typeof OffscreenCanvas !== "undefined"
        ? new OffscreenCanvas(width, height)
        : document.createElement("canvas");

    canvas.width = width;
    canvas.height = height;

    const ctx = canvas.getContext("2d");
    ctx.font = `bold ${fontSize}px monospace`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillStyle = "white";
    ctx.fillText(text, width / 2, height / 2);

    signSpriteCache.set(key, canvas);
    return canvas;
}

function drawSigns(target = ctx, bounds) {
    if (!grid || grid.length === 0) return;

    const halfCell = CELL * 0.5;
    const fontSize = Math.max(1, 24 * zoom);

    for (let y = bounds.startY; y <= bounds.endY; y++) {
        const row = grid[y];
        if (!row) continue;

        for (let x = bounds.startX; x <= bounds.endX; x++) {
            const cell = row[x];
            if (!cell || cell.type?.id !== "Sign") continue;

            const text = cell.type.data;
            const sprite = getSignSprite(text, fontSize);

            const worldX = x * CELL + halfCell;
            const worldY = y * CELL + halfCell;
            const screen = worldToScreen(worldX, worldY);

            target.drawImage(
                sprite,
                screen.x - sprite.width / 2,
                screen.y - sprite.height / 2
            );
        }
    }
}

function drawMinimap() {
    if (!grid || grid.length === 0) return;

    if (minimapCanvas.width !== SIZE) {
        minimapCanvas.width = SIZE;
        minimapCanvas.height = SIZE;

        minimapCacheCanvas.width = SIZE;
        minimapCacheCanvas.height = SIZE;

        minimapCanvas.style.imageRendering = "pixelated";
        minimapCacheCtx.imageSmoothingEnabled = false;
        mctx.imageSmoothingEnabled = false;

        minimapDirty = true;
    }    
    if (minimapFxCanvas.width !== SIZE) {
        minimapFxCanvas.width = SIZE;
        minimapFxCanvas.height = SIZE;

        minimapFxCanvas.style.imageRendering = "pixelated";
        mFxCtx.imageSmoothingEnabled = false;
    }

    if (minimapDirty) {
        renderMinimapWorld();
        minimapDirty = false;
    }

    renderMinimapViewport();
}

function renderMinimapWorld() {
    minimapCacheCtx.clearRect(0, 0, SIZE, SIZE);
    const imgData = minimapCacheCtx.createImageData(SIZE, SIZE);
    const data = imgData.data;

    for (let y = 0; y < SIZE; y++) {
        for (let x = 0; x < SIZE; x++) {
            const cell = grid[y][x];
            if (!cell || cell.contour_id === 0) continue;
            
            let color;
            if (cell.player_id === 0) {
                color = { r: 29, g: 29, b: 29 };
            } else {
                color = getStableRGB(cell.player_id);
            }           

            const i = (y * SIZE + x) * 4;
            
            data[i]     = color.r;
            data[i + 1] = color.g;
            data[i + 2] = color.b;
            data[i + 3] = 255;
        }
    }
    minimapCacheCtx.putImageData(imgData, 0, 0);
}
function renderMinimapViewport() {    
    mctx.clearRect(0, 0, SIZE, SIZE);
    mctx.drawImage(minimapCacheCanvas, 0, 0);

    const viewLeft = -offsetX / (zoom * CELL);
    const viewTop = -offsetY / (zoom * CELL);
    const viewWidth = canvas.width / (zoom * CELL);
    const viewHeight = canvas.height / (zoom * CELL);

    mctx.strokeStyle = "white";
    mctx.lineWidth = 1;
    mctx.strokeRect(viewLeft, viewTop, viewWidth, viewHeight);
}

function renderMinimapHighlights(ctx) {
    ctx.clearRect(0, 0, SIZE, SIZE);

    minimapHighlights.forEach(h => {
        const pulse = 1 + Math.sin(h.life * 30) * 0.5;
        const size = h.radius * pulse;

        ctx.save();
        ctx.globalAlpha = h.life;
        ctx.strokeStyle = h.color;
        ctx.lineWidth = 1;

        ctx.strokeRect(
            h.x - size / 2,
            h.y - size / 2,
            size,
            size
        );

        ctx.restore();
    });
}

const minimapHighlights = [];

function triggerHighlight(
    x, 
    y, 
    radius = 1,
    player_id = 0,
    decaySpeed = 0.00025 // дефолт
) {
    const color = getStableColor(player_id)

    minimapHighlights.push({
        x,
        y,
        radius,
        color,
        life: 1,
        decaySpeed
    });
}

function updateHighlights(dt) {
    for (let i = minimapHighlights.length - 1; i >= 0; i--) {
        const h = minimapHighlights[i];
        
        const deltaLife = dt * h.decaySpeed;
        h.life -= deltaLife;

        if (h.life <= 0) {
            minimapHighlights.splice(i, 1);
        }
    }
}





function drawHoverTooltip(target = fxCtx) {
    if (hoveredCellX === -1 || hoveredCellY === -1) return;

    const row = grid?.[hoveredCellY];
    const cell = row?.[hoveredCellX];

    if (!cell || cell.contour_id === 0 || cell.player_id === 0) return;

    const ownerId = cell.player_id;
    // if (ownerId === window.currentPlayer) return;
   
    const pIdKey = String(ownerId);
    const player = players[pIdKey];
    
    let playerName = player ? player.name : null;

    if (!playerName) {
        const leaderEntry = serverLeaderboard.find(p => String(p.player_id) === pIdKey);
        playerName = leaderEntry ? leaderEntry.name : `Игрок ${ownerId}`;
    }
    
    const text = `Точка ${playerName}`;
    const screen = worldToScreen(hoveredCellX * CELL + CELL / 2, hoveredCellY * CELL + CELL / 2);

    target.font = "bold 13px monospace";
    const textWidth = target.measureText(text).width;
    const paddingX = 10;
    const paddingY = 6;
    const rectWidth = textWidth + paddingX * 2;
    const rectHeight = 20 + paddingY * 2;

    const rectX = screen.x - rectWidth / 2;
    const rectY = screen.y - rectHeight - (CELL * 0.2 * zoom); 

    target.fillStyle = "rgba(0, 0, 0, 0.75)";
    target.strokeStyle = colorFor(ownerId, 0.5); 
    target.lineWidth = 1;
    
    target.beginPath();
    target.roundRect(rectX, rectY, rectWidth, rectHeight, 4); 
    target.fill();
    target.stroke();

    target.fillStyle = "#ffffff";
    target.textAlign = "center";
    target.textBaseline = "middle";
    target.fillText(text, screen.x, rectY + rectHeight / 2);
}

function drawFloatingTexts(target = fxCtx) {
    target.font = "bold 14px monospace";
    target.textAlign = "center";

    for (const ft of floatingTexts) {
        target.fillStyle = `rgba(231, 76, 60, ${ft.alpha})`;
        target.shadowColor = 'black';
        target.shadowBlur = 4;
        target.fillText(ft.text, ft.x, ft.y);
    }
}

// unused
function showFloatingError(cellX, cellY, text) {
    const screen = worldToScreen(cellX * CELL + CELL / 2, cellY * CELL + CELL / 2);
    
    floatingTexts.push({
        x: screen.x,
        y: screen.y - 15, 
        text: text,
        alpha: 1.0,       
        life: 1.0         
    });
}

const TOOL_BUTTON_MAP = {
    draw: "tool-draw",
    erase: "tool-erase",
    blast: "tool-blast",
    sign: "tool-sign",
    structure: "tool-structure",
    blast: "tool-blast",
    tier2draw: "tool-tier2draw",
    tier2erase: "tool-tier2erase",
    tier2blast: "tool-tier2blast"
};

function flashButtonError(toolName) {

    playSound("error");

    if (animationsEnabled) {
        const btnId = TOOL_BUTTON_MAP[toolName];
        const btn = document.getElementById(btnId);        
        
        if (btn) {
            btn.classList.remove("btn-error-flash");
            void btn.offsetWidth; 
            btn.classList.add("btn-error-flash");
        }
    }
}

function triggerAnimation(elementOrId, className, player_id = 0) {
    const el = (typeof elementOrId === 'string') 
        ? document.getElementById(elementOrId) 
        : elementOrId;
    
    const color = getStableColor(player_id);

    if (el) {
        el.style.setProperty('--flash-color', color);
        el.classList.remove(className);
        void el.offsetWidth;
        el.classList.add(className);
    }
}



function createExplosion(worldX, worldY, playerId, options = {}) {    
    
    const {
        count = 20,
        spread = 3.0,
        duration = 0.5
    } = options;

    for (let i = 0; i < count; i++) {
        const angle = Math.random() * Math.PI * 2;
        const speed = (0.5 + Math.random() * spread);

        particles.push({
            worldX,
            worldY,
            vx: Math.cos(angle) * speed,
            vy: Math.sin(angle) * speed,
            size: 2.5 + Math.random() * 3.5,
            color: getStableRGBA(playerId),
            alpha: 1.0,
            life: 1.0,
            decay: (0.02 + Math.random() * 0.03) / duration 
        });
    }
}

function drawParticles(target = fxCtx) {
    target.save();

    const currentZoom = zoom;
    for (const p of particles) {
        const screen = worldToScreen(p.worldX, p.worldY);
        
        const drawSize = p.size * currentZoom;
        const halfSize = drawSize * 0.5;
        
        target.fillStyle = p.color + p.alpha + ")";
        target.fillRect(
            screen.x - halfSize, 
            screen.y - halfSize, 
            drawSize, 
            drawSize
        );
    }
    target.restore();
}

function createGridEvents(points, playerId = null) {
    for (let i = 0; i < points.length; i++) {
        gridEvents.push({
            x: points[i].x,
            y: points[i].y,
            playerId: playerId,
            t: 0,
            speed: 40 + Math.random() * 80,
            offset: (Math.random() * 0.2 - 0.1),
            dx: (Math.random() - 0.5) * 0.5, 
            dy: (Math.random() - 0.5) * 0.5
        });
    }
}

function updateGridEvents(dt) {
    if (gridEvents.length === 0) {
        return;
    }

    for (let i = gridEvents.length - 1; i >= 0; i--) {
        const e = gridEvents[i];

        e.t += dt * 0.003;

        if (e.t > 1.5) {
            gridEvents.splice(i, 1);
        }
    }
}

function drawGridEvents(target = fxCtx) {
    for (const e of gridEvents) {
        const t = Math.max(0, e.t + e.offset);
        if (t >= 1) continue;

        const cx = (e.x + 0.5 + e.dx) * CELL;
        const cy = (e.y + 0.5 + e.dy) * CELL;
        const screen = worldToScreen(cx, cy);

        const radius = t * e.speed * zoom;
        const alpha = (1.0 - t) * 0.6;

        drawPulse(target, screen, radius, alpha, e.playerId, 0);
    }
}

function createGridSweep(contourData) {
    if (!contourData?.path?.length) return;
    const points = contourData.path;

    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    points.forEach(p => {
        minX = Math.min(minX, p.x); maxX = Math.max(maxX, p.x);
        minY = Math.min(minY, p.y); maxY = Math.max(maxY, p.y);
    });

    const padding = 10;
    const w = (maxX - minX + 1) * CELL + padding * 2;
    const h = (maxY - minY + 1) * CELL + padding * 2;

    const offscreen = document.createElement('canvas');
    offscreen.width = w;
    offscreen.height = h;
    const ctx = offscreen.getContext('2d');

    ctx.beginPath();
    for (let i = 0; i < points.length; i++) {
        const p = points[i];
        const sx = (p.x - minX) * CELL + (CELL * 0.5) + padding;
        const sy = (p.y - minY) * CELL + (CELL * 0.5) + padding;
        if (i === 0) ctx.moveTo(sx, sy); else ctx.lineTo(sx, sy);
    }
    ctx.strokeStyle = "white";
    ctx.lineWidth = 10;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.stroke();

    gridSweeps.push({
        cache: offscreen,
        x: minX * CELL - padding,
        y: minY * CELL - padding,
        w: w,
        h: h,
        life: Math.sqrt(0.4),
        decaySpeed: 1.0 / 1000.0,
        active: true
    });
}

function updateGridSweep(dt) {
    if (gridSweeps.length === 0) {
        return;
    }

    for (let i = gridSweeps.length - 1; i >= 0; i--) {
        const sweep = gridSweeps[i];
        
        sweep.life -= dt * sweep.decaySpeed;

        if (sweep.life <= 0) {
            gridSweeps.splice(i, 1);
        }
    }
}

function drawGridSweep(target = fxCtx) {
    target.save();
    for (const sweep of gridSweeps) {
        const screenPos = worldToScreen(sweep.x, sweep.y);
        
        target.globalAlpha = 0.9 * Math.pow(sweep.life, 2);
        target.drawImage(sweep.cache, screenPos.x, screenPos.y, sweep.w * zoom, sweep.h * zoom);
    }
    target.restore();
}

function drawPulse(target, screen, radius, alpha, playerId, i) {
    if (alpha <= 0) return;

    target.beginPath();
    target.arc(screen.x, screen.y, radius, 0, Math.PI * 2);

    const a = alpha * (1 - i * 0.08);

    target.strokeStyle = colorFor(playerId, a);
    target.lineWidth = (2 * zoom) * (1 - i * 0.1);

    target.stroke();
}

function drawExplosions(target = fxCtx) {
    for (const e of explosions) {

        const screen = worldToScreen(
            e.x * CELL + CELL / 2,
            e.y * CELL + CELL / 2
        );

        const t = e.t;

        const flash = Math.max(0, 1 - t / 0.2);

        const waveT = Math.min(1, Math.max(0, (t - 0.1) / 0.7));

        const decayT = Math.max(0, (t - 0.5) / 1.0);

        const baseRadius = e.radius * CELL;

        target.beginPath();
        target.arc(screen.x, screen.y, baseRadius * 0.4 * flash, 0, Math.PI * 2);
        target.fillStyle = colorFor(e.playerId, flash * 0.8);
        target.fill();

        const waveRadius = baseRadius * (0.3 + waveT * 2.2);

        target.beginPath();
        target.arc(screen.x, screen.y, waveRadius, 0, Math.PI * 2);
        target.strokeStyle = colorFor(e.playerId, (1 - waveT) * 0.6);
        target.lineWidth = (6 - waveT * 4) * zoom;
        target.stroke();

        for (let i = 0; i < 5; i++) {
            const jitter = Math.sin(e.seed + i * 10 + t * 6) * 4;

            target.beginPath();
            target.arc(
                screen.x + jitter,
                screen.y - jitter,
                waveRadius * (1 + i * 0.03),
                0,
                Math.PI * 2
            );

            target.strokeStyle = colorFor(
                e.playerId,
                (0.3 - i * 0.05) * (1 - decayT)
            );

            target.lineWidth = (3 - i * 0.5) * zoom;
            target.stroke();
        }

        target.beginPath();
        target.arc(screen.x, screen.y, waveRadius * 0.2, 0, Math.PI * 2);
        target.fillStyle = colorFor(e.playerId, 0.25 * (1 - decayT));
        target.fill();
    }
}

function hashGrid(grid) {
    let hash = 0;
    for (let y = 0; y < grid.length; y++) {
        const row = grid[y];
        for (let x = 0; x < row.length; x++) {
            const val = grid[y][x].contour_id; 
            hash = (hash * 31 + val) | 0;
        }
    }
    return hash;
}

function hashLeaderboard(lb) {
    return lb.map(p => `${p.player_id}:${p.totalArea}`).join("|");
}

let lastLeaderboardOrder = [];
function renderLeaderboard() {
    const leaderboardEl = document.getElementById("leaderboard");

    const currentOrder = serverLeaderboard.map(p => p.player_id);
    const hasOrderChanged = JSON.stringify(currentOrder) !== JSON.stringify(lastLeaderboardOrder);

    if (hasOrderChanged && lastLeaderboardOrder.length > 0) {
        addChatMessage('Топ игроков изменился', 'info');
        triggerAnimation("leaderboard", "basic-flash");
    }

    lastLeaderboardOrder = currentOrder;

    leaderboardEl.innerHTML = serverLeaderboard.map((player, index) => {
        const playerColor = colorFor(player.player_id, 1);

        return `
            <div class="leader-item" style="display: flex; flex-direction: column; gap: 2px; white-space: nowrap; padding-right: 10px; ${player.player_id === window.currentPlayer ? 'text-decoration: underline;' : ''}">
                <div class="leader-row" style="display: flex; justify-content: flex-start; align-items: center; gap: 8px;">
                    <span style="font-size: 14px; font-weight: bold;">#${index + 1}</span>
                    <span class="player-color-dot" style="background: ${playerColor}; width: 10px; height: 10px; flex-shrink: 0;"></span>
                    <span style="font-size: 14px; font-weight: bold;">
                        ${player.name} ${player.player_id === window.currentPlayer ? '(Вы)' : ''}
                    </span>
                </div>
                <div style="font-size: 11px; color: rgba(255,255,255,0.6); padding-left: 44px;">
                    площадь: ${player.totalArea.toFixed(1)}
                </div>
            </div>
        `;
    }).join("");

    leaderboardDirty = false;
}

function redrawWorld() {
    worldCtx.setTransform(1, 0, 0, 1, 0, 0);
    worldCtx.clearRect(0, 0, worldCanvas.width, worldCanvas.height);

    const bounds = getVisibleBounds();

    measure("Render | Grid", () => drawGrid(worldCtx, bounds), DEBUG_PROFILER_RENDER);
    measure("Render | Stones", () => drawStones(worldCtx, bounds), DEBUG_PROFILER_RENDER);
    measure("Render | Contours", () => {
        Object.values(serverContours).forEach(c => drawServerContour(worldCtx, bounds, c));
    }, DEBUG_PROFILER_RENDER);
    measure("Render | Dots", () => drawDots(worldCtx, bounds), DEBUG_PROFILER_RENDER);
    measure("Render | Signs", () => drawSigns(worldCtx, bounds), DEBUG_PROFILER_RENDER);
}

function render() {
    ctx.clearRect(0,0,canvas.width,canvas.height);

    if (worldDirty) {
        redrawWorld();
        worldDirty = false;
    }

    ctx.save();
    ctx.drawImage(worldCanvas,0,0);
    ctx.restore();

    if (leaderboardDirty) {
        renderLeaderboard();
    }

    drawMinimap();
}

function fxRender(target = fxCtx) {
    target.setTransform(1,0,0,1,0,0);
    target.globalAlpha = 1;
    target.clearRect(0, 0, fxCanvas.width, fxCanvas.height);

    if (gridSweeps.length > 0) {
        measure("FX | Grid Sweep", () => drawGridSweep(target), DEBUG_PROFILER_FX);
    }    
    if (particles.length > 0) {
        measure("FX | Particles", () => drawParticles(target), DEBUG_PROFILER_FX);
    }
    if (gridEvents.length > 0) {
        measure("FX | Grid Events", () => drawGridEvents(target), DEBUG_PROFILER_FX);
    }
    if (explosions.length > 0) {
        measure("FX | Explosions", () => drawExplosions(target), DEBUG_PROFILER_FX); 
    }

    measure("FX | Hover Tooltip", () => drawHoverTooltip(target), DEBUG_PROFILER_FX);

    // unused
    // measure("FX | Floating Texts", () => drawFloatingTexts(target), DEBUG_PROFILER_FX);
}

function mapExtraRender(target = mFxCtx) {
        
    measure("Minimap | Highlights", () => renderMinimapHighlights(target), DEBUG_PROFILER_MAP);
}

function measure(name, fn, profiler) {
    if (profiler) {
        const t = performance.now();
        fn();
        const dt = performance.now() - t;
        
        if (dt > 0.50) {
            console.log(name, dt.toFixed(2));
        }
        if (dt > 0.25) {
            console.log(`${name}: ${dt.toFixed(2)} ms`);
        }
    } else {
        fn();
    }
}

let lastTime = performance.now();

function updateAnimation() {
    if (animationsEnabled) {
        const now = performance.now();
        const dt = now - lastTime;
        lastTime = now;
    
        gridAnimationTime += dt * 0.0007;
        if (window.currentPlayer && players[String(window.currentPlayer)]) {
            
            if (particles.length > 0) {
                measure("UPD | Particles", () => updateParticles(dt), DEBUG_PROFILER_UPDATE);
            }                      
            if (explosions.length > 0) {
                measure("UPD | Explosions", () => updateExplosions(dt), DEBUG_PROFILER_UPDATE); 
            }             
            if (gridEvents.length > 0) {
                measure("UPD | Grid Events", () => updateGridEvents(dt), DEBUG_PROFILER_UPDATE);
            }          
            if (gridSweeps.length > 0) {
                measure("UPD | Grid Sweep", () => updateGridSweep(dt), DEBUG_PROFILER_UPDATE);
            }
            if (minimapHighlights.length > 0) {
                measure("UPD | Highlights", () => updateHighlights(dt), DEBUG_PROFILER_UPDATE);
            }

            // unused
            // if (floatingTexts.length > 0) {
            //     measure("UPD | Floating Texts", () => updateFloatingTexts(dt), DEBUG_PROFILER_UPDATE); 
            // }  
        }
    }

    requestAnimationFrame(updateAnimation);
}

function updateCooldownUI() {
    const p = players[String(window.currentPlayer)];
    if (!p) return;

    const c = p.cooldowns;
    const now = Date.now();

    function syncButton(btn, cd, label) {
        const isCooldownActive = cd.endsAt > now;
        
        let text;
        if (cd.charges === 0) {
            text = label; 
        } else if (cd.charges < cd.maxCharges) {
            text = `${label} (${cd.charges}/${cd.maxCharges})`;
        } else {
            text = label;
        }

        setText(btn, text, isCooldownActive ? cd.endsAt : 0);
    }

    syncButton(btnDraw, c.draw, "Точка");
    syncButton(btnErase, c.erase, "Ластик");
    syncButton(btnSign, c.sign, "Знак 🪧");
    syncButton(btnStructure, c.structure, "Замок 💠");
    syncButton(btnBlast, c.blast, "Взрыв 💥");
    syncButton(btnTier2Draw, c.tier2draw, "Точка Ур.2");
    syncButton(btnTier2Erase, c.tier2erase, "Ластик Ур.2");
    syncButton(btnTier2Blast, c.tier2blast, "Взрыв 💥 Ур.2");
}

function setText(btn, normalText, endsAt) {
    const now = Date.now();

    const remaining = endsAt - now;

    if (remaining > 0) {
        const seconds = Math.ceil(remaining / 1000);
        const newText = `${normalText} (${seconds}s)`;

        if (btn.innerText !== newText) {
            btn.innerText = newText;
        }
    } else {
        if (btn.innerText !== normalText) {
            btn.innerText = normalText;
        }
    }
}


function startCooldown(btn, totalSec, startSec = 0) {
    btn.classList.remove('on-cooldown');
    void btn.offsetWidth; 
    
    if (animationsEnabled) {
        btn.style.setProperty('--total-duration', totalSec + 's');
        btn.style.setProperty('--start-delay', '-' + startSec + 's');
    }
    
    btn.classList.add('on-cooldown');

    setTimeout(() => {
        btn.classList.remove('on-cooldown');
    }, (totalSec - startSec) * 1000);
}

function updateParticles(dt) {
    if (!animationsEnabled) return;

    const dt16 = dt / 16;
    const damping = Math.pow(0.92, dt16);

    for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i];

        p.worldX += p.vx * dt16;
        p.worldY += p.vy * dt16;

        p.vx *= damping;
        p.vy *= damping;

        p.life -= p.decay * dt16;
        p.alpha = Math.max(0, p.life);

        if (p.life <= 0) particles.splice(i, 1);
    }
}

function updateExplosions(dt) {
    if (!animationsEnabled) return;

    for (let i = explosions.length - 1; i >= 0; i--) {
        const e = explosions[i];
        e.t += dt / 600;

        if (e.t >= 1.5) {
            explosions.splice(i, 1);
        }
    }
}

function updateFloatingTexts(dt) {    
    for (let i = floatingTexts.length - 1; i >= 0; i--) {
        const ft = floatingTexts[i];

        ft.life -= dt / 800;
        ft.y -= dt * 0.04;
        ft.alpha = Math.max(0, ft.life);

        if (ft.life <= 0) floatingTexts.splice(i, 1);
    }
}

let renderScheduled = false;

function requestRender() {
    if (renderScheduled) return;

    renderScheduled = true;

    requestAnimationFrame(() => {
        renderScheduled = false;
        render();
    });
}

function startFXLoop() {
    function loop() {
        if (animationsEnabled) {
            fxRender(fxCtx);
            mapExtraRender(mFxCtx);
        }        
        requestAnimationFrame(loop);
    }
    requestAnimationFrame(loop);
}

function changeZoom(multiplier) {
    const centerX = window.innerWidth / 2;
    const centerY = window.innerHeight / 2;
    
    const worldX = (centerX - offsetX) / zoom;
    const worldY = (centerY - offsetY) / zoom;
    
    zoom = Math.min(Math.max(zoom * multiplier, maxZoom), minZoom);
    
    offsetX = centerX - worldX * zoom;
    offsetY = centerY - worldY * zoom;

    worldDirty = true;
    requestRender();
}

canvas.addEventListener("mousedown", (e) => {
    isDragging = true;
    hasMoved = false;
    
    mouseStartX = e.clientX;
    mouseStartY = e.clientY;
    
    lastMouseX = e.clientX;
    lastMouseY = e.clientY;
    
    startX = offsetX;
    startY = offsetY;
});

canvas.addEventListener("mousemove", (e) => {
    if (isDragging) {
        const totalDx = e.clientX - mouseStartX;
        const totalDy = e.clientY - mouseStartY;
        if (Math.hypot(totalDx, totalDy) > 5) {
            hasMoved = true;
        }

        const deltaX = e.clientX - lastMouseX;
        const deltaY = e.clientY - lastMouseY;
        const speed = Math.hypot(deltaX, deltaY);
                
        lastMouseX = e.clientX;
        lastMouseY = e.clientY;
        
        offsetX = startX + totalDx;
        offsetY = startY + totalDy;
        
        hoveredCellX = -1;
        hoveredCellY = -1;

        worldDirty = true;
        requestRender();
    } else {
        const x = Math.floor(((e.clientX - offsetX) / zoom) / CELL);
        const y = Math.floor(((e.clientY - offsetY) / zoom) / CELL);
        hoveredCellX = inBounds(x, y) ? x : -1;
        hoveredCellY = inBounds(x, y) ? y : -1;
    }
});

window.addEventListener("mouseup", (e) => {
    if (isDragging) {
        isDragging = false;
        if (!hasMoved) {
            processClick(e);
            requestRender();
        }
    }
});
canvas.addEventListener("mouseleave", () => { hoveredCellX = -1; hoveredCellY = -1; });

canvas.addEventListener("wheel", (e) => {
    e.preventDefault();
    const mouseX = e.clientX; const mouseY = e.clientY;
    const worldX = (mouseX - offsetX) / zoom; const worldY = (mouseY - offsetY) / zoom;
    zoom = e.deltaY < 0 ? Math.min(zoom * 1.1, minZoom) : Math.max(zoom / 1.1, maxZoom);
    offsetX = mouseX - worldX * zoom; offsetY = mouseY - worldY * zoom;
    worldDirty = true;
    requestRender();
}, { passive: false });

window.addEventListener("keydown", (e) => {
    const key = e.key.toLowerCase();
    if        (key === "w" || key === "ц") {
        setTool("draw");
    } else if (key === "e" || key === "у") {
        setTool("erase");
    } else if (key === "a" || key === "ф") {
        setTool("tier2draw");
    } else if (key === "s" || key === "ы") {
        setTool("tier2erase");
    } else if (key === "d" || key === "в") {
        setTool("structure");
    } else if (key === "f" || key === "а") {
        setTool("sign");
    } else if (key === "g" || key === "п") {
        setTool("blast");
    } else if (key === "h" || key === "р") {
        setTool("tier2blast");
    } else if (key === "pagedown" || key === "=") {
        changeZoom(1.2);
    } else if (key === "pageup" || key === "-" ){
        changeZoom(0.8);    
    } else if (key === "p" || key === "з") {        
        toggleAnimations(); 
    } else if (key === "o" || key === "щ") {
        openSettings();
    } else if (key === "escape" || key === "esc") {
        closeSign();
        closeSettings();
    } 
    // else  {
    //    console.log(key)
    // }
});

canvas.addEventListener("touchstart", (e) => {
    if (e.touches.length > 0) {
        const touch = e.touches[0];
        
        worldDirty = true;
        isDragging = true;
        hasMoved = false;
        mouseStartX = touch.clientX;
        mouseStartY = touch.clientY;
        lastMouseX = touch.clientX;
        lastMouseY = touch.clientY;
        startX = offsetX;
        startY = offsetY;
        requestRender();
    }
}, { passive: false });

canvas.addEventListener("touchmove", (e) => {
    if (isDragging && e.touches.length > 0) {
        e.preventDefault();
        const touch = e.touches[0];
        
        const totalDx = touch.clientX - mouseStartX;
        const totalDy = touch.clientY - mouseStartY;
        
        if (Math.hypot(totalDx, totalDy) > 5) {
            hasMoved = true;
        }

        const deltaX = touch.clientX - lastMouseX;
        const deltaY = touch.clientY - lastMouseY;
        
        offsetX = startX + totalDx;
        offsetY = startY + totalDy;
        
        lastMouseX = touch.clientX;
        lastMouseY = touch.clientY;
        
        hoveredCellX = -1;
        hoveredCellY = -1;

        worldDirty = true;
        requestRender();
    }
}, { passive: false });

canvas.addEventListener("touchend", (e) => {
    if (isDragging) {
        worldDirty = true;
        isDragging = false;
        
        if (!hasMoved) {            
            const touch = e.changedTouches[0];
            processClick({ clientX: touch.clientX, clientY: touch.clientY });
            requestRender();
        }
    }
});

let pendingSignCoords = { x: null, y: null };
function processClick(e) {
    const pIdString = String(window.currentPlayer);
    const pData = players[pIdString];
    if (!pData) return;

    const x = Math.floor(((e.clientX - offsetX) / zoom) / CELL);
    const y = Math.floor(((e.clientY - offsetY) / zoom) / CELL);
    if (!inBounds(x, y)) return;

    const cell = grid[y][x];
    const now = Date.now();

    if (!canUseTool(currentTool, pData, cell, now, x, y)) {
        return;
    }

    if (currentTool === 'sign') {
        pendingSignCoords = { x, y };
        document.getElementById('sign-modal').style.display = 'flex';
        return;
    }

    const worldX = x * CELL + CELL / 2;
    const worldY = y * CELL + CELL / 2;

    createExplosion(worldX, worldY, window.currentPlayer);

    if (socket.readyState === WebSocket.OPEN) {
        socket.send(MessagePack.encode({
            type: "action",
            payload: {
                player_id: window.currentPlayer,
                tool: currentTool,
                x,
                y
            }
        }));
    }
}

function canUseTool(toolName, pData, cell, now, x, y, grid) {
    const cd = pData.cooldowns[toolName];
    if (!cd) return true;

    function messageWithFlash(text) {
        addChatMessage(text, 'warn');
        flashButtonError(toolName);
    }
    
    const isOnCooldown = cd.endsAt > now;
    const hasCharges = cd.maxCharges == null || cd.charges > 0;
    
    switch (toolName) {
        case "sign":
            if (cell.type != null) {
                messageWithFlash('Здесь чем-то занято');
                return false;
            }
            break;

        case "draw":
        case "tier2draw":
            if (cell.contour_id !== 0) {
                messageWithFlash('Здесь уже занято');
                return false;
            }
            break;

        case "structure":
            if (cell.contour_id !== 0) {
                messageWithFlash('Можно строить только на пустом');
                return false;
            }
            break;

        case "erase":
        case "tier2erase":
            if (cell.contour_id === 0 || (cell.type?.id === "Stone")) {
                messageWithFlash('Здесь ничего нет');
                return false;
            }
            if (toolName === "erase" && (cell.type?.id === "T2Dot" || cell.type?.id === "Sign")) {
                messageWithFlash('Это может ластик 2-го уровня');
                return false;
            }
            break;

        case "blast":
        case "tier2blast":
            if (cell.contour_id === 0) {
                messageWithFlash('Не может начинаться с пустого места');
                return false;
            }
            break;
    }

    if (!hasCharges && isOnCooldown) {
        addChatMessage('На перезарядке!', 'tip');
        flashButtonError(toolName);
        return false;
    }

    return true;
}

function submitSign() {
    const text = document.getElementById('sign-input').value;
    const { x, y } = pendingSignCoords;

    if (x !== null && y !== null && text.trim() !== "") {
        if (socket.readyState === WebSocket.OPEN) {
            socket.send(MessagePack.encode({
                type: "action",
                payload: {
                    player_id: window.currentPlayer,
                    tool: "sign",
                    x: x,
                    y: y,
                    text: text
                }
            }));
        }
        
        createExplosion(x * CELL + CELL / 2, y * CELL + CELL / 2, window.currentPlayer);
    } else {
        addChatMessage('Что-то не так с текстом таблички')
    }

    closeSign();
}

function closeSign() {
    document.getElementById('sign-modal').style.display = 'none';
    document.getElementById('sign-input').value = "";
    pendingSignCoords = { x: null, y: null };
}

const shownTooltips = new Set();
const TOOL_TIP_MAP = {
    draw: "обычная точка",
    erase: "ситарет одну обычную точку",
    blast: "стирает обычные точки в радиусе взрыва",
    sign: "табличка с текстом, удаляется только ластиком/взрывом 2-го уровня",
    structure: "структура из точек 2-го уровня",
    tier2draw: "точка 2-го уровня",
    tier2erase: "ситарет одну точку 2-го уровня",
    tier2blast: "стирает точки 2-го уровня в радиусе взрыва"
};

function setTool(tool) {
    document.querySelectorAll('.action-button').forEach(b => b.classList.remove('active'));
    document.getElementById(`tool-${tool}`).classList.add('active');

    currentTool = tool;
    
    // if (!shownTooltips.has(tool)) {
    //     addChatMessage(TOOL_TIP_MAP[tool]);
    //     shownTooltips.add(tool);
    // }
}

function handleMinimapClick(e) {
    if (!SIZE) return;
    const rect = minimapCanvas.getBoundingClientRect();
    
    const clickX = (e.clientX - rect.left) / rect.width;
    const clickY = (e.clientY - rect.top) / rect.height;
    
    const targetWorldX = clickX * SIZE * CELL;
    const targetWorldY = clickY * SIZE * CELL;
    
    offsetX = window.innerWidth / 2 - targetWorldX * zoom;
    offsetY = window.innerHeight / 2 - targetWorldY * zoom;

    worldDirty = true;
    requestRender();
}

function handleMinimapCords(e) {
    if (!SIZE) return;
    const rect = minimapCanvas.getBoundingClientRect();
    
    const clickX = (e.clientX - rect.left) / rect.width;
    const clickY = (e.clientY - rect.top) / rect.height;
    
    const targetWorldX = clickX * SIZE * CELL;
    const targetWorldY = clickY * SIZE * CELL;
    
    addChatMessage(`Миникарта: ${Math.round(targetWorldX)}, ${Math.round(targetWorldY)}`, 'info')
}

minimapCanvas.addEventListener("mousedown", (e) => {
    handleMinimapClick(e);
    
    const onMouseMove = (moveEvent) => handleMinimapClick(moveEvent);
    const onMouseUp = (moveEvent) => {
        window.removeEventListener("mousemove", onMouseMove);
        window.removeEventListener("mouseup", onMouseUp);
        handleMinimapCords(moveEvent);
    };
    
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
});

const overlay = document.getElementById("error-overlay");
const content = document.getElementById("error-content");

function logErrorToOverlay(message, source, lineno, colno, error) {
    const errorText = `
        Error: ${message}
        Source: ${source} (${lineno}:${colno})
        Stack: ${error ? error.stack : 'No stack trace'}
        -----------------------------------
    `;
    
    const div = document.createElement("div");
    div.textContent = errorText;
    content.appendChild(div);
    
    overlay.style.display = "block";
    console.error("Caught error:", message);
}

window.onerror = logErrorToOverlay;

window.onunhandledrejection = (event) => {
    logErrorToOverlay(event.reason, "Promise", 0, 0, event.reason);
};

function addChatMessage(text, type = 'info', timeout = 2000, force = false) {
    if (animationsEnabled || force) {
        const container = document.getElementById('chat-container');
        const msg = document.createElement('div');
        
        msg.className = `chat-message ${type}`;
        msg.innerText = text;
        container.appendChild(msg);
        msg.style.setProperty('--anim-duration', `${timeout}ms`);
        msg.classList.add('fade-out');    

        setTimeout(() => {
            msg.addEventListener('animationend', () => {
                msg.remove();
            }, { once: true });
            
        }, timeout);
    }
}

resizeCanvas();
centerMap();
updateAnimation();
startFXLoop();
setInterval(updateCooldownUI, 300);
connect();