 (function() {
            // Настройки
            const SNOWFLAKE_COUNT = 80;
            const SNOWFLAKE_MIN_SPEED = 0.3;
            const SNOWFLAKE_MAX_SPEED = 0.5;
            const SNOWFLAKE_RADIUS = 5.0;
            const ACCUMULATION_LIMIT = 20;

            // Основной холст
            const canvas = document.createElement('canvas');
            canvas.id = 'snowCanvas';
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

            const snowLayer = document.createElement('canvas');
            const snowCtx = snowLayer.getContext('2d');
            snowLayer.width = w;
            snowLayer.height = h;

            let accumulation = new Array(w).fill(0);

            let snowflakes = [];
            for (let i = 0; i < SNOWFLAKE_COUNT; i++) {
                const speed = SNOWFLAKE_MIN_SPEED + Math.random() * (SNOWFLAKE_MAX_SPEED - SNOWFLAKE_MIN_SPEED);

                snowflakes.push({
                    x: Math.random() * w,
                    y: Math.random() * h,
                    speed: speed,
                    radius: SNOWFLAKE_RADIUS * (speed / SNOWFLAKE_MAX_SPEED),
                    drift: 0
                });
            }


            let mouseX = 0;
            let lastMouseX = 0;

            //window.addEventListener('mousemove', e => {
            //    mouseX = e.clientX;
            //});

            window.addEventListener('resize', () => {
                w = canvas.width = window.innerWidth;
                h = canvas.height = window.innerHeight;

                snowLayer.width = w;
                snowLayer.height = h;

                accumulation = new Array(w).fill(0);
                updateSnowLayer();
            });


            function updateSnowLayer() {
                snowCtx.clearRect(0, 0, w, h);
                snowCtx.fillStyle = 'rgba(255,255,255,0.7)';
                snowCtx.beginPath();

                for (let i = 0; i < w; i++) {
                    let height = accumulation[i];
                    if (height > 0) {
                        snowCtx.rect(i, h - height, 1, height);
                    }
                }

                snowCtx.fill();
            }

            function drawSnow() {
                // if (!snowEnabled) {
                //     requestAnimationFrame(drawSnow);
                //     return;
                // }

                ctx.clearRect(0, 0, w, h);

                let deltaX = mouseX - lastMouseX;

                snowflakes.forEach(flake => {
                    flake.drift = -deltaX * 0.05;

                    let idx = Math.floor(flake.x);
                    if (idx < 0) idx = 0;
                    if (idx >= w) idx = w - 1;

                    let normalizedY = flake.y / (h - accumulation[idx]);
                    normalizedY = Math.min(1, normalizedY);

                    let minSpeedFactor = 0.3;
                    let speedFactor = minSpeedFactor + (1 - minSpeedFactor) * Math.exp(-3 * normalizedY);
                    let vy = flake.speed * speedFactor;

                    flake.x += flake.drift;
                    flake.y += vy;

                    if (flake.x < 0) flake.x += w;
                    if (flake.x > w) flake.x -= w;

                    if (flake.y >= h - accumulation[idx]) {
                        accumulation[idx] = Math.min(accumulation[idx] + 0.7, ACCUMULATION_LIMIT);
                        if (idx > 0) accumulation[idx - 1] = Math.min(accumulation[idx - 1] + 0.3, ACCUMULATION_LIMIT);
                        if (idx < w - 1) accumulation[idx + 1] = Math.min(accumulation[idx + 1] + 0.3, ACCUMULATION_LIMIT);

                        updateSnowLayer();
                        flake.y = 0;
                        flake.x = Math.random() * w;
                    }

                    ctx.beginPath();
                    ctx.arc(flake.x, flake.y, flake.radius, 0, Math.PI * 2);
                    ctx.fillStyle = 'rgba(255,255,255,0.8)';
                    ctx.fill();
                });

                ctx.drawImage(snowLayer, 0, 0);

                lastMouseX = mouseX;
                requestAnimationFrame(drawSnow);
            }

            drawSnow();


})();