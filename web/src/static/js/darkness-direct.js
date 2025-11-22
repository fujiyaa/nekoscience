const params = new URLSearchParams(location.search);
const id = params.get("id");
const set_id = params.get("set_id");
const box = document.getElementById("content");

if (!id) {
    const title = "400";
    document.title = title;
    box.innerHTML = `
    <h1>${title}</h1>
    <p>Отсутствует ID карты.</p>
    <small>Пример правильного URL: <code>index.html?id=727727&set_id=12345</code></small>
    `;
} else if (!/^\d+$/.test(id)) {
    const title = "422";
    document.title = title;
    box.innerHTML = `
    <h1>${title}</h1>
    <p>Неправильный ID карты.</p>
    <small>Пример правильного URL: <code>index.html?id=727727&set_id=12345</code></small>
    `;
} else {
    const title = "Переадресация...";
    document.title = title;

    const pageUrl = set_id 
    ? `https://osu.ppy.sh/beatmapsets/${set_id}` 
    : `https://osu.ppy.sh/beatmapsets/${id}`; 

    box.innerHTML = `
    <h1>${title}</h1>
    <div class="buttons">
        <a class="button" href="osu://b/${id}">Открыть ещё раз</a>
        <a class="button" href="${pageUrl}">Страница на сайте</a>
    </div>
    <small>Если ничего не происходит, osu!direct не настроен.</small>
    `;

    setTimeout(() => {
    try {
        location.replace("osu://b/" + id);
    } catch (e) {}
    }, 50);
}

