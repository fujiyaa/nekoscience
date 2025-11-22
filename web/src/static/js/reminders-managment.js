let user = "";
const MAX_REMINDERS = 10;

async function login() {
    const password = document.getElementById("password").value.trim();
    if (!password) { alert("Введите пароль"); return; }

    const res = await fetch("/darkness/reminders/password", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({password})
    });

    if (res.ok) {
    const data = await res.json();
    user = data.user; 
    document.getElementById("loginSection").style.display = "none";
    document.getElementById("formSection").style.display = "block";
    } else {
    const err = await res.json();
    alert(err.detail || "Ошибка входа");
    }
}

async function saveReminder() {
    const message = document.getElementById('message').value.trim();
    const date = document.getElementById('date').value;
    const time = document.getElementById('time').value;
    const repeatCount = document.getElementById('repeatCount').value;

    if (!message || !date || !time) { 
        alert('Заполните все поля'); 
        return; 
    }

    const resList = await fetch(`/darkness/reminders/list?user=${encodeURIComponent(user)}`);
    const currentReminders = await resList.json();

    if (currentReminders.length >= MAX_REMINDERS) {
        alert(`Превышено максимальное количество ${MAX_REMINDERS} напоминаний для одного пользователя`);
        return;
    }

    const reminder = { user, message, date, time, repeatCount: Number(repeatCount) };

    const res = await fetch('/darkness/reminders/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(reminder)
    });

    const result = await res.json();
    if (res.ok) {
        alert(result.message);
        loadReminders();
    } else {
        alert(result.detail || "Ошибка при сохранении");
    }
}

async function loadReminders() {
    const res = await fetch(`/darkness/reminders/list?user=${encodeURIComponent(user)}`);
    const reminders = await res.json();
    const list = document.getElementById('reminderList');
    list.innerHTML = "";

    reminders.forEach(r => {
    const li = document.createElement('li');
    const reminderDate = new Date(`${r.date}T${r.time}`);
    const now = new Date();
    if (reminderDate < now) {
        li.style.background = 'linear-gradient(135deg, #442222, #663333)';
    }

    li.textContent = `"${r.message}" — ${r.date} ${r.time} (${r.repeatCount} раз)`;

    const delBtn = document.createElement('button');
    delBtn.textContent = '❌';
    delBtn.className = 'deleteBtn';
    delBtn.onclick = async () => {
        if (!confirm("Удалить это напоминание?")) return;
        const delRes = await fetch(`/darkness/reminders/delete?user=${encodeURIComponent(r.user)}&message=${encodeURIComponent(r.message)}&date=${r.date}&time=${r.time}`, {
        method: 'DELETE'
        });
        if (delRes.ok) loadReminders();
        else {
        const err = await delRes.json();
        alert(err.detail || "Ошибка при удалении");
        }
    };

    li.appendChild(delBtn);
    list.appendChild(li);
    });

    document.getElementById('listSection').style.display = reminders.length ? 'block' : 'none';
}