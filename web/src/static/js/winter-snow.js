//  (function() {
//             // Настройки
//             const SNOWFLAKE_COUNT = 80;
//             const SNOWFLAKE_MIN_SPEED = 0.3;
//             const SNOWFLAKE_MAX_SPEED = 0.5;
//             const SNOWFLAKE_RADIUS = 5.0;
//             const ACCUMULATION_LIMIT = 20;

//             // Основной холст
//             const canvas = document.createElement('canvas');
//             canvas.id = 'snowCanvas';
//             document.body.appendChild(canvas);

//             Object.assign(canvas.style, {
//                 position: 'fixed',
//                 top: '0',
//                 left: '0',
//                 width: '100%',
//                 height: '100%',
//                 pointerEvents: 'none',
//                 zIndex: '0'
//             });
//             const ctx = canvas.getContext('2d');
//             let w = canvas.width = window.innerWidth;
//             let h = canvas.height = window.innerHeight;

//             const snowLayer = document.createElement('canvas');
//             const snowCtx = snowLayer.getContext('2d');
//             snowLayer.width = w;
//             snowLayer.height = h;

//             let accumulation = new Array(w).fill(0);

//             let snowflakes = [];
//             for (let i = 0; i < SNOWFLAKE_COUNT; i++) {
//                 const speed = SNOWFLAKE_MIN_SPEED + Math.random() * (SNOWFLAKE_MAX_SPEED - SNOWFLAKE_MIN_SPEED);

//                 snowflakes.push({
//                     x: Math.random() * w,
//                     y: Math.random() * h,
//                     speed: speed,
//                     radius: SNOWFLAKE_RADIUS * (speed / SNOWFLAKE_MAX_SPEED),
//                     drift: 0
//                 });
//             }


//             let mouseX = 0;
//             let lastMouseX = 0;

//             //window.addEventListener('mousemove', e => {
//             //    mouseX = e.clientX;
//             //});

//             window.addEventListener('resize', () => {
//                 w = canvas.width = window.innerWidth;
//                 h = canvas.height = window.innerHeight;

//                 snowLayer.width = w;
//                 snowLayer.height = h;

//                 accumulation = new Array(w).fill(0);
//                 updateSnowLayer();
//             });


//             function updateSnowLayer() {
//                 snowCtx.clearRect(0, 0, w, h);
//                 snowCtx.fillStyle = 'rgba(255,255,255,0.7)';
//                 snowCtx.beginPath();

//                 for (let i = 0; i < w; i++) {
//                     let height = accumulation[i];
//                     if (height > 0) {
//                         snowCtx.rect(i, h - height, 1, height);
//                     }
//                 }

//                 snowCtx.fill();
//             }

//             function drawSnow() {
//                 // if (!snowEnabled) {
//                 //     requestAnimationFrame(drawSnow);
//                 //     return;
//                 // }

//                 ctx.clearRect(0, 0, w, h);

//                 let deltaX = mouseX - lastMouseX;

//                 snowflakes.forEach(flake => {
//                     flake.drift = -deltaX * 0.05;

//                     let idx = Math.floor(flake.x);
//                     if (idx < 0) idx = 0;
//                     if (idx >= w) idx = w - 1;

//                     let normalizedY = flake.y / (h - accumulation[idx]);
//                     normalizedY = Math.min(1, normalizedY);

//                     let minSpeedFactor = 0.3;
//                     let speedFactor = minSpeedFactor + (1 - minSpeedFactor) * Math.exp(-3 * normalizedY);
//                     let vy = flake.speed * speedFactor;

//                     flake.x += flake.drift;
//                     flake.y += vy;

//                     if (flake.x < 0) flake.x += w;
//                     if (flake.x > w) flake.x -= w;

//                     if (flake.y >= h - accumulation[idx]) {
//                         accumulation[idx] = Math.min(accumulation[idx] + 0.7, ACCUMULATION_LIMIT);
//                         if (idx > 0) accumulation[idx - 1] = Math.min(accumulation[idx - 1] + 0.3, ACCUMULATION_LIMIT);
//                         if (idx < w - 1) accumulation[idx + 1] = Math.min(accumulation[idx + 1] + 0.3, ACCUMULATION_LIMIT);

//                         updateSnowLayer();
//                         flake.y = 0;
//                         flake.x = Math.random() * w;
//                     }

//                     ctx.beginPath();
//                     ctx.arc(flake.x, flake.y, flake.radius, 0, Math.PI * 2);
//                     ctx.fillStyle = 'rgba(255,255,255,0.8)';
//                     ctx.fill();
//                 });

//                 ctx.drawImage(snowLayer, 0, 0);

//                 lastMouseX = mouseX;
//                 requestAnimationFrame(drawSnow);
//             }

//             drawSnow();


// })();

(function() {
            const SNOWFLAKE_COUNT = 80;
            const SNOWFLAKE_MAX_SPEED = 0.003;
            const SNOWFLAKE_MIN_SPEED = 0.002;
            const SNOWFLAKE_SIZE_MAX =50;
            const SNOWFLAKE_SIZE_MIN = 4;
            const SIZE_BIAS = 0.5; // типа насколько чаще мелкие да
            const DRIFT_AMOUNT = 0.0005;
            const SPEED_FALLOFF = 0.7;
            const DRIFT_FALLOFF = 1.0;

            const canvas = document.createElement('canvas');
            canvas.id = 'snowGL';
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

            const gl = canvas.getContext('webgl', { alpha: true });
            if (!gl) return console.error('WebGL');

            gl.enable(gl.BLEND);
            gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);

            function resize() {
                canvas.width = window.innerWidth;
                canvas.height = window.innerHeight;
                gl.viewport(0, 0, gl.drawingBufferWidth, gl.drawingBufferHeight);
            }
            resize();
            window.addEventListener('resize', resize);

            const vertexShaderSource = `
                attribute vec2 a_position;
                attribute float a_pointSize;
                void main() {
                    gl_PointSize = a_pointSize;
                    gl_Position = vec4(a_position, 0.0, 1.0);
                }
            `;

            const fragmentShaderSource = `
                precision mediump float;

                uniform float u_opacity;
                uniform float u_edgeSoftness;
                uniform float u_rimStrength;
                uniform float u_centerFade;
                uniform float u_time;

                void main() {
                    vec2 uv = gl_PointCoord * 2.0 - 1.0;

                    float baseDist = length(uv);

                    float n1 = sin(uv.x * 6.0 + u_time) *
                            sin(uv.y * 6.0 + u_time * 1.3);

                    float n2 = sin(uv.x * 14.0 - u_time * 0.7) *
                            sin(uv.y * 14.0 + u_time);

                    float noise = (n1 * 0.7 + n2 * 0.3);

                    noise *= smoothstep(0.3, 1.0, baseDist);
                    noise *= 0.03;

                    float dist = baseDist + noise;

                    if (dist > 1.0) discard;

                    float alpha = smoothstep(u_centerFade, 1.0, dist) * u_opacity;
                    float edge = smoothstep(1.0, u_edgeSoftness, dist);

                    vec3 base = vec3(0.5, 0.75, 1.0);

                    vec3 iridescent = vec3(
                        0.5 + 0.5 * sin(u_time + dist * 8.0),
                        0.5 + 0.5 * sin(u_time + dist * 8.0 + 2.0),
                        0.5 + 0.5 * sin(u_time + dist * 8.0 + 4.0)
                    );

                    vec3 color = mix(base, iridescent, 0.4);

                    float rim = smoothstep(0.7, 1.0, dist);
                    color += rim * u_rimStrength;

                    gl_FragColor = vec4(color * edge, alpha);
                }
            `;

            function createShader(type, source) {
                const shader = gl.createShader(type);
                gl.shaderSource(shader, source);
                gl.compileShader(shader);
                if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
                    console.error(gl.getShaderInfoLog(shader));
                }
                return shader;
            }

            const vertexShader = createShader(gl.VERTEX_SHADER, vertexShaderSource);
            const fragmentShader = createShader(gl.FRAGMENT_SHADER, fragmentShaderSource);

            const program = gl.createProgram();
            gl.attachShader(program, vertexShader);
            gl.attachShader(program, fragmentShader);
            gl.linkProgram(program);

            if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
                console.error(gl.getProgramInfoLog(program));
            }

            gl.useProgram(program);

            const uOpacity = gl.getUniformLocation(program, "u_opacity");
            const uEdgeSoftness = gl.getUniformLocation(program, "u_edgeSoftness");
            const uRimStrength = gl.getUniformLocation(program, "u_rimStrength");
            const uCenterFade = gl.getUniformLocation(program, "u_centerFade");
            const uTime = gl.getUniformLocation(program, "u_time");

            gl.uniform1f(uOpacity, 0.6);
            gl.uniform1f(uEdgeSoftness, 0.75);
            gl.uniform1f(uRimStrength, 0.6);
            gl.uniform1f(uCenterFade, 0.35);

            const positionBuffer = gl.createBuffer();
            const sizeBuffer = gl.createBuffer();

            const aPosition = gl.getAttribLocation(program, 'a_position');
            const aPointSize = gl.getAttribLocation(program, 'a_pointSize');

            let snowflakes = [];

            for (let i = 0; i < SNOWFLAKE_COUNT; i++) {
                let t;

                if (Math.random() < 0.1) {
                    t = Math.random() < 0.5 ? 0.0 : 1.0;
                } else {
                    t = 1.0 - Math.pow(Math.random(), SIZE_BIAS);
                }

                const size = SNOWFLAKE_SIZE_MIN +
                      t * (SNOWFLAKE_SIZE_MAX - SNOWFLAKE_SIZE_MIN);

                const speed = SNOWFLAKE_MIN_SPEED +
                      (size - SNOWFLAKE_SIZE_MIN) /
                      (SNOWFLAKE_SIZE_MAX - SNOWFLAKE_SIZE_MIN) *
                      (SNOWFLAKE_MAX_SPEED - SNOWFLAKE_MIN_SPEED);

                const driftDirection = Math.random() < 0.5 ? -1 : 1;
                const driftStrength = 0.7 + Math.random() * 0.3;

                snowflakes.push({
                    x: Math.random() * 2 - 1,
                    y: Math.random() * 4 - 1,
                    size,
                    speed,
                    driftDirection,
                    driftStrength
                });
            }

            const positions = new Float32Array(SNOWFLAKE_COUNT * 2);
            const sizes = new Float32Array(SNOWFLAKE_COUNT);

            snowflakes.forEach((f, i) => {
                positions[i * 2] = f.x;
                positions[i * 2 + 1] = f.y;
                sizes[i] = f.size;
            });

            gl.bindBuffer(gl.ARRAY_BUFFER, sizeBuffer);
            gl.bufferData(gl.ARRAY_BUFFER, sizes, gl.STATIC_DRAW);
            gl.enableVertexAttribArray(aPointSize);
            gl.vertexAttribPointer(aPointSize, 1, gl.FLOAT, false, 0, 0);

            const SIN_STEPS = 16;
            const sinTable = new Float32Array(SIN_STEPS);
            for (let i = 0; i < SIN_STEPS; i++) {
                sinTable[i] = Math.sin((i / (SIN_STEPS - 1)) * (Math.PI / 2));
            }

            function sinApprox(value) {
                const idx = Math.floor(value * (SIN_STEPS - 1));
                return sinTable[idx];
            }

            let lastTime = 0;
            const targetFPS = 60;
            const frameDuration = 1000 / targetFPS;

            function draw(timestamp) {
                if (timestamp - lastTime < frameDuration) {
                    requestAnimationFrame(draw);
                    return;
                }
                lastTime = timestamp;

                gl.clear(gl.COLOR_BUFFER_BIT);
                gl.uniform1f(uTime, timestamp * 0.001);

                snowflakes.forEach((f, i) => {
                    let normalizedY = (1 - (f.y + 1) / 2);
                    let speedFactor = Math.max(1 - SPEED_FALLOFF * normalizedY, 0.1);
                    f.y -= f.speed * speedFactor;

                    let driftFactor = (1 - normalizedY) * (1 - DRIFT_FALLOFF) + DRIFT_FALLOFF;

                    f.x += sinApprox(1 - normalizedY) *
                        DRIFT_AMOUNT *
                        driftFactor *
                        f.driftStrength *
                        f.driftDirection *
                        Math.random();

                    if (f.x < -1) f.x += 2;
                    else if (f.x > 1) f.x -= 2;

                    if (f.y < -1) {
                        f.y = 1;
                        f.x = Math.random() * 2 - 1;
                    }

                    positions[i * 2] = f.x;
                    positions[i * 2 + 1] = f.y;
                });

                gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
                gl.bufferData(gl.ARRAY_BUFFER, positions, gl.DYNAMIC_DRAW);
                gl.enableVertexAttribArray(aPosition);
                gl.vertexAttribPointer(aPosition, 2, gl.FLOAT, false, 0, 0);

                gl.drawArrays(gl.POINTS, 0, SNOWFLAKE_COUNT);

                requestAnimationFrame(draw);
            }

            gl.clearColor(0, 0, 0, 0);
            draw(0);
        })();