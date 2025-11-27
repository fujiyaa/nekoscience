(function() {
    const footer = document.createElement('footer');
    footer.id = 'footer';
    footer.style.cssText = `
        text-align: center;
        padding: 1rem 0;
        background: rgba(42, 42, 60, 0);
        color: #a8caff;
        font-size: 0.9rem;
        width: 100%;
        margin-top: auto; /* отталкиваем от контента */
    `;

    const linksDiv = document.createElement('div');
    linksDiv.className = 'footer-links';
    linksDiv.innerHTML = `
        <a href="/dashboard">Status</a> | 
        <a href="https://github.com/fujiyaa/nekoscience">Github</a> | 
        <a href="https://t.me/fujiyaosu">Телеграм чат</a>
    `;

    const style = document.createElement('style');
    style.innerHTML = `
        #footer a {
            color: #a8caff;
            text-decoration: none;
            transition: all 0.3s;
        }
        #footer a:hover {
            color: #ffffff;
            text-decoration: underline;
        }
        body {
            display: flex;
            flex-direction: column;
            min-height: 100vh;
            margin: 0;
        }
    `;
    document.head.appendChild(style);

    footer.appendChild(linksDiv);
    document.body.appendChild(footer);
})();
