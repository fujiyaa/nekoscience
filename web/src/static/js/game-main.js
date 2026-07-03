const DEBUG_PROFILER_RENDER = false;
const DEBUG_PROFILER_FX = false;
const DEBUG_PROFILER_UPDATE = false;
const DEBUG_PROFILER_MAP = false;
const DEBUG_CONSOLE_LOG = false; 
const DEBUG_SPRIE_CACHE_LOG = true; 
const DEBUG_PACKET_SIZE_IN_CHAT = false; 

const DEFAULT_SOUNDS = {
    draw: "https://www.myinstants.com/media/sounds/snapchat-messages.mp3",
    blast: "https://www.myinstants.com/media/sounds/duck-button.mp3",
    error: "https://www.myinstants.com/media/sounds/typing-error.mp3",
    erase: "https://www.myinstants.com/media/sounds/yahoo-messenger-message-sound.mp3",
    sign: "https://www.myinstants.com/media/sounds/pop-message.mp3",
    structure: "https://www.myinstants.com/media/sounds/mlbb-new-message-notification.mp3"
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
let lastLeaderboardHash = "";
let signActive = false;

window.Telegram.WebApp.ready();
const initData = window.Telegram.WebApp.initData;
let isAuthorized = false;
let pingInterval = null;

let savedAuthToken = localStorage.getItem('auth_token') || "";

let pingTimer = null;
let pongTimeout = null;
const PING_INTERVAL = 20000;
const PONG_DEADLINE = 10000;

let ClientMessage;
let ServerMessage;

if (localStorage.getItem("game_volume") === null) {
    localStorage.setItem("game_volume", "0");
}

const hueSlider = document.getElementById('hue-slider');
const colorPreview = document.getElementById('color-preview');

hueSlider.addEventListener('input', (e) => {
    const hue = e.target.value;
    const color = `hsl(${hue}, 100%, 50%)`;
    colorPreview.style.backgroundColor = color;
    e.target.style.setProperty('--thumb-color', color);
});

function openPersonalSettings() {
    const el = document.getElementById("settings-personal-overlay");
    if (!el) return;
    el.style.display = "flex";

    const player_id = window.currentPlayer

    hueSlider.value = getPlayerCustomHue(player_id);
    colorPreview.style.backgroundColor = getPlayerCustomColor(player_id);

    const nickname = document.getElementById("personal-nickname");
    if (nickname) nickname.value = getPlayerCustomNickname(player_id);
}
function closePersonalSettings() {
    const el = document.getElementById("settings-personal-overlay");
    if (!el) return;    

    el.style.display = "none";
}

function savePersonal() {
    const newNickname = document.getElementById("personal-nickname").value;
    const newHue = parseInt(document.getElementById("hue-slider").value, 10);

    if (socket.readyState === WebSocket.OPEN) {
        sendProto("personal", {
            nickname: newNickname,
            hue: newHue        
        });
    } else {
        alert("Нет интернета или сервер оффлайн");
    }
    
    closePersonalSettings();
}
function resetPersonal() {
    const newNickname = getPlayerOldNickname(window.currentPlayer);

    if (socket.readyState === WebSocket.OPEN) {
        sendProto("personal", {
            nickname: newNickname,
            hue: -1       
        });
    } else {
        alert("Нет интернета или сервер оффлайн");
    }

    closePersonalSettings();
}

function openAudioSettings() {
    const el = document.getElementById("settings-audio-overlay");
    if (!el) return;

    el.style.display = "flex";

    const btn = document.getElementById("save-sounds-btn");
    if (btn) btn.disabled = false;

    requestAnimationFrame(loadSoundsToInputs);
    updateVolumeUI();
}

function closeAudioSettings() {
    const el = document.getElementById("settings-audio-overlay");
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
    closeAudioSettings();
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
    closeAudioSettings();
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

    updateVolumeUI();

    if (volume <= 0) return;

    const audio = new Audio(url);
    audio.volume = volume;
    audio.play().catch(() => {});    
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
    sessionStorage.clear();
});
window.onerror = function(message, source, lineno, colno, error) {
    alert("JS: " + message);
};

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

protobuf.load("static/game.proto", (err, root) => {
    if (err) throw err;

    ClientMessage = root.lookupType("ClientMessage");
    ServerMessage = root.lookupType("ServerMessage");
  });

function sendProto(type, data, retryCount = 0) {
    const MAX_RETRIES = 5;
    const RETRY_DELAY = 500;

    if (!ClientMessage) {
        if (retryCount < MAX_RETRIES) {            
            setTimeout(() => {
                sendProto(type, data, retryCount + 1);
            }, RETRY_DELAY);
            
            return;
        }
    }
    const msg = ClientMessage.create({ [type]: data });
    const buffer = ClientMessage.encode(msg).finish();
    socket.send(buffer);
}

