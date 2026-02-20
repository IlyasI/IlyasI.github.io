// main.js — ilyasi.com
// Zero dependencies. Vanilla ES6.
// Particle simulation adapted from Florian Cordillot (CodePen: ZaGgRy)

(() => {
    'use strict';

    const startTime = Date.now();

    // ─── Console ──────────────────────────────────────────────

    console.log(
        '%cilyasi.com %cv3.0',
        'background:#38bdf8;color:#0a0e18;padding:3px 8px;border-radius:3px 0 0 3px;font-weight:bold;font-family:monospace;',
        'background:#1e293b;color:#cbd5e1;padding:3px 8px;border-radius:0 3px 3px 0;font-family:monospace;'
    );
    console.log('');
    console.log('%cBuild Info', 'font-weight:bold;color:#38bdf8;font-family:monospace;');
    console.log('  Runtime deps:  0');
    console.log('  Framework:     none');
    console.log('  Bundler:       n/a');
    console.log('  CSS-in-JS:     absolutely not');
    console.log('  Particles:     200');
    console.log('');
    console.log('%cContact', 'font-weight:bold;color:#38bdf8;font-family:monospace;');
    console.log('  ilyas.ibragimov@outlook.com');

    // ─── Typing Animation ─────────────────────────────────────

    const typedEl = document.getElementById('typed-title');
    const phrase = 'Senior Software Developer';
    let charIdx = 0;

    function typeNext() {
        if (charIdx <= phrase.length) {
            typedEl.textContent = phrase.slice(0, charIdx);
            charIdx++;
            setTimeout(typeNext, 40 + Math.random() * 60);
        }
    }

    setTimeout(typeNext, 600);

    // ─── Scroll Progress ──────────────────────────────────────

    const progressBar = document.querySelector('.scroll-progress');

    function updateProgress() {
        const h = document.documentElement.scrollHeight - window.innerHeight;
        progressBar.style.transform = `scaleX(${h > 0 ? window.scrollY / h : 0})`;
    }

    // ─── Navigation ───────────────────────────────────────────

    const nav = document.querySelector('.nav');
    const navLinks = document.querySelectorAll('.nav-links a[href^="#"]');
    const sections = document.querySelectorAll('.section');

    function updateNav() {
        nav.classList.toggle('nav-scrolled', window.scrollY > 80);
    }

    const sectionObs = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const id = entry.target.id;
                navLinks.forEach(link => {
                    link.classList.toggle('active', link.getAttribute('href') === `#${id}`);
                });
            }
        });
    }, { rootMargin: '-40% 0px -60% 0px' });

    sections.forEach(s => sectionObs.observe(s));

    // ─── Scroll Reveal ────────────────────────────────────────

    const revealObs = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) entry.target.classList.add('revealed');
        });
    }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });

    document.querySelectorAll('.reveal').forEach(el => revealObs.observe(el));

    // ─── Scroll Events ────────────────────────────────────────

    let ticking = false;
    window.addEventListener('scroll', () => {
        if (!ticking) {
            requestAnimationFrame(() => {
                updateProgress();
                updateNav();
                ticking = false;
            });
            ticking = true;
        }
    }, { passive: true });

    // ─── 3D Card Tilt ─────────────────────────────────────────

    document.querySelectorAll('[data-tilt]').forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const cx = rect.width / 2;
            const cy = rect.height / 2;
            const rx = ((e.clientY - rect.top - cy) / cy) * -3;
            const ry = ((e.clientX - rect.left - cx) / cx) * 3;
            card.style.transform = `perspective(600px) rotateX(${rx}deg) rotateY(${ry}deg) translateY(-2px)`;
        });
        card.addEventListener('mouseleave', () => {
            card.style.transform = '';
        });
    });

    // ─── Market Hours Accent ──────────────────────────────────

    try {
        const ny = new Date(new Date().toLocaleString('en-US', { timeZone: 'America/New_York' }));
        const day = ny.getDay();
        const mins = ny.getHours() * 60 + ny.getMinutes();
        const open = day >= 1 && day <= 5 && mins >= 570 && mins < 960;
        document.documentElement.style.setProperty('--accent', open ? '#38bdf8' : '#60a5fa');
    } catch { /* timezone API unavailable */ }

    // ─── Theme Toggle ───────────────────────────────────────────

    const themeToggle = document.getElementById('theme-toggle');
    themeToggle.addEventListener('click', () => {
        const isLight = document.documentElement.hasAttribute('data-theme');
        if (isLight) {
            document.documentElement.removeAttribute('data-theme');
        } else {
            document.documentElement.setAttribute('data-theme', 'light');
        }
    });

    // ─── Interactive Terminal ──────────────────────────────────

    const terminal = document.getElementById('terminal');
    const terminalHeader = document.querySelector('.terminal-header');
    const terminalInput = document.getElementById('terminal-input');
    const terminalOutput = document.getElementById('terminal-output');
    const terminalBody = document.getElementById('terminal-body');
    const terminalClose = document.getElementById('terminal-close');
    const terminalTrigger = document.getElementById('terminal-trigger');
    let termOpen = false;
    const cmdHistory = [];
    let historyIdx = -1;

    function openTerminal() {
        if (termOpen) return;
        termOpen = true;
        terminal.classList.add('open');
        terminalTrigger.classList.add('hidden');
        terminalInput.focus();
        if (!terminalOutput.innerHTML) {
            printLine('<span class="cmd-dim">ilyasi.com — interactive terminal</span>');
            printLine('<span class="cmd-dim">Type</span> <span class="cmd-accent">help</span> <span class="cmd-dim">for commands. Drag the title bar to move.</span>\n');
        }
        // Force obstacle recalc so particles flow around terminal
        lastObstacleScroll = -999;
    }

    function closeTerminal() {
        if (!termOpen) return;
        termOpen = false;
        terminal.classList.remove('open');
        terminalTrigger.classList.remove('hidden');
        lastObstacleScroll = -999;
    }

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && termOpen) {
            closeTerminal();
        }
    });

    terminalClose.addEventListener('click', closeTerminal);
    terminalTrigger.addEventListener('click', openTerminal);

    // Dot buttons: red=close, yellow=minimize, green=maximize
    const dots = document.querySelectorAll('.terminal-dots span');
    dots[0].addEventListener('click', (e) => { e.stopPropagation(); closeTerminal(); });
    dots[1].addEventListener('click', (e) => { e.stopPropagation(); terminal.classList.toggle('minimized'); terminal.classList.remove('maximized'); });
    dots[2].addEventListener('click', (e) => { e.stopPropagation(); terminal.classList.toggle('maximized'); terminal.classList.remove('minimized'); });

    // ─── Terminal Dragging ────────────────────────────────────

    let isDragging = false;
    let dragOffsetX = 0;
    let dragOffsetY = 0;

    terminalHeader.addEventListener('mousedown', (e) => {
        // Don't drag if clicking buttons
        if (e.target.closest('.terminal-close') || e.target.closest('.terminal-dots')) return;
        isDragging = true;
        const rect = terminal.getBoundingClientRect();
        dragOffsetX = e.clientX - rect.left;
        dragOffsetY = e.clientY - rect.top;
        terminal.style.transition = 'none';
        e.preventDefault();
    });

    document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        let x = e.clientX - dragOffsetX;
        let y = e.clientY - dragOffsetY;

        // Clamp to viewport
        const tw = terminal.offsetWidth;
        const th = terminal.offsetHeight;
        x = Math.max(0, Math.min(x, window.innerWidth - tw));
        y = Math.max(0, Math.min(y, window.innerHeight - th));

        terminal.style.left = x + 'px';
        terminal.style.top = y + 'px';
        terminal.style.right = 'auto';
        terminal.style.bottom = 'auto';

        // Update obstacles since terminal moved
        lastObstacleScroll = -999;
    });

    document.addEventListener('mouseup', () => {
        if (isDragging) {
            isDragging = false;
            terminal.style.transition = '';
        }
    });

    // Touch dragging
    terminalHeader.addEventListener('touchstart', (e) => {
        if (e.target.closest('.terminal-close') || e.target.closest('.terminal-dots')) return;
        isDragging = true;
        const rect = terminal.getBoundingClientRect();
        const touch = e.touches[0];
        dragOffsetX = touch.clientX - rect.left;
        dragOffsetY = touch.clientY - rect.top;
        terminal.style.transition = 'none';
    }, { passive: true });

    document.addEventListener('touchmove', (e) => {
        if (!isDragging) return;
        const touch = e.touches[0];
        let x = touch.clientX - dragOffsetX;
        let y = touch.clientY - dragOffsetY;
        const tw = terminal.offsetWidth;
        const th = terminal.offsetHeight;
        x = Math.max(0, Math.min(x, window.innerWidth - tw));
        y = Math.max(0, Math.min(y, window.innerHeight - th));
        terminal.style.left = x + 'px';
        terminal.style.top = y + 'px';
        terminal.style.right = 'auto';
        terminal.style.bottom = 'auto';
        lastObstacleScroll = -999;
    }, { passive: true });

    document.addEventListener('touchend', () => {
        if (isDragging) {
            isDragging = false;
            terminal.style.transition = '';
        }
    });

    // ─── Terminal Input ───────────────────────────────────────

    const knownCommands = ['help', 'whoami', 'experience', 'skills', 'education', 'contact', 'resume', 'neofetch', 'theme', 'particles', 'accent', 'gravity', 'matrix', 'speed', 'reset', 'clear', 'exit'];

    terminalInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            const cmd = terminalInput.value.trim();
            terminalInput.value = '';
            if (cmd) {
                cmdHistory.unshift(cmd);
                historyIdx = -1;
            }
            printLine(`<span class="cmd-green">visitor@ilyasi.com:~$</span> <span class="cmd-text">${escapeHtml(cmd)}</span>`);
            handleCommand(cmd.toLowerCase());
            terminalBody.scrollTop = terminalBody.scrollHeight;
        }
        if (e.key === 'ArrowUp') {
            e.preventDefault();
            if (historyIdx < cmdHistory.length - 1) {
                historyIdx++;
                terminalInput.value = cmdHistory[historyIdx];
            }
        }
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            if (historyIdx > 0) {
                historyIdx--;
                terminalInput.value = cmdHistory[historyIdx];
            } else {
                historyIdx = -1;
                terminalInput.value = '';
            }
        }
        // Tab completion
        if (e.key === 'Tab') {
            e.preventDefault();
            const partial = terminalInput.value.trim().toLowerCase();
            if (partial) {
                const matches = knownCommands.filter(c => c.startsWith(partial));
                if (matches.length === 1) {
                    terminalInput.value = matches[0];
                } else if (matches.length > 1) {
                    printLine(`<span class="cmd-green">visitor@ilyasi.com:~$</span> <span class="cmd-text">${escapeHtml(partial)}</span>`);
                    printLine('<span class="cmd-dim">' + matches.join('  ') + '</span>');
                    terminalBody.scrollTop = terminalBody.scrollHeight;
                }
            }
        }
    });

    // Click anywhere on terminal body to focus input
    terminalBody.addEventListener('click', () => {
        terminalInput.focus();
    });

    function printLine(html) {
        terminalOutput.innerHTML += html + '\n';
    }

    function escapeHtml(str) {
        return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    function formatUptime() {
        const s = Math.floor((Date.now() - startTime) / 1000);
        if (s < 60) return `${s}s`;
        const m = Math.floor(s / 60);
        if (m < 60) return `${m}m ${s % 60}s`;
        const h = Math.floor(m / 60);
        return `${h}h ${m % 60}m`;
    }

    function handleCommand(cmd) {
        const commands = {
            help() {
                printLine(`
<span class="cmd-accent">Commands:</span>

  <span class="cmd-text">whoami</span>              <span class="cmd-dim">About me</span>
  <span class="cmd-text">experience</span>          <span class="cmd-dim">Work history</span>
  <span class="cmd-text">projects</span>            <span class="cmd-dim">Side projects</span>
  <span class="cmd-text">skills</span>              <span class="cmd-dim">Technical skills</span>
  <span class="cmd-text">education</span>           <span class="cmd-dim">Education</span>
  <span class="cmd-text">contact</span>             <span class="cmd-dim">Get in touch</span>
  <span class="cmd-text">resume</span>              <span class="cmd-dim">Download resume</span>
  <span class="cmd-text">neofetch</span>            <span class="cmd-dim">System info</span>

<span class="cmd-accent">Site controls:</span>

  <span class="cmd-text">theme light|dark</span>    <span class="cmd-dim">Switch color scheme</span>
  <span class="cmd-text">accent [color]</span>      <span class="cmd-dim">blue green red orange purple pink</span>
  <span class="cmd-text">particles [n]</span>       <span class="cmd-dim">Set count (50–8000) or off|on</span>
  <span class="cmd-text">gravity</span>             <span class="cmd-dim">Toggle particle gravity</span>
  <span class="cmd-text">matrix</span>              <span class="cmd-dim">Toggle matrix rain mode</span>
  <span class="cmd-text">speed [0.5–3]</span>       <span class="cmd-dim">Simulation speed multiplier</span>
  <span class="cmd-text">reset</span>               <span class="cmd-dim">Reset all visual changes</span>
  <span class="cmd-text">clear</span>               <span class="cmd-dim">Clear terminal</span>
  <span class="cmd-text">exit</span>                <span class="cmd-dim">Close terminal</span>

<span class="cmd-dim">Tab to autocomplete. Arrow keys for history.</span>`);
            },

            whoami() {
                printLine(`
<span class="cmd-accent">Ilyas Ibragimov</span>
Senior Software Developer

6+ years building platform infrastructure and
trading systems in financial technology.
LLM-native engineer.

Currently at <span class="cmd-text">Two Sigma</span> (via Randstad Digital).

<span class="cmd-dim">ilyas.ibragimov@outlook.com</span>`);
            },

            experience() {
                printLine(`
<span class="cmd-accent">Two Sigma</span>           Senior Software Developer
<span class="cmd-dim">via Randstad Digital   Nov 2022 — Present · New York, NY</span>
  ELT pipelines · dbt · BigQuery · 15+ TB/day
  LLM-powered tools · Claude · Vertex AI
  Sole backend eng on $80MM+ cost platform

<span class="cmd-accent">Blueshift AM</span>        Software Developer
<span class="cmd-dim">                      Jan 2020 — Nov 2022 · Red Bank, NJ</span>
  C++ trading platform · Portfolio analytics
  Exchange integrations · Compliance systems

<span class="cmd-accent">Fidessa</span>             Platform Dev Intern
<span class="cmd-dim">                      Jul — Sep 2018 · Woking, UK</span>
  Secure file transmission · Java/JS`);
            },

            skills() {
                printLine(`
<span class="cmd-accent">Languages</span>      Python · SQL · C++ · Bash · JavaScript
<span class="cmd-accent">Data</span>           dbt · BigQuery · PostgreSQL · ELT Pipelines
<span class="cmd-accent">Cloud</span>          GCP · AWS · Docker · GitHub Actions · Linux
<span class="cmd-accent">AI/LLM</span>         Claude Code · Claude API · MCP Servers
<span class="cmd-accent">Tools</span>          Git · Datadog · Jira · REST APIs
<span class="cmd-accent">Frameworks</span>     Flask · Django · Playwright · Selenium`);
            },

            education() {
                printLine(`
<span class="cmd-accent">UCL</span>              MEng Electronic & Electrical   <span class="cmd-dim">2019</span>
                 First Class Honors (4.0 GPA)

<span class="cmd-accent">Baruch College</span>   C++ Financial Engineering      <span class="cmd-dim">2020</span>
                 Certificate, Distinction

<span class="cmd-accent">Brooklyn Tech</span>    Mathematics                    <span class="cmd-dim">2015</span>
                 4.0 GPA`);
            },

            contact() {
                printLine(`
<span class="cmd-accent">Email</span>      <a href="mailto:ilyas.ibragimov@outlook.com" style="color:var(--text-primary)">ilyas.ibragimov@outlook.com</a>
<span class="cmd-accent">GitHub</span>     <a href="https://github.com/IlyasI" target="_blank" rel="noopener" style="color:var(--text-primary)">github.com/IlyasI</a>
<span class="cmd-accent">LinkedIn</span>   <a href="https://www.linkedin.com/in/ilyasi" target="_blank" rel="noopener" style="color:var(--text-primary)">linkedin.com/in/ilyasi</a>
<span class="cmd-accent">Resume</span>     <a href="resume.pdf" download="IlyasIbragimov-Resume.pdf" style="color:var(--text-primary)">Download resume.pdf</a>`);
            },

            projects() {
                printLine(`
<span class="cmd-accent">ilyasi.com</span>                                  <span class="cmd-dim">2026</span>
  Personal portfolio · Vanilla JS · Zero runtime deps
  Canvas particle sim · Interactive terminal · 33 tests
  <a href="https://github.com/IlyasI/IlyasI.github.io" target="_blank" rel="noopener" style="color:var(--accent-dim)">github.com/IlyasI/IlyasI.github.io</a>

<span class="cmd-accent">Network Packet Routing with Deep RL</span>         <span class="cmd-dim">2019</span>
  MEng Thesis · UCL · First Class Honors
  Deep RL models for SDN routing · Python · TensorFlow

<span class="cmd-accent">Deep Learning for Cryptocurrency Trading</span>    <span class="cmd-dim">2018</span>
  BEng Thesis · UCL · First Class Honors
  LSTM networks for return prediction · Keras`);
            },

            resume() {
                printLine('<span class="cmd-dim">Downloading resume...</span>');
                const a = document.createElement('a');
                a.href = 'resume.pdf';
                a.download = 'IlyasIbragimov-Resume.pdf';
                a.click();
            },

            neofetch() {
                const n = particles.length;
                const w = window.innerWidth;
                const h = window.innerHeight;
                const theme = document.documentElement.hasAttribute('data-theme') ? 'light' : 'dark';
                const modes = [matrixMode && 'matrix', gravityOn && 'gravity', simSpeed !== 1 && `speed:${simSpeed}x`].filter(Boolean).join(' · ') || 'default';
                printLine(`
<span class="cmd-green">  ilyas</span><span class="cmd-dim">@</span><span class="cmd-accent">ilyasi.com</span>
  <span class="cmd-dim">─────────────────────</span>
  <span class="cmd-accent">Role</span>          Senior Software Developer
  <span class="cmd-accent">Location</span>      New York, NY
  <span class="cmd-accent">Stack</span>         Vanilla JS · 0 runtime deps
  <span class="cmd-accent">Theme</span>         ${theme}
  <span class="cmd-accent">Particles</span>     ${n}
  <span class="cmd-accent">Mode</span>          ${modes}
  <span class="cmd-accent">Viewport</span>      ${w} x ${h}
  <span class="cmd-accent">Uptime</span>        ${formatUptime()}
  <span class="cmd-accent">Source</span>        github.com/IlyasI/IlyasI.github.io`);
            },

            clear() {
                terminalOutput.innerHTML = '';
            },

            exit() {
                closeTerminal();
            }
        };

        // Aliases
        commands.ls = commands.help;
        commands['cat skills'] = commands.skills;
        commands['cat experience'] = commands.experience;
        commands['cat education'] = commands.education;
        commands['cat contact'] = commands.contact;
        commands['cat projects'] = commands.projects;
        commands.about = commands.whoami;
        commands.close = commands.exit;
        commands.quit = commands.exit;

        if (!cmd) return;

        // Theme switching
        if (cmd === 'theme light') {
            document.documentElement.setAttribute('data-theme', 'light');
            printLine('<span class="cmd-dim">Switched to light theme.</span>');
            return;
        }
        if (cmd === 'theme dark') {
            document.documentElement.removeAttribute('data-theme');
            printLine('<span class="cmd-dim">Switched to dark theme.</span>');
            return;
        }
        if (cmd === 'theme') {
            const current = document.documentElement.hasAttribute('data-theme') ? 'light' : 'dark';
            printLine(`<span class="cmd-dim">Current theme:</span> <span class="cmd-text">${current}</span>\n<span class="cmd-dim">Usage: theme light | theme dark</span>`);
            return;
        }

        // Particle controls
        if (cmd === 'particles off') {
            canvas.style.display = 'none';
            printLine('<span class="cmd-dim">Particles disabled.</span>');
            return;
        }
        if (cmd === 'particles on') {
            canvas.style.display = '';
            printLine('<span class="cmd-dim">Particles enabled.</span>');
            return;
        }
        if (cmd.startsWith('particles ')) {
            const n = parseInt(cmd.split(' ')[1]);
            if (!isNaN(n) && n >= 50 && n <= 8000) {
                const w = canvas.width;
                const h = canvas.height;
                particles = [];
                for (let i = 0; i < n; i++) {
                    const x = Math.random() * w;
                    const y = Math.random() * h;
                    particles.push({ x, y, px: x, py: y, xv: 0, yv: 0 });
                }
                printLine(`<span class="cmd-dim">Particle count set to</span> <span class="cmd-text">${n}</span>`);
            } else {
                printLine('<span class="cmd-dim">Usage: particles [50–8000] | particles off | particles on</span>');
            }
            return;
        }
        if (cmd === 'particles') {
            printLine(`<span class="cmd-dim">Current count:</span> <span class="cmd-text">${particles.length}</span>\n<span class="cmd-dim">Usage: particles [50–8000] | particles off | particles on</span>`);
            return;
        }

        // Accent color
        const accentColors = {
            blue:   { accent: '#38bdf8', dim: '#2d8abf' },
            green:  { accent: '#4ade80', dim: '#22c55e' },
            red:    { accent: '#f87171', dim: '#dc2626' },
            orange: { accent: '#fb923c', dim: '#ea580c' },
            purple: { accent: '#c084fc', dim: '#9333ea' },
            pink:   { accent: '#f472b6', dim: '#db2777' }
        };
        if (cmd.startsWith('accent ')) {
            const color = cmd.split(' ')[1];
            if (accentColors[color]) {
                document.documentElement.style.setProperty('--accent', accentColors[color].accent);
                document.documentElement.style.setProperty('--accent-dim', accentColors[color].dim);
                printLine(`<span class="cmd-dim">Accent color set to</span> <span class="cmd-text">${color}</span>`);
            } else {
                printLine(`<span class="cmd-dim">Colors: ${Object.keys(accentColors).join(' · ')}</span>`);
            }
            return;
        }
        if (cmd === 'accent') {
            printLine(`<span class="cmd-dim">Usage: accent [color]</span>\n<span class="cmd-dim">Colors: ${Object.keys(accentColors).join(' · ')}</span>`);
            return;
        }

        // Gravity
        if (cmd === 'gravity') {
            gravityOn = !gravityOn;
            printLine(`<span class="cmd-dim">Gravity</span> <span class="cmd-text">${gravityOn ? 'on' : 'off'}</span>`);
            return;
        }

        // Matrix mode
        if (cmd === 'matrix') {
            matrixMode = !matrixMode;
            if (matrixMode) {
                gravityOn = true;
                document.documentElement.style.setProperty('--accent', '#00cc44');
                document.documentElement.style.setProperty('--accent-dim', '#009933');
                document.documentElement.style.setProperty('--green', '#00ff55');
            } else {
                gravityOn = false;
                document.documentElement.style.removeProperty('--accent');
                document.documentElement.style.removeProperty('--accent-dim');
                document.documentElement.style.removeProperty('--green');
            }
            printLine(`<span class="cmd-dim">Matrix mode</span> <span class="cmd-text">${matrixMode ? 'on' : 'off'}</span>`);
            return;
        }

        // Speed
        if (cmd.startsWith('speed ')) {
            const s = parseFloat(cmd.split(' ')[1]);
            if (!isNaN(s) && s >= 0.5 && s <= 3) {
                simSpeed = s;
                printLine(`<span class="cmd-dim">Simulation speed set to</span> <span class="cmd-text">${s}x</span>`);
            } else {
                printLine('<span class="cmd-dim">Usage: speed [0.5–3]</span>');
            }
            return;
        }
        if (cmd === 'speed') {
            printLine(`<span class="cmd-dim">Current speed:</span> <span class="cmd-text">${simSpeed}x</span>\n<span class="cmd-dim">Usage: speed [0.5–3]</span>`);
            return;
        }

        // Reset all visual changes
        if (cmd === 'reset') {
            gravityOn = false;
            matrixMode = false;
            simSpeed = 1;
            document.documentElement.removeAttribute('data-theme');
            document.documentElement.style.removeProperty('--accent');
            document.documentElement.style.removeProperty('--accent-dim');
            document.documentElement.style.removeProperty('--green');
            canvas.style.display = '';
            setup();
            printLine('<span class="cmd-dim">All visual settings reset to defaults.</span>');
            return;
        }

        const fn = commands[cmd];
        if (fn) {
            fn();
        } else {
            printLine(`<span class="cmd-dim">command not found: ${escapeHtml(cmd)}. Type</span> <span class="cmd-accent">help</span> <span class="cmd-dim">for available commands.</span>`);
        }
    }

    // ─── Obstacle Detection ───────────────────────────────────

    const obstacleEls = document.querySelectorAll('.hero-card, .glass-panel, .project-card');
    let obstacles = [];
    let lastObstacleScroll = -999;

    function updateObstacles() {
        const scaleX = canvas.width / window.innerWidth;
        const scaleY = canvas.height / window.innerHeight;
        const pad = 6;
        obstacles = [];

        obstacleEls.forEach(el => {
            const rect = el.getBoundingClientRect();
            if (rect.bottom > -50 && rect.top < window.innerHeight + 50) {
                obstacles.push({
                    left:   (rect.left - pad) * scaleX,
                    right:  (rect.right + pad) * scaleX,
                    top:    (rect.top - pad) * scaleY,
                    bottom: (rect.bottom + pad) * scaleY
                });
            }
        });

        // Terminal is also an obstacle when open
        if (termOpen) {
            const rect = terminal.getBoundingClientRect();
            obstacles.push({
                left:   (rect.left - pad) * scaleX,
                right:  (rect.right + pad) * scaleX,
                top:    (rect.top - pad) * scaleY,
                bottom: (rect.bottom + pad) * scaleY
            });
        }
    }

    // ─── Particle Simulation ──────────────────────────────────

    const canvas = document.getElementById('canvas');
    const ctx = canvas.getContext('2d');
    const mouse = { x: 0, y: 0, px: 0, py: 0, down: false };
    const RES = 20;
    const HOVER_PEN = 40;
    const CLICK_PEN = 55;
    const REPEL_MARGIN = 12;
    let cells = [];
    let particles = [];
    let numCols = 0;
    let numRows = 0;

    // Visual mode flags
    let gravityOn = false;
    let matrixMode = false;
    let simSpeed = 1;

    function setup() {
        const w = window.innerWidth;
        const h = window.innerHeight;
        canvas.width = Math.round(w / RES) * RES;
        canvas.height = Math.round(h / RES) * RES;
        numCols = canvas.width / RES;
        numRows = canvas.height / RES;

        const count = 200;
        particles = [];
        for (let i = 0; i < count; i++) {
            const x = Math.random() * canvas.width;
            const y = Math.random() * canvas.height;
            particles.push({ x, y, px: x, py: y, xv: 0, yv: 0 });
        }

        cells = [];
        for (let c = 0; c < numCols; c++) {
            cells[c] = [];
            for (let r = 0; r < numRows; r++) {
                cells[c][r] = { x: c * RES, y: r * RES, xv: 0, yv: 0, pressure: 0 };
            }
        }

        for (let c = 0; c < numCols; c++) {
            for (let r = 0; r < numRows; r++) {
                const cell = cells[c][r];
                const u = r > 0 ? r - 1 : numRows - 1;
                const d = r < numRows - 1 ? r + 1 : 0;
                const l = c > 0 ? c - 1 : numCols - 1;
                const rt = c < numCols - 1 ? c + 1 : 0;
                cell.up = cells[c][u];
                cell.down = cells[c][d];
                cell.left = cells[l][r];
                cell.right = cells[rt][r];
                cell.upLeft = cells[l][u];
                cell.upRight = cells[rt][u];
                cell.downLeft = cells[l][d];
                cell.downRight = cells[rt][d];
            }
        }

        updateObstacles();
    }

    function draw() {
        const sy = window.scrollY;
        if (Math.abs(sy - lastObstacleScroll) > 2) {
            updateObstacles();
            lastObstacleScroll = sy;
        }

        // Don't apply mouse physics when dragging the terminal
        const applyMouse = !isDragging;
        const mx = Math.min(mouse.x - mouse.px, 30);
        const my = Math.min(mouse.y - mouse.py, 30);
        const pen = mouse.down ? CLICK_PEN : HOVER_PEN;
        const strength = mouse.down ? 0.4 : 0.12;

        for (let i = 0; i < cells.length; i++) {
            const col = cells[i];
            for (let j = 0; j < col.length; j++) {
                const c = col[j];

                c.xv += Math.random() * 0.4 - 0.2;
                c.yv += Math.random() * 0.4 - 0.2;

                if (applyMouse) {
                    const dx = c.x - mouse.x;
                    const dy = c.y - mouse.y;
                    const dist = Math.sqrt(dx * dx + dy * dy);
                    if (dist < pen) {
                        const power = (pen / (dist < 4 ? pen : dist)) * strength;
                        c.xv += mx * power;
                        c.yv += my * power;
                    }
                }

                c.pressure = (
                    (c.upLeft.xv * 0.5 + c.left.xv + c.downLeft.xv * 0.5
                        - c.upRight.xv * 0.5 - c.right.xv - c.downRight.xv * 0.5) +
                    (c.upLeft.yv * 0.5 + c.up.yv + c.upRight.yv * 0.5
                        - c.downLeft.yv * 0.5 - c.down.yv - c.downRight.yv * 0.5)
                ) * 0.25;
            }
        }

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        const isLight = document.documentElement.hasAttribute('data-theme');
        const styles = getComputedStyle(document.documentElement);
        const accentColor = styles.getPropertyValue('--accent').trim();
        const dimColor = styles.getPropertyValue('--accent-dim').trim();
        const grad = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
        if (matrixMode) {
            grad.addColorStop(0, '#003300');
            grad.addColorStop(0.5, '#00cc44');
            grad.addColorStop(1, '#66ff88');
        } else if (isLight) {
            grad.addColorStop(0, dimColor);
            grad.addColorStop(0.5, accentColor);
            grad.addColorStop(1, '#475569');
        } else {
            grad.addColorStop(0, dimColor);
            grad.addColorStop(0.5, accentColor);
            grad.addColorStop(1, '#e2e8f0');
        }
        ctx.strokeStyle = grad;
        ctx.lineWidth = 1;

        const numObs = obstacles.length;

        for (let i = 0; i < particles.length; i++) {
            const p = particles[i];

            if (p.x >= 0 && p.x < canvas.width && p.y >= 0 && p.y < canvas.height) {
                const col = Math.floor(p.x / RES);
                const row = Math.floor(p.y / RES);

                if (col >= 0 && col < numCols && row >= 0 && row < numRows) {
                    const c = cells[col][row];
                    const ax = (p.x % RES) / RES;
                    const ay = (p.y % RES) / RES;

                    p.xv += (1 - ax) * c.xv * 0.05;
                    p.yv += (1 - ay) * c.yv * 0.05;
                    p.xv += ax * c.right.xv * 0.05;
                    p.yv += ax * c.right.yv * 0.05;
                    p.xv += ay * c.down.xv * 0.05;
                    p.yv += ay * c.down.yv * 0.05;
                }

                p.xv *= simSpeed;
                p.yv *= simSpeed;

                if (gravityOn || matrixMode) {
                    p.yv += matrixMode ? 0.3 : 0.15;
                }

                p.x += p.xv;
                p.y += p.yv;

                for (let o = 0; o < numObs; o++) {
                    const obs = obstacles[o];

                    if (p.x > obs.left && p.x < obs.right &&
                        p.y > obs.top && p.y < obs.bottom) {

                        const dL = p.x - obs.left;
                        const dR = obs.right - p.x;
                        const dT = p.y - obs.top;
                        const dB = obs.bottom - p.y;
                        const min = Math.min(dL, dR, dT, dB);

                        if (min === dL)      { p.x = obs.left - 1;  p.xv *= -0.15; }
                        else if (min === dR)  { p.x = obs.right + 1; p.xv *= -0.15; }
                        else if (min === dT)  { p.y = obs.top - 1;   p.yv *= -0.15; }
                        else                  { p.y = obs.bottom + 1; p.yv *= -0.15; }

                        p.px = p.x;
                        p.py = p.y;
                    } else {
                        const sL = obs.left - REPEL_MARGIN;
                        const sR = obs.right + REPEL_MARGIN;
                        const sT = obs.top - REPEL_MARGIN;
                        const sB = obs.bottom + REPEL_MARGIN;

                        if (p.x > sL && p.x < sR && p.y > sT && p.y < sB) {
                            if (p.x < obs.left)       p.xv -= 0.06;
                            else if (p.x > obs.right)  p.xv += 0.06;
                            if (p.y < obs.top)         p.yv -= 0.06;
                            else if (p.y > obs.bottom)  p.yv += 0.06;
                        }
                    }
                }

                const ddx = p.px - p.x;
                const ddy = p.py - p.y;
                const pdist = Math.sqrt(ddx * ddx + ddy * ddy);
                const limit = Math.random() * 0.5;

                ctx.beginPath();
                ctx.moveTo(p.x, p.y);
                ctx.lineTo(pdist > limit ? p.px : p.x + limit, pdist > limit ? p.py : p.y + limit);
                ctx.stroke();

                p.px = p.x;
                p.py = p.y;
            } else {
                if ((gravityOn || matrixMode) && p.y >= canvas.height) {
                    p.x = p.px = Math.random() * canvas.width;
                    p.y = p.py = 0;
                } else {
                    p.x = p.px = Math.random() * canvas.width;
                    p.y = p.py = Math.random() * canvas.height;
                }
                p.xv = p.yv = 0;
            }

            p.xv *= 0.5;
            p.yv *= 0.5;
        }

        for (let i = 0; i < cells.length; i++) {
            const col = cells[i];
            for (let j = 0; j < col.length; j++) {
                const c = col[j];
                c.xv += (c.upLeft.pressure * 0.5 + c.left.pressure + c.downLeft.pressure * 0.5
                    - c.upRight.pressure * 0.5 - c.right.pressure - c.downRight.pressure * 0.5) * 0.25;
                c.yv += (c.upLeft.pressure * 0.5 + c.up.pressure + c.upRight.pressure * 0.5
                    - c.downLeft.pressure * 0.5 - c.down.pressure - c.downRight.pressure * 0.5) * 0.25;
                c.xv *= 0.99;
                c.yv *= 0.99;
            }
        }

        mouse.px = mouse.x;
        mouse.py = mouse.y;

        requestAnimationFrame(draw);
    }

    function handleMove(clientX, clientY) {
        mouse.px = mouse.x;
        mouse.py = mouse.y;
        mouse.x = clientX * (canvas.width / window.innerWidth);
        mouse.y = clientY * (canvas.height / window.innerHeight);
    }

    document.addEventListener('mousedown', (e) => {
        // Don't set mouse.down if interacting with the terminal
        if (!e.target.closest('.terminal')) {
            mouse.down = true;
        }
    });
    document.addEventListener('mouseup', () => { mouse.down = false; });
    document.addEventListener('mousemove', (e) => {
        if (!isDragging) handleMove(e.clientX, e.clientY);
    });

    document.addEventListener('touchstart', (e) => {
        if (!e.target.closest('.terminal')) {
            mouse.down = true;
            handleMove(e.touches[0].clientX, e.touches[0].clientY);
        }
    }, { passive: true });
    document.addEventListener('touchend', (e) => {
        if (!e.touches.length) mouse.down = false;
    });
    document.addEventListener('touchmove', (e) => {
        if (!isDragging) handleMove(e.touches[0].clientX, e.touches[0].clientY);
    }, { passive: true });

    window.addEventListener('resize', setup);

    // ─── Initialize ───────────────────────────────────────────

    setup();
    draw();
    updateNav();
    updateProgress();

})();
