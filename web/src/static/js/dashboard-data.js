const colors = ["#4bc0c0", "#ff9f40", "#9966ff"];
let statsData = {};
let charts = {}; // Храним все графики Chart.js

async function fetchData(period = "day") {
    try {
        const res = await fetch(`/api/data?period=${period}`);
        if (!res.ok) throw new Error("Не удалось получить данные с сервера");
        const json = await res.json();
        return json;
    } catch (err) {
        console.error(err);
        return null;
    }
}

// Загружаем JSON
async function loadStatsJSON() {
    try {
        const res = await fetch('/static/data/bot_stats.json');
        if (!res.ok) throw new Error('Не удалось загрузить JSON');
        statsData = await res.json();
    } catch (err) {
        console.error('Ошибка при загрузке JSON:', err);
    }
}

// Создание datasets для Chart.js
function makeDataset(type, dataObj, labels) {
    const datasets = [];
    for (const [key, values] of Object.entries(dataObj)) {
        datasets.push({
            label: key,
            data: values,
            borderColor: colors[datasets.length % colors.length],
            backgroundColor: colors[datasets.length % colors.length],
            tension: 0.3,
            fill: type === "line",
        });
    }
    return { labels, datasets };
}

// Создание/обновление графика
function createChart(ctxId, type, labels, dataObj) {
    if (charts[ctxId]) charts[ctxId].destroy();
    const ctx = document.getElementById(ctxId).getContext("2d");
    const data = makeDataset(type, dataObj, labels);
    charts[ctxId] = new Chart(ctx, {
        type,
        data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: "#a8caff" } },
                tooltip: { mode: 'index', intersect: false }
            },
            scales: {
                x: { ticks: { color: "#a8caff" }, grid: { color: 'rgba(255,255,255,0.1)' } },
                y: { ticks: { color: "#a8caff" }, grid: { color: 'rgba(255,255,255,0.1)' } }
            }
        }
    });
}

function updatePieCommands(stats) {
    const commandsTotal = Object.values(stats.command_map || {})
        .reduce((sum, key) => sum + (stats.chart.data[key]?.reduce((a,b)=>a+b,0)||0), 0);
    const messagesTotal = stats.total_requests;
    const others = messagesTotal - commandsTotal;

    const ctx = document.getElementById("pie_commands").getContext("2d");

    if (charts["pie_commands"]) {
        charts["pie_commands"].data.datasets[0].data = [commandsTotal, others];
        charts["pie_commands"].update();
    } else {
        charts["pie_commands"] = new Chart(ctx, {
            type: "pie",
            data: { labels: ["Команды", "Остальные сообщения"], datasets: [{ data: [commandsTotal, others], backgroundColor: ["#4bc0c0", "#ff9f40"] }] },
            options: { responsive: true, plugins: { legend: { labels: { color: "#a8caff" } } } }
        });
    }
}