function schedulePing() {
    if (pingTimer) clearTimeout(pingTimer);
    
    pingTimer = setTimeout(() => {
        if (socket && socket.readyState === WebSocket.OPEN) {            
            sendProto("ping", {});
                       
            pongTimeout = setTimeout(() => {
                console.error("WS: no pong");
                socket.close();
            }, PONG_DEADLINE);
        } else {
            alert("Нет интернета или сервер оффлайн");
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
        sendProto("externalAuth", { token: code });
    } else {
        alert("Нет интернет или сервер оффлайн");
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
            sendProto("auth", { initData: initData });
        } else {
            if (savedAuthToken) {
                if (DEBUG_CONSOLE_LOG) {
                    console.log("WS: Авторизация сохраненным кодом");
                }
                sendProto("externalAuth", { token: savedAuthToken });
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

            const buffer = new Uint8Array(event.data);

            const serverMsg = ServerMessage.decode(buffer);

            if (DEBUG_PACKET_SIZE_IN_CHAT) {
                addChatMessage(
                    `inbound: ${(buffer.byteLength / 1024).toFixed(2)} KB`, 
                    'info',
                    3000,
                    true
                );
            }

            if (serverMsg.pong) return;                

            if (DEBUG_CONSOLE_LOG) {
                console.group("WS MESSAGE");
                console.log(`inbound: ${(buffer.byteLength / 1024).toFixed(2)} KB`);
                console.log("Parsed:", serverMsg);
                console.groupEnd();
            }            

            if (isAuthorized) {
                 
                if (serverMsg.initResponse || serverMsg.update ) {
                    
                    UI.showLoading(false);
                    UI.showReconnect(false);

                    if (serverMsg.initResponse) {
                        processInit(serverMsg.initResponse);
                    } else {
                        processUpdate(serverMsg.update);
                    }
                    
                    requestRender();
                }
            }            

            if (serverMsg.authSuccess) {
                const data = serverMsg.authSuccess;
                window.currentPlayer = data.playerId;
                isAuthorized = true;
                UI.showAuth(false);
                UI.showReconnect(false);
                UI.showLoading(true);
                if (DEBUG_CONSOLE_LOG) {                    
                    console.log("WS: Авторизован");
                }
                if (socket && socket.readyState === WebSocket.OPEN) {                    
                    sendProto("init", {});
                } else {
                    alert("Нет интернета или сервер оффлайн");
                }
                return;
            } else if (serverMsg.error) {
                isAuthorized = false;
                UI.showAuth(true);
                UI.showReconnect(false);
                UI.showLoading(false);
                alert("Неправильный код авторизации");
                return;
            } else if (serverMsg.sessionReplaced) {
                isAuthorized = false;
                kickedByNewSession = true;
                UI.showReconnect(false);
                UI.showLoading(false);
                UI.showKicked(true);
                socket.close();
                return;
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

function processInit(initResponse) {
    SIZE = initResponse.config.size;
    CELL = initResponse.config.cell;
    serverLeaderboard = initResponse.leaderboard;
    grid = initResponse.grid;
    
    minimapDirty = true;
    worldDirty = true;  

    if (initResponse.contours) {
        initResponse.contours.forEach((contourObj) => {                
            serverContours[contourObj.id] = {
                id: contourObj.id,
                playerId: contourObj.playerId,
                path: contourObj.path
            };
        });
    }  

    if (initResponse.players) {
        for (let pId in initResponse.players) {
            players[pId] = initResponse.players[pId];            
        }

        const currentPId = String(window.currentPlayer);
        const p = players[currentPId];

        if (!p) return;

        const c = p.cooldowns;
        const now = Date.now();

        function applyCooldown(btn, cd) {
            const endsAt = cd.endsAt ? Number(cd.endsAt) : 0;            
            if (endsAt === 0) return;
            const now = Date.now();
            const remainingMs = Math.max(0, endsAt - now);
            
            if (remainingMs > 0 && cd.duration > 0) {
                const totalSec = cd.duration / 1000;
                const startTime = endsAt - cd.duration;
                const elapsedSec = (now - startTime) / 1000;                
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
    updateCooldownUI();
    updateLeaderboardCache();
    renderLeaderboard();
    loadMapState();
    loadToolState();
    if (initResponse.events) { processEvents(initResponse.events); }
}

function processUpdate(message) {
    if (message.updatedContours) {
        Object.entries(message.updatedContours).forEach(([idStr, contourData]) => {
            const contourId = parseInt(idStr);

            if (!contourData) {
                console.error('!contourData')
                return;
            }

            if (contourData.isDeleted) {
                contourCache.delete(contourId);
                delete serverContours[contourId];
                return;
            }

            if (serverContours[contourId]) {
                contourCache.delete(contourId);
                serverContours[contourId].playerId = contourData.playerId;
                serverContours[contourId].path = contourData.path;
            } else {
                contourCache.delete(contourId);
                serverContours[contourId] = {
                    id: contourId,
                    playerId: contourData.playerId,
                    path: contourData.path
                };
            }           
    

            if (animationsEnabled) {
                createGridSweep(serverContours[contourId]);
            }            
        });
        worldDirty = true;
    }
    if (message.players) {
        for (let pId in message.players) {
            players[pId] = message.players[pId];            
        }

        const currentPId = String(window.currentPlayer);
        const p = players[currentPId];

        if (!p) return;

        const c = p.cooldowns;
        const now = Date.now();

        function applyCooldown(btn, cd) {
            const endsAt = cd.endsAt ? Number(cd.endsAt) : 0;            
            if (endsAt === 0) return;
            const now = Date.now();
            const remainingMs = Math.max(0, endsAt - now);
            
            if (remainingMs > 0 && cd.duration > 0) {
                const totalSec = cd.duration / 1000;
                const startTime = endsAt - cd.duration;
                const elapsedSec = (now - startTime) / 1000;                
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
        
        updateCooldownUI();
    }
    if (message.leaderboard && message.leaderboard.length > 0) {
        serverLeaderboard = message.leaderboard
        updateLeaderboardCache();
        renderLeaderboard();
    }

    if (message.events) { processEvents(message.events); }
}

function processEvents(events) {    
    events.forEach(event => {
        if (animationsEnabled) {
            if (event.cords) {
                if (window.currentPlayer != event.cords.playerId) {
                    const halfCell = CELL*0.5
                    createExplosion(
                        event.cords.x*CELL+halfCell, 
                        event.cords.y*CELL+halfCell, 
                        event.cords.playerId
                    );
                }                
                triggerHighlight(
                    event.cords.x, 
                    event.cords.y, 
                    event.cords.radius,
                    event.cords.playerId
                );
                triggerAnimation("minimap-container", "basic-flash", event.cords.playerId);
            }
            if (event.msg) {                
                switch(event.msg.toId) {
                    case String(window.currentPlayer):
                    case 'all':
                        addChatMessage(event.msg.text, event.msg.level, 6000, false);
                        break;
                }  
            }
        }
        if (event.updatedColors) {
            contourCache.clear();
            pointSpriteCache.clear();
            coloredSpriteCache.clear();
            minimapDirty = true;
        }
        if (event.sfx) {
            playSound(event.sfx.sfx)
        }
    });

    const eventsArray = Object.values(events);
    const toolEvent = eventsArray.find(e => e.tool);
    const cordsEvent = eventsArray.find(e => e.cords);

    if (toolEvent && cordsEvent) {
        const tool = toolEvent.tool.tool;
        const { 
            x, 
            y, 
            contourId, 
            playerId, 
            radius,
            structureRadius,
            blastRadius,
            data
        } = cordsEvent.cords;

        const index = y * SIZE + x;
        if (grid[index]) {        
            switch(tool) {
                case "blast":
                case "tier2blast": {
                    const r = blastRadius;
                    const r2 = r * r;
                    let immuneTypes = ["Stone"];
                    if (tool === "blast") {
                        immuneTypes.push("T2Dot", "Sign");
                    }
                    for (let dy = -r; dy <= r; dy++) {
                        for (let dx = -r; dx <= r; dx++) {
                            const nx = x + dx;
                            const ny = y + dy;
                            if (ny >= 0 && ny < SIZE && nx >= 0 && nx < SIZE && (dx * dx + dy * dy <= r2)) {                                
                                const targetIndex = ny * SIZE + nx;
                                const cell = grid[targetIndex];                                 
                                const typeId = cell.type?.id;
                                if (cell && !immuneTypes.includes(typeId)) {
                                    cell.contourId = 0;
                                    cell.playerId = 0;                                    
                                    if (cell.type) {
                                        cell.type.id = "";
                                        cell.type.data = "";
                                    }
                                }
                            }
                        }
                    }
                    explosions.push({
                        x: x,
                        y: y,
                        radius: blastRadius,
                        playerId: playerId,
                        t: 0
                    });
                    break;
                }
                case "sign": {
                    grid[index].playerId = playerId;
                    grid[index].contourId = contourId;
                    grid[index].type = {
                        data: data,
                        id: 'Sign'
                    };             
                    break;
                }
                case "draw":
                case "tier2draw": {
                    const cellTypeId = (tool === "draw") ? "Dot" : "T2Dot";
                    
                    grid[index].playerId = playerId;
                    grid[index].contourId = contourId;
                    grid[index].type = {
                        data: null,
                        id: cellTypeId
                    };                    
                    if (tool === "tier2draw") {
                        createGridEvents([{ x: x, y: y }], playerId);
                    }                
                    break;
                }
                case "erase":
                case "tier2erase": {
                    grid[index].playerId = null;
                    grid[index].contourId = 0;
                    grid[index].type = null;

                    if (tool == "tier2erase") {
                        createGridEvents([{ x: x, y: y }], playerId);
                    }  
                    break;
                }          
                case "structure": {
                    const radius = structureRadius;
                    const startX = Math.max(0, x - radius);
                    const endX = Math.min(SIZE - 1, x + radius);
                    const startY = Math.max(0, y - radius);
                    const endY = Math.min(SIZE - 1, y + radius);
                    const pointsToUpdate = [];

                    for (let nx = startX; nx <= endX; nx++) {
                        for (let ny = startY; ny <= endY; ny++) {
                            if (Math.abs(nx - x) + Math.abs(ny - y) === radius) {
                                const index = ny * SIZE + nx;
                                const cell = grid[index];                                
                                cell.contourId = contourId;
                                cell.playerId = playerId;                                
                                if (cell.type) {
                                    cell.type.id = "T2Dot";
                                    cell.type.data = "";
                                } else {
                                    cell.type = { id: "T2Dot", data: "" };
                                }
                                pointsToUpdate.push({ x: nx, y: ny });
                            }
                        }
                    }
                    createGridEvents(pointsToUpdate, playerId);
                    break;
                }
            }
            worldDirty = true;
            minimapDirty = true;
        } else {
            console.error('out of bounds (tool events)')
        }
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
    coloredSpriteCache.clear();
    contourCache.clear();
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

window.addEventListener('resize', resizeCanvas);
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

let saveTimeout;
function debouncedSave() {
    clearTimeout(saveTimeout);
    saveTimeout = setTimeout(saveMapState, 500);
}

function saveMapState() {
    applyBounds();
    const state = {
        zoom: zoom,
        offsetX: offsetX,
        offsetY: offsetY
    };   
    localStorage.setItem('mapState', JSON.stringify(state));
}

function loadMapState() {
    const saved = localStorage.getItem('mapState');
    if (saved) {
        try {
            const state = JSON.parse(saved);
            zoom = state.zoom || 1;
            offsetX = state.offsetX || 0;
            offsetY = state.offsetY || 0;  
            applyBounds();     
            
        } catch (e) {
            console.warn(e);
        }
    }
}

function saveToolState() {
    applyBounds();
    const state = {
        tool: currentTool
    };   
    localStorage.setItem('toolState', JSON.stringify(state));
}

function loadToolState() {
    const saved = localStorage.getItem('toolState');
    if (saved) {
        try {
            const state = JSON.parse(saved);
            setTool(state.tool || 'draw');
        } catch (e) {
            console.warn(e);
        }
    }
}

function applyBounds() {
    const bounds = getVisibleBounds();
    
    const isVisible = bounds.startX <= bounds.endX && bounds.startY <= bounds.endY;

    if (!isVisible) {    
        const mapSize = SIZE * CELL * zoom;
        const viewWidth = canvas.width;
        const viewHeight = canvas.height;

        const oldOffsetX = offsetX;
        const oldOffsetY = offsetY;

        offsetX = mapSize < viewWidth 
            ? (viewWidth - mapSize) / 2 
            : Math.max(viewWidth - mapSize, Math.min(0, offsetX));

        offsetY = mapSize < viewHeight 
            ? (viewHeight - mapSize) / 2 
            : Math.max(viewHeight - mapSize, Math.min(0, offsetY));

        if (oldOffsetX !== offsetX || oldOffsetY !== offsetY) {
            worldDirty = true;
            requestRender();
        }
    }
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

function getStableHue(id) {
    if (!id || id === 0) return "hsl(0, 0%, 100%)";
    if (colorCache.hsl[id]) return colorCache.hsl[id];

    const params = getBaseColorParams(id);
    const hue = params.hue.toFixed(1);
    
    return hue;
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

function drawGrid(target = ctx, bounds) {
    const width = 1 / Math.sqrt(zoom);

    target.save();
    target.setTransform(zoom, 0, 0, zoom, offsetX, offsetY);    
    target.fillStyle = "#111111";
    target.fillRect(0, 0, SIZE * CELL, SIZE * CELL);

    if (zoom > 0.15) {
        target.strokeStyle = "rgb(30, 30, 30)";       
        target.lineWidth = width;
        target.beginPath();
        for (let x = bounds.startX; x <= bounds.endX + 1; x++) {
            const wx = x * CELL;
            target.moveTo(wx, bounds.startY * CELL);
            target.lineTo(wx, (bounds.endY + 1) * CELL);
        }
        for (let y = bounds.startY; y <= bounds.endY + 1; y++) {
            const wy = y * CELL;
            target.moveTo(bounds.startX * CELL, wy);
            target.lineTo((bounds.endX + 1) * CELL, wy);
        }
        target.stroke();
    }
    
    target.strokeStyle = "rgb(41, 41, 41)"; 
    target.lineWidth = width * 4;
    target.strokeRect(0, 0, SIZE * CELL, SIZE * CELL);

    target.restore();
}

const contourCache = new Map();
function getCachedContour(contourId ,playerId, points, animationsEnabled) {
    const key = contourId;
    
    if (contourCache.has(key)) {
        return contourCache.get(key);
    }

    if (DEBUG_SPRIE_CACHE_LOG){
        console.log(`new CONTOUR sprite | ${contourCache.size+1} total`)
    }

    let minX = points[0].x, maxX = points[0].x;
    let minY = points[0].y, maxY = points[0].y;
    for (const p of points) {
        if (p.x < minX) minX = p.x; if (p.x > maxX) maxX = p.x;
        if (p.y < minY) minY = p.y; if (p.y > maxY) maxY = p.y;
    }

    const offscreen = document.createElement('canvas');
    offscreen.width = (maxX - minX + 1) * CELL + 10; 
    offscreen.height = (maxY - minY + 1) * CELL + 10;
    const ctx = offscreen.getContext('2d');

    const halfCell = CELL * 0.5;
    ctx.beginPath();
    ctx.moveTo((points[0].x - minX) * CELL + halfCell, (points[0].y - minY) * CELL + halfCell);
    for (let i = 1; i < points.length; i++) {
        ctx.lineTo((points[i].x - minX) * CELL + halfCell, (points[i].y - minY) * CELL + halfCell);
    }
    ctx.closePath();
    
    ctx.fillStyle = getPlayerCustomColor(playerId, 0.2);
    ctx.fill();

    const iterations = animationsEnabled ? 4 : 1;
    for (let i = 0; i < iterations; i++) {
        const idx = animationsEnabled ? i : 3;
        ctx.lineWidth = GLOW_CONFIG.contourWidths[idx];
        ctx.strokeStyle = getPlayerCustomColor(playerId, GLOW_CONFIG.alpha[idx]);
        ctx.stroke();
    }

    const data = { canvas: offscreen, minX, minY };
    contourCache.set(key, data);
    return data;
}

function drawServerContour(target = ctx, bounds, contourObj) {
    const points = contourObj.path;
    if (!points || points.length <= 1) return;

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

    const { canvas, minX, minY } = getCachedContour(
        contourObj.id, 
        contourObj.playerId, 
        contourObj.path,
        animationsEnabled
    );

    target.drawImage(
        canvas,
        (minX * CELL) * zoom + offsetX, 
        (minY * CELL) * zoom + offsetY,
        canvas.width * zoom,
        canvas.height * zoom
    );   
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
    const startX = Math.max(0, bounds.startX);
    const endX = Math.min(SIZE - 1, bounds.endX);
    const startY = Math.max(0, bounds.startY);
    const endY = Math.min(SIZE - 1, bounds.endY);
    for (let y = startY; y <= endY; y++) {
        const rowOffset = y * SIZE;
        const worldY = y * CELL + (CELL * 0.5);
        for (let x = startX; x <= endX; x++) {
            const cell = grid[rowOffset + x];
            if (!cell || cell.contourId === 0 || !cell.type) continue;
            callback(cell, x, y, x * CELL + (CELL * 0.5), worldY);
        }
    }
}

const stoneSpriteCache = new Map();
function getStoneSprite(baseSize) {
    let sprite = stoneSpriteCache.get(baseSize);
    if (sprite) return sprite;

    if (DEBUG_SPRIE_CACHE_LOG) {
        console.log(`new STONE sprite | ${stoneSpriteCache.size+1} total`)
    }

    const canvas = (typeof OffscreenCanvas !== "undefined")
        ? new OffscreenCanvas(baseSize, baseSize)
        : document.createElement("canvas");

    canvas.width = baseSize;
    canvas.height = baseSize;

    const ctx = canvas.getContext("2d");
    ctx.fillStyle = "#1d1d1d";
    ctx.fillRect(0, 0, baseSize, baseSize);

    stoneSpriteCache.set(baseSize, canvas);
    return canvas;
}

const coloredSpriteCache = new Map();
function getMaxZoomPointSprite(playerId, typeId) {
    let playerCache = coloredSpriteCache.get(playerId);
    if (!playerCache) {
        playerCache = new Map();
        coloredSpriteCache.set(playerId, playerCache);
    }
    
    if (playerCache.has(typeId)) return playerCache.get(typeId);

    if (DEBUG_SPRIE_CACHE_LOG){
        console.log(`new maxzoom-POINT sprite | ${coloredSpriteCache.size+1} total`)
    }
    

    const size = CELL;
    const canvas = (typeof OffscreenCanvas !== "undefined") 
        ? new OffscreenCanvas(size, size) 
        : document.createElement("canvas");

    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext("2d");

    if (typeId === TYPE_T2DOT) {
        
        ctx.fillStyle = getPlayerCustomColor(playerId, 1);
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(size, 0);
        ctx.lineTo(size, size);
        ctx.closePath();
        ctx.fill();

        ctx.fillStyle = "white";;
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(0, size);
        ctx.lineTo(size, size);
        ctx.closePath();
        ctx.fill();
    } else {
        ctx.fillStyle = getPlayerCustomColor(playerId, 1);
        ctx.fillRect(0, 0, size, size);
    }
    
    playerCache.set(typeId, canvas);
    return canvas;
}

const TYPE_STONE = "Stone";
const TYPE_DOT = "Dot";
const TYPE_T2DOT = "T2Dot";
const PI2 = Math.PI * 2;

function drawCircle(ctx, center, radius, fillStyle, strokeStyle, lineWidth) {
    ctx.beginPath();
    ctx.arc(center, center, radius, 0, PI2);
    if (fillStyle) {
        ctx.fillStyle = fillStyle;
        ctx.fill();
    }
    if (strokeStyle) {
        ctx.strokeStyle = strokeStyle;
        ctx.lineWidth = lineWidth;
        ctx.stroke();
    }
}

const pointSpriteCache = new Map();
function getPointSprite(playerId, typeId) {
    let playerCache = pointSpriteCache.get(playerId);
    if (!playerCache) {
        playerCache = new Map();
        pointSpriteCache.set(playerId, playerCache);
    }
    
    if (playerCache.has(typeId)) return playerCache.get(typeId);

    if (DEBUG_SPRIE_CACHE_LOG){
        console.log(`new POINT sprite | ${pointSpriteCache.size+1} total`)
    }

    const size = CELL;
    const canvas = (typeof OffscreenCanvas !== "undefined") 
        ? new OffscreenCanvas(size, size) 
        : document.createElement("canvas");

    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext("2d");
    const center = size / 2;
    const baseRadius = CELL * 0.15;

    if (animationsEnabled) {
        const radii = GLOW_CONFIG.pointRadii;
        const alphas = GLOW_CONFIG.alpha;
        for (let i = 0; i < 4; i++) {
            drawCircle(ctx, center, baseRadius * radii[i], getPlayerCustomColor(playerId, alphas[i]));
            if (typeId === TYPE_T2DOT) {
                drawCircle(ctx, center, baseRadius * radii[i] * 2, null, `rgba(255, 255, 255, ${alphas[i] * 0.5})`, 1);
            }
        }
    } else {
        drawCircle(ctx, center, baseRadius, getPlayerCustomColor(playerId, 1));
        if (typeId === TYPE_T2DOT) {
            drawCircle(ctx, center, baseRadius * 2, null, "white", 3);
        }
    }

    playerCache.set(typeId, canvas);
    return canvas;
}

function drawScene(target = ctx, bounds) {
    const cellSize = Math.ceil(CELL * zoom);
    const halfSize = cellSize * 0.5;
    
    const stoneSprite = getStoneSprite(CELL);

    const getPointSpriteStrategy = (zoom > 0.15) 
        ? getPointSprite 
        : getMaxZoomPointSprite;

    forEachVisiblePoint(bounds, (cell, x, y, worldX, worldY) => {
        const screenX = (worldX * zoom + offsetX) - halfSize;
        const screenY = (worldY * zoom + offsetY) - halfSize;

        const typeId = cell.type?.id;

        if (typeId === TYPE_STONE) {
            target.drawImage(stoneSprite, screenX, screenY, cellSize, cellSize);
        } 
        else if (typeId === "Dot" || typeId === "T2Dot") {
            
            const sprite = getPointSpriteStrategy(
                cell.playerId, 
                (typeId === "T2Dot") ? TYPE_T2DOT : TYPE_DOT
            );
            target.drawImage(sprite, screenX, screenY, cellSize, cellSize);
        }
    });
}

const signSpriteCache = new Map();

function getSignSprite(text, fontSize) {
    const key = `${text}_${fontSize}`;

    if (signSpriteCache.has(key)) return signSpriteCache.get(key);

    if (DEBUG_SPRIE_CACHE_LOG) {
        console.log(`new SIGN sprite | ${signSpriteCache.size+1} total`)
    }

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
    const halfCell = CELL * 0.5;
    const fontSize = 48;
    const scale = zoom * 0.5;            

    for (let y = bounds.startY; y <= bounds.endY; y++) {
        if (y < 0 || y >= SIZE) continue;
        for (let x = bounds.startX; x <= bounds.endX; x++) {
            if (x < 0 || x >= SIZE) continue;

            const index = y * SIZE + x;
            const cell = grid[index];

            if (!cell || cell.type?.id !== "Sign") continue;

            const isTooSmall = zoom < 0.15;
            const text = isTooSmall ? "🪧" : cell.type.data;
            const currentScale = isTooSmall ? (scale * 8) : scale;
            
            const sprite = getSignSprite(text, fontSize);

            const worldX = x * CELL + halfCell;
            const worldY = y * CELL + halfCell;
            const screen = worldToScreen(worldX, worldY);            

            const scaledWidth = sprite.width * currentScale;
            const scaledHeight = sprite.height * currentScale;

            target.drawImage(
                sprite,
                screen.x - scaledWidth * 0.5,
                screen.y - scaledHeight * 0.5,
                scaledWidth,
                scaledHeight
            );
        }
    }
}

function drawMinimap() {
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

    let index = 0;
    for (let y = 0; y < SIZE; y++) {
        for (let x = 0; x < SIZE; x++) {
            const cell = grid[index++];

            if (!cell || cell.contourId === 0 || cell.contourId === -2 || cell.contourId === -1) continue;
            
            let color;
            if (cell.playerId === 0) {
                color = { r: 29, g: 29, b: 29 };
            } else {
                color = getPlayerCustomRGB(cell.playerId);
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
    mctx.lineWidth = 2;
    mctx.strokeRect(viewLeft, viewTop, viewWidth, viewHeight);
}

function renderMinimapHighlights(ctx) {
    ctx.clearRect(0, 0, SIZE, SIZE);

    minimapHighlights.forEach(h => {
        const pulse = 1 + Math.sin(h.life * 50) * 0.5;
        const size = h.radius * pulse;

        ctx.save();
        ctx.globalAlpha = h.life;
        ctx.strokeStyle = h.color;
        ctx.lineWidth = 5;

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
    decaySpeed = 0.00015 // дефолт
) {
    const color = getPlayerCustomColor(player_id)

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

    const cell = grid?.[hoveredCellY * SIZE + hoveredCellX];    
    const contourId = Number(cell.contourId);

    if (contourId === 0) return;

    if (cell?.playerId || cell.contourId === -1){
        let text = ''
        if (contourId > 0){
            const ownerId = cell.playerId;
            if (ownerId === window.currentPlayer) return;
            
            playerName = getPlayerCustomNickname(ownerId);
            if (!playerName) { getPlayerName(ownerId); }
            
            text = `Точка ${playerName}`;
            target.strokeStyle = getPlayerCustomColor(ownerId, 0.5);

        } else if (cell.contourId === -1){
            
            text = `Текст: ${cell.type.data}`;
            target.strokeStyle = "#ffffff";
        } else if (cell.contourId === -2){            
            return;
        }

        target.font = "bold 13px monospace";
        const textWidth = target.measureText(text).width;
        const rectWidth = textWidth + 20;
        const rectHeight = 32;

        const screen = worldToScreen(hoveredCellX * CELL + CELL / 2, hoveredCellY * CELL + CELL / 2);
        const rectX = screen.x - rectWidth / 2;
        const rectY = screen.y - rectHeight - (CELL * 0.2 * zoom); 

        target.fillStyle = "rgba(0, 0, 0, 0.75)";
        
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
}

// unused
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
    
    const color = getPlayerCustomColor(player_id);

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
            color: getPlayerCustomColor(playerId),
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

    target.strokeStyle = getPlayerCustomColor(playerId, a);
    target.lineWidth = (2 * zoom) * (1 - i * 0.1);

    target.stroke();
}

function drawExplosions(target = fxCtx) {
    for (const e of explosions) {

        const screen = worldToScreen(
            e.x * CELL + CELL * 0.5,
            e.y * CELL + CELL * 0.5
        );

        const t = e.t;
        const flash = Math.max(0, 1 - t / 0.2);
        const waveT = Math.min(1, Math.max(0, (t - 0.1) / 0.7));
        const decayT = Math.max(0, (t - 0.5) / 1.0);
        const baseRadius = e.radius * CELL;

        target.beginPath();
        target.arc(screen.x, screen.y, baseRadius * 0.4 * flash, 0, Math.PI * 2);
        target.fillStyle = getPlayerCustomColor(e.playerId, flash * 0.8);
        target.fill();

        const waveRadius = baseRadius * (0.3 + waveT * 2.2);

        target.beginPath();
        target.arc(screen.x, screen.y, waveRadius, 0, Math.PI * 2);
        target.strokeStyle = getPlayerCustomColor(e.playerId, (1 - waveT) * 0.6);
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

            target.strokeStyle = getPlayerCustomColor(
                e.playerId,
                (0.3 - i * 0.05) * (1 - decayT)
            );

            target.lineWidth = (3 - i * 0.5) * zoom;
            target.stroke();
        }

        target.beginPath();
        target.arc(screen.x, screen.y, waveRadius * 0.2, 0, Math.PI * 2);
        target.fillStyle = getPlayerCustomColor(e.playerId, 0.25 * (1 - decayT));
        target.fill();
    }
}

let leaderboardCache = new Map();
let lastLeaderboardOrder = [];
function renderLeaderboard() {
    const leaderboardEl = document.getElementById("leaderboard");

    const currentOrder = serverLeaderboard.map(p => p.playerId);
    const hasOrderChanged = JSON.stringify(currentOrder) !== JSON.stringify(lastLeaderboardOrder);

    if (hasOrderChanged && lastLeaderboardOrder.length > 0) {
        addChatMessage('Топ игроков изменился', 'info', 7500);
        triggerAnimation("leaderboard", "basic-flash");        
    }

    lastLeaderboardOrder = currentOrder;

    const current_player_id = window.currentPlayer

    leaderboardEl.innerHTML = serverLeaderboard.map((player, index) => {
        const player_id = player.playerId
        const player_color = getPlayerCustomColor(player_id)
        const player_name = getPlayerCustomNickname(player_id)

        return `
            <div class="leader-item" style="display: flex; flex-direction: column; gap: 2px; white-space: nowrap; padding-right: 10px; ${player_id === current_player_id ? 'text-decoration: underline;' : ''}">
                <div class="leader-row" style="display: flex; justify-content: flex-start; align-items: center; gap: 8px;">
                    <span style="font-size: 14px; font-weight: bold;">#${index + 1}</span>
                    <span class="player-color-dot" style="background: ${player_color}; width: 10px; height: 10px; flex-shrink: 0;"></span>
                    <span style="font-size: 14px; font-weight: bold;">
                        ${player_name} ${player_id === current_player_id ? '(Вы)' : ''}
                    </span>
                </div>
                <div style="font-size: 11px; color: rgba(255,255,255,0.6); padding-left: 44px;">
                    площадь: ${player.totalArea.toFixed(1)}
                </div>
            </div>
        `;
    }).join("");
}
function updateLeaderboardCache() {
    leaderboardCache.clear();
    for (const player of serverLeaderboard) {
        leaderboardCache.set(player.playerId, player);
    }
}
function getPlayerName(id) {
    return leaderboardCache.get(id)?.name ?? id;
}
function getPlayerCustomNickname(id) {
    const player = leaderboardCache.get(id);
    return player?.nickname || player?.name || id;
}
function getPlayerOldNickname(id) {
    const player = leaderboardCache.get(id);
    return player?.name || player?.nickname || id;
}
const customColorCache = new Map();
function getPlayerCustomColor(id, alpha = 1.0) {
    const hue = leaderboardCache.get(id)?.hue ?? id;
    if (hue >= 0) {
        const key = `${hue}:${alpha}`;

        let color = customColorCache.get(key);
        if (!color) {
            color = `hsla(${hue}, 65%, 45%, ${alpha})`;
            customColorCache.set(key, color);
        }

        return color;
    } else {
        return colorFor(id, alpha);
    }
}
function getPlayerCustomRGB(id) {
    const hue = leaderboardCache.get(id)?.hue ?? id;
    if (hue >= 0) {
        const key = `${id}:${hue}`;

        let color = customColorCache.get(key);
        if (!color) {
            color = hslToRgb(hue, 65, 45);
            customColorCache.set(key, color);
        }

        return color;        
    } else {
        return getStableRGB(id);
    }
}
function getPlayerCustomHue(id, alpha = 1.0) {
    const hue = leaderboardCache.get(id)?.hue ?? id;
    if (hue >= 0) { 
        return hue;
    } else {        
        return getStableHue(id);
    }
}


function redrawWorld() {    
    worldCtx.setTransform(1, 0, 0, 1, 0, 0);
    worldCtx.clearRect(0, 0, worldCanvas.width, worldCanvas.height);

    const bounds = getVisibleBounds();
    if (DEBUG_PROFILER_RENDER) {
        measure("Render | Grid", () => drawGrid(worldCtx, bounds));        
        measure("Render | Scene (cell)", () => drawScene(worldCtx, bounds));
        measure("Render | Contours", () => {
            Object.values(serverContours).forEach(c => drawServerContour(worldCtx, bounds, c));
        });
        measure("Render | Signs", () => drawSigns(worldCtx, bounds));
    } else {
        drawGrid(worldCtx, bounds);
        drawScene(worldCtx, bounds);
        Object.values(serverContours).forEach(c => drawServerContour(worldCtx, bounds, c));
        drawSigns(worldCtx, bounds);
    }
}

function render() {
    if (grid.length > 0) {
        ctx.clearRect(0,0,canvas.width,canvas.height);

        if (worldDirty) {  
            redrawWorld();
            worldDirty = false;   
        }

        ctx.save();
        ctx.drawImage(worldCanvas,0,0);
        ctx.restore();

        drawMinimap();
    }
}

function fxRender(target = fxCtx) {
    target.setTransform(1,0,0,1,0,0);
    target.globalAlpha = 1;
    target.clearRect(0, 0, fxCanvas.width, fxCanvas.height);

    if (DEBUG_PROFILER_FX) {
        if (gridSweeps.length > 0) {
            measure("FX | Grid Sweep", () => drawGridSweep(target));
        }    
        if (particles.length > 0) {
            measure("FX | Particles", () => drawParticles(target));
        }
        if (gridEvents.length > 0) {
            measure("FX | Grid Events", () => drawGridEvents(target));
        }
        if (explosions.length > 0) {
            measure("FX | Explosions", () => drawExplosions(target)); 
        }
        measure("FX | Hover Tooltip", () => drawHoverTooltip(target));
    } else {
         if (gridSweeps.length > 0) {
            drawGridSweep(target);
        }    
        if (particles.length > 0) {
            drawParticles(target);
        }
        if (gridEvents.length > 0) {
            drawGridEvents(target);
        }
        if (explosions.length > 0) {
            drawExplosions(target); 
        }
        drawHoverTooltip(target)
    }  
    // unused
    // measure("FX | Floating Texts", () => drawFloatingTexts(target), DEBUG_PROFILER_FX);
}

function mapExtraRender(target = mFxCtx) {
    if (DEBUG_PROFILER_MAP){
        measure("Minimap | Highlights", () => renderMinimapHighlights(target), );
    } else {
        renderMinimapHighlights(target);
    }    
}

function measure(name, fn) {    
    const t = performance.now();
    fn();
    const dt = performance.now() - t;
    
    if (dt > 0.50) {
        console.log(name, dt.toFixed(2));
    }
    if (dt > 0.25) {
        console.log(`${name}: ${dt.toFixed(2)} ms`);
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
            if (DEBUG_PROFILER_UPDATE) {
                if (particles.length > 0) {
                measure("UPD | Particles", () => updateParticles(dt));
                }                      
                if (explosions.length > 0) {
                    measure("UPD | Explosions", () => updateExplosions(dt)); 
                }             
                if (gridEvents.length > 0) {
                    measure("UPD | Grid Events", () => updateGridEvents(dt));
                }          
                if (gridSweeps.length > 0) {
                    measure("UPD | Grid Sweep", () => updateGridSweep(dt));
                }
                if (minimapHighlights.length > 0) {
                    measure("UPD | Highlights", () => updateHighlights(dt));
                }
            } else {
                if (particles.length > 0) {
                    updateParticles(dt);
                }                      
                if (explosions.length > 0) {
                    updateExplosions(dt); 
                }             
                if (gridEvents.length > 0) {
                    updateGridEvents(dt);
                }          
                if (gridSweeps.length > 0) {
                    updateGridSweep(dt);
                }
                if (minimapHighlights.length > 0) {
                    updateHighlights(dt);
                }
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
    syncButton(btnTier2Blast, c.tier2blast, "Взрыв Ур.2");
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
        updateCooldownUI()
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

function changeZoom(zoomIn) {
    const scaleFactor = 1.2;
    const multiplier = zoomIn ? scaleFactor : 1 / scaleFactor;
    const targetZoom = Number((zoom * multiplier).toFixed(2));    
    const nextZoom = Math.min(Math.max(targetZoom, maxZoom), minZoom);

    if (nextZoom === zoom) {
        return;
    }

    const centerX = window.innerWidth / 2;
    const centerY = window.innerHeight / 2;
    
    const worldX = (centerX - offsetX) / zoom;
    const worldY = (centerY - offsetY) / zoom;
    
    zoom = nextZoom;
    
    offsetX = centerX - worldX * zoom;
    offsetY = centerY - worldY * zoom;

    debouncedSave();
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
    const rect = canvas.getBoundingClientRect();
    const clientX = e.clientX - rect.left;
    const clientY = e.clientY - rect.top;

    if (isDragging) {
        const deltaX = clientX - lastMouseX;
        const deltaY = clientY - lastMouseY;

        offsetX += deltaX;
        offsetY += deltaY;

        if (!hasMoved && Math.hypot(clientX - mouseStartX, clientY - mouseStartY) > 5) {
            hasMoved = true;
        }

        lastMouseX = clientX;
        lastMouseY = clientY;

        worldDirty = true;
        requestRender();
    } else {
        const x = Math.floor(((clientX - offsetX) / zoom) / CELL);
        const y = Math.floor(((clientY - offsetY) / zoom) / CELL);
        
        const inWorld = inBounds(x, y);
        hoveredCellX = inWorld ? x : -1;
        hoveredCellY = inWorld ? y : -1;
    }
});

window.addEventListener("mouseup", (e) => {
    if (isDragging) {
        isDragging = false;
        debouncedSave();
        if (!hasMoved) {
            processClick(e);
            requestRender();
        }
    }
});
canvas.addEventListener("mouseleave", () => { hoveredCellX = -1; hoveredCellY = -1; });

canvas.addEventListener("wheel", (e) => {
    e.preventDefault();

    const scaleFactor = 1.2;
    const multiplier = e.deltaY < 0 ? scaleFactor : 1 / scaleFactor;

    const targetZoom = Number((zoom * multiplier).toFixed(2));
    const nextZoom = Math.min(Math.max(targetZoom, maxZoom), minZoom);

    if (nextZoom === zoom) return;

    const mouseX = e.clientX;
    const mouseY = e.clientY;
    
    const worldX = (mouseX - offsetX) / zoom;
    const worldY = (mouseY - offsetY) / zoom;
    
    zoom = nextZoom;
    
    offsetX = mouseX - worldX * zoom;
    offsetY = mouseY - worldY * zoom;

    debouncedSave();
    worldDirty = true;
    requestRender();
}, { passive: false });

window.addEventListener("keydown", (e) => {
    const key = e.key.toLowerCase();    

    if (key === "escape" || key === "esc") {
        closeSign();
        closeAudioSettings();
        closePersonalSettings();
    } 

    if (!signActive) { 
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
            changeZoom(false);
        } else if (key === "pageup" || key === "-" ){
            changeZoom(true);
        // } else if (key === "p" || key === "з") {        
        //     toggleAnimations(); 
        // } else if (key === "o" || key === "щ") {
        //     openAudioSettings();
        }
        // else  {
        //    console.log(key)
        // }
    }
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
            debouncedSave();
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

    const index = y * SIZE + x;
    const cell = grid[index];
    const now = Date.now();

    if (!canUseTool(currentTool, pData, cell, now, x, y)) {
        return;
    }

    if (currentTool === 'sign') {
        signActive = true;
        pendingSignCoords = { x, y };
        document.getElementById('sign-modal').style.display = 'flex';
        return;
    }

    const worldX = x * CELL + CELL / 2;
    const worldY = y * CELL + CELL / 2;

    createExplosion(worldX, worldY, window.currentPlayer);

    if (socket.readyState === WebSocket.OPEN) {
        sendProto("action", {
            tool: currentTool,
            x: x,
            y: y            
        });
    } else {
        alert("Нет интернета или сервер оффлайн");
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
            if (cell.type != null && cell.type.id !== "") {
                messageWithFlash('Здесь чем-то занято');
                return false;
            }
            break;

        case "draw":
        case "tier2draw":
            if (cell.contourId !== 0) {
                messageWithFlash('Здесь уже занято');
                return false;
            }
            break;

        case "structure":
            if (cell.contourId !== 0) {
                messageWithFlash('Можно строить только на пустом');
                return false;
            }
            break;

        case "erase":
        case "tier2erase":
            if (cell.contourId === 0 || (cell.type?.id === "Stone")) {
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
            if (cell.contourId === 0) {
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
            sendProto("action", {
                data: text,
                tool: currentTool,
                x: x,
                y: y            
            });
        } else {
            alert("Нет интернета или сервер оффлайн");
        }
        
        createExplosion(x * CELL + CELL / 2, y * CELL + CELL / 2, window.currentPlayer);
    } else {
        addChatMessage('Что-то не так с текстом таблички')
    }

    closeSign();
}

function closeSign() {
    signActive = false
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
    saveToolState()    
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

    debouncedSave();
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
updateAnimation();
startFXLoop();
setInterval(updateCooldownUI, 300);
connect();