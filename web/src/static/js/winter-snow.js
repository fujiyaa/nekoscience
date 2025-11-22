(function() {
    const canvas = document.createElement('canvas');
    canvas.id = 'snow-canvas';
    document.body.appendChild(canvas);

    Object.assign(canvas.style, {
        position: 'fixed',
        top: '0',
        left: '0',
        width: '100%',
        height: '100%',
        pointerEvents: 'none', 
        zIndex: '0'
    });

    const ctx = canvas.getContext('2d');

    let w = canvas.width = window.innerWidth;
    let h = canvas.height = window.innerHeight;

    const snowflakes = [];
    const maxFlakes = 100;
    const accumulation = new Array(w).fill(0);

    for (let i = 0; i < maxFlakes; i++) {
        snowflakes.push({
            x: Math.random() * w,
            y: Math.random() * h,
            radius: 2 + Math.random() * 3,
            speed: 0.2 + Math.random() * 0.2,
            drift: 0
        });
    }

    let lastMouseX = w / 2;
    let mouseX = w / 2;

    window.addEventListener('mousemove', e => { mouseX = e.clientX; });

    window.addEventListener('resize', () => {
        w = canvas.width = window.innerWidth;
        h = canvas.height = window.innerHeight;
        if(accumulation.length < w){
            accumulation.length = w;
            for(let i=0;i<w;i++) accumulation[i] = accumulation[i] || 0;
        }
    });

    function drawSnow() {
        ctx.clearRect(0, 0, w, h);
        let deltaX = mouseX - lastMouseX;

        snowflakes.forEach(flake => {
            flake.drift = -deltaX * 0.05;

            let idx = Math.floor(flake.x);
            if(idx < 0) idx = 0;
            if(idx >= w) idx = w-1;

            let normalizedY = flake.y / (h - accumulation[idx]);
            if(normalizedY > 1) normalizedY = 1;
            let minSpeedFactor = 0.3;
            let speedFactor = minSpeedFactor + (1 - minSpeedFactor) * Math.exp(-3 * normalizedY);
            let vy = flake.speed * speedFactor;

            flake.x += flake.drift;
            flake.y += vy;

            if(flake.x < 0) flake.x += w;
            if(flake.x > w) flake.x -= w;

            if(flake.y >= h - accumulation[idx]) {
                accumulation[idx] += 0.7;
                if(idx > 0) accumulation[idx-1] += 0.3;
                if(idx < w-1) accumulation[idx+1] += 0.3;
                flake.y = 0;
                flake.x = Math.random() * w;
            }

            ctx.beginPath();
            ctx.arc(flake.x, flake.y, flake.radius, 0, Math.PI*2);
            ctx.fillStyle = 'rgba(255,255,255,0.8)';
            ctx.fill();
        });

        ctx.fillStyle = 'rgba(255,255,255,0.7)';
        for(let i=0;i<w;i++){
            if(accumulation[i] > 0){
                ctx.fillRect(i, h - accumulation[i], 5, accumulation[i]);
            }
        }

        lastMouseX = mouseX;
        requestAnimationFrame(drawSnow);
    }

    drawSnow();

})();