function updatePieCacheRandom() {
    const random1 = Math.floor(Math.random() * 100);
    const random2 = Math.floor(Math.random() * 100);
    const random3 = Math.floor(Math.random() * 100);
    const random4 = Math.floor(Math.random() * 100);
    
    const ctx = document.getElementById("pie_cache").getContext("2d");

    if (charts["pie_cache"]) {
        charts["pie_cache"].data.datasets[0].data = [random1, random2, random3, random4];
        charts["pie_cache"].update();
    } else {
        charts["pie_cache"] = new Chart(ctx, {
            type: "doughnut",
            data: {
                labels: ["Кэш 1", "Кэш 2", "Кэш 3", "Кэш 4"],
                datasets: [{
                    data: [random1, random2, random3, random4],
                    backgroundColor: ["#4bc0c0", "#ecff40ff", "#ffc340ff", "#40ff53ff"]
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { labels: { color: "#a8caff" } }
                }
            }
        });
    }
}

function updateLineCommandsRandom() {
    const ctx = document.getElementById("line_commands_err").getContext("2d");
    if (charts["line_commands_err"]) charts["line_commands_err"].destroy();

    // Пусть будет 5 "команд" и 10 точек на графике
    const commands = ["cmd1", "cmd2", "cmd3", "cmd4", "cmd5"];
    const labels = Array.from({ length: 10 }, (_, i) => `T${i+1}`);

    const datasets = commands.map((cmd, i) => ({
        label: cmd,
        data: labels.map(() => Math.floor(Math.random() * 100)), // случайные значения
        borderColor: colors[i % colors.length],
        backgroundColor: colors[i % colors.length],
        fill: false,
        tension: 0.3
    }));

    charts["line_commands_err"] = new Chart(ctx, {
        type: "line",
        data: { labels, datasets },
        options: {
            responsive: true,
            plugins: {
                legend: { labels: { color: "#a8caff" } }
            },
            scales: {
                x: { ticks: { color: "#a8caff" } },
                y: { ticks: { color: "#a8caff" } }
            }
        }
    });
}




function updateLineCommands(stats) {
    const ctx = document.getElementById("line_commands").getContext("2d");
    if (charts["line_commands"]) charts["line_commands"].destroy();

    const datasets = Object.entries(stats.command_map || {}).map(([cmd, key], i) => ({
        label: cmd,
        data: stats.chart.data[key] || [],
        borderColor: colors[i % colors.length],
        backgroundColor: colors[i % colors.length],
        fill: false,
        tension: 0.3
    }));

    charts["line_commands"] = new Chart(ctx, {
        type: "line",
        data: { labels: stats.chart.labels, datasets },
        options: {
            responsive: true,
            plugins: { legend: { labels: { color: "#a8caff" } } },
            scales: { x: { ticks: { color: "#a8caff" } }, y: { ticks: { color: "#a8caff" } } }
        }
    });
}

function updateBarUsers(stats) {
    const ctx = document.getElementById("bar_users").getContext("2d");
    if (charts["bar_users"]) charts["bar_users"].destroy();

    const datasets = Object.entries(stats.user_map || {}).map(([username, key], i) => ({
        label: username,
        data: stats.chart.data[key] || [],
        backgroundColor: colors[i % colors.length],
        borderColor: colors[i % colors.length],
        borderWidth: 1
    }));

    charts["bar_users"] = new Chart(ctx, {
        type: "bar",
        data: {
            labels: stats.chart.labels,
            datasets
        },
        options: {
            responsive: true,
            plugins: { legend: { labels: { color: "#a8caff" } } },
            scales: { x: { ticks: { color: "#a8caff" } }, y: { ticks: { color: "#a8caff" } } }
        }
    });
}




// Обновляем карточки
function renderCards(stats) {
    document.getElementById('total-requests').textContent = stats.total_requests;
    document.getElementById('commands').textContent = stats.commands;
    document.getElementById('users').textContent = stats.users;
    document.getElementById('chats').textContent = stats.chats;
  
}

async function renderMainCards(period) {
    const data = await fetchData(period);
    if (!data) return;

    const s = data.all_stats;
    const cards = document.getElementById("cards"); 
    cards.innerHTML = `
        <div class="card"><h3>API</h3>
            <p>${s.avg_value}</p>
        </div> 
        <div class="card"><h3>Warnings</h3>
            <p>${s.warns}</p>
        </div> 
        <div class="card"><h3>Errors</h3>
            <p>${s.errors}</p>
        </div> 
        <div class="card"><h3>Uptime</h3>
            <p>${s.uptime}</p>
        </div>
    `;
}

async function updateAllFromJSON(period) {
    const d = statsData[period];

    await renderMainCards(period);
    renderCards(d);
    updatePieCommands(d);
    updatePieCacheRandom();
    updateLineCommands(d);
    createChart("bar_messages", "bar", d.chart.labels, { "Сообщения": d.chart.data.data_total });
    updateBarUsers(d);
    updateLineCommandsRandom();
}



// Инициализация
async function init() {
    await loadStatsJSON();
    const defaultPeriod = document.getElementById('range').value;
    updateAllFromJSON(defaultPeriod);

    // обновление при смене периода
    document.getElementById('range').addEventListener('change', e => {
        updateAllFromJSON(e.target.value);
    });
}

// старт
init();