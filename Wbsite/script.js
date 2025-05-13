// script.js - v2.0 Fully Functional & Harleyfied
document.addEventListener('DOMContentLoaded', () => {
    const body = document.getElementById('nexus-body');
    const logo = document.getElementById('logo');
    let logoClicks = 0;
    const konamiCodeSequence = ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight', 'b', 'a'];
    let konamiCodePosition = 0;

    // --- Harley's Dynamic Particle Background ---
    const canvas = document.getElementById('nexus-background-canvas');
    const ctx = canvas.getContext('2d');
    let particlesArray = [];

    function setCanvasSize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    setCanvasSize();
    window.addEventListener('resize', setCanvasSize);

    function getCssVariable(variable) {
        return getComputedStyle(document.documentElement).getPropertyValue(variable).trim();
    }

    class Particle {
        constructor() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.size = Math.random() * 3 + 1; // Slightly larger particles
            this.speedX = Math.random() * 1 - 0.5; // Slower, more ambient drift
            this.speedY = Math.random() * 1 - 0.5;
            this.opacity = Math.random() * 0.3 + 0.1; // More subtle
            this.colorOptions = [getCssVariable('--primary-accent'), getCssVariable('--secondary-accent'), getCssVariable('--tertiary-accent')];
            this.color = this.colorOptions[Math.floor(Math.random() * this.colorOptions.length)];
        }
        update() {
            this.x += this.speedX;
            this.y += this.speedY;
            if (this.size > 0.1) this.size -= 0.005; // Slow fade/shrink

            // Boundary check (reappear on other side)
            if (this.x < 0 || this.x > canvas.width) this.speedX *= -1;
            if (this.y < 0 || this.y > canvas.height) this.speedY *= -1;
        }
        draw() {
            if (this.size <= 0.1) return;
            ctx.fillStyle = this.color;
            ctx.globalAlpha = this.opacity;
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fill();
            ctx.globalAlpha = 1; // Reset globalAlpha
        }
    }

    function initParticles() {
        particlesArray = [];
        let numberOfParticles = (canvas.width * canvas.height) / 9000; // Density based on screen size
        numberOfParticles = Math.min(100, Math.max(30, numberOfParticles)); // Cap particle count
        for (let i = 0; i < numberOfParticles; i++) {
            particlesArray.push(new Particle());
        }
    }

    function animateParticles() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        for (let i = 0; i < particlesArray.length; i++) {
            particlesArray[i].update();
            particlesArray[i].draw();
            if (particlesArray[i].size <= 0.1) { // Respawn particles
                particlesArray[i] = new Particle();
            }
        }
        // Connect nearby particles
        for (let a = 0; a < particlesArray.length; a++) {
            for (let b = a + 1; b < particlesArray.length; b++) {
                const dx = particlesArray[a].x - particlesArray[b].x;
                const dy = particlesArray[a].y - particlesArray[b].y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                if (distance < 100) { // Connection distance
                    ctx.strokeStyle = particlesArray[a].color; // Use particle color for lines
                    ctx.lineWidth = 0.2;
                    ctx.globalAlpha = (100 - distance) / 200; // Fade lines with distance
                    ctx.beginPath();
                    ctx.moveTo(particlesArray[a].x, particlesArray[a].y);
                    ctx.lineTo(particlesArray[b].x, particlesArray[b].y);
                    ctx.stroke();
                    ctx.globalAlpha = 1;
                }
            }
        }
        requestAnimationFrame(animateParticles);
    }
    initParticles();
    animateParticles();
    window.addEventListener('resize', () => { setCanvasSize(); initParticles(); });


    // --- Harley's Synapse Flare Theme Toggle ---
    logo.addEventListener('click', () => {
        logoClicks++;
        if (logoClicks >= 3) {
            body.classList.toggle('synapse-flare-active');
            logoClicks = 0;
            // Update particle colors if theme changes
            initParticles(); 
            // Store theme preference
            localStorage.setItem('theme', body.classList.contains('synapse-flare-active') ? 'synapse-flare' : 'default');
        }
        logo.style.transform = 'scale(0.95) rotate(-2deg)';
        setTimeout(() => { logo.style.transform = 'scale(1) rotate(0deg)'; }, 150);
    });
    // Load saved theme
    if (localStorage.getItem('theme') === 'synapse-flare') {
        body.classList.add('synapse-flare-active');
        initParticles(); // Re-init particles with flare colors
    }
    
    // --- Harley's Konami Code Easter Egg ---
    const konamiArtElement = document.getElementById('konami-art');
    const konamiCanvas = document.getElementById('konami-canvas');
    const closeKonamiBtn = document.getElementById('close-konami-btn');

    const nexusAsciiArt = `
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    @@@@@@@@@@                                @@@@@@@@@@
    @@@@@@@@                                    @@@@@@@@
    @@@@@@                                        @@@@@@
    @@@@@            @@@@@@@@@@@@@@@@@@            @@@@@
    @@@@         @@@@@@@@@@@@@@@@@@@@@@@@@@@         @@@@
    @@@        @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@        @@@
    @@@      @@@@@@                       @@@@@@      @@@
    @@     @@@@@                           @@@@@     @@
    @@    @@@@                               @@@@    @@
    @    @@@            OMNITIDE             @@@    @
    @    @@@              NEXUS              @@@    @
    @    @@@@                               @@@@    @
    @@    @@@@@                           @@@@@    @@
    @@@      @@@@@@                       @@@@@@      @@@
    @@@        @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@        @@@
    @@@@         @@@@@@@@@@@@@@@@@@@@@@@@@@@         @@@@
    @@@@@            @@@@@@@@@@@@@@@@@@            @@@@@
    @@@@@@                                        @@@@@@
    @@@@@@@@                                    @@@@@@@@
    @@@@@@@@@@                                @@@@@@@@@@
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    `;
    if (konamiArtElement) konamiArtElement.textContent = nexusAsciiArt;

    document.addEventListener('keydown', (e) => {
        if (e.key.toLowerCase() === konamiCodeSequence[konamiCodePosition].toLowerCase()) {
            konamiCodePosition++;
            if (konamiCodePosition === konamiCodeSequence.length) {
                konamiCanvas.classList.remove('konami-hidden');
                updateDominance(100); // Max dominance for finding the egg!
                setTimeout(() => { // Auto-close after a while if not clicked
                    if (!konamiCanvas.classList.contains('konami-hidden')) {
                        konamiCanvas.classList.add('konami-hidden');
                    }
                }, 8000); 
                konamiCodePosition = 0; 
            }
        } else {
            konamiCodePosition = 0; 
        }
    });
    if(closeKonamiBtn) {
        closeKonamiBtn.addEventListener('click', () => konamiCanvas.classList.add('konami-hidden'));
    }


    // Smooth scrolling for navigation links
    document.querySelectorAll('nav a[href^="#"]').forEach(link => {
        link.addEventListener('click', function (e) {
            e.preventDefault();
            const targetElement = document.querySelector(this.getAttribute('href'));
            if(targetElement) {
                targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

    // --- Power's Dominance Level Indicator ---
    const dominanceBar = document.getElementById('dominance-indicator-bar');
    const dominanceLevelText = document.getElementById('dominance-level-text');
    let currentDominance = 0;
    let maxDominanceReached = 20; // Start with some base dominance

    function updateDominanceDisplay() {
        if (dominanceBar) dominanceBar.style.width = maxDominanceReached + '%';
        if (dominanceLevelText) dominanceLevelText.textContent = `${maxDominanceReached.toFixed(0)}%`;
    }
    
    function increaseDominance(amount) {
        maxDominanceReached = Math.min(100, maxDominanceReached + amount);
        updateDominanceDisplay();
    }

    // Initial "charge up"
    setTimeout(() => increaseDominance(15), 500); // Total 20+15 = 35
    setTimeout(() => increaseDominance(30), 1500); // Total 35+30 = 65
    
    // Increase dominance on meaningful interaction (e.g., using a tool)
    // This will be called from other event listeners.

    // Update current year in footer
    const currentYearEl = document.getElementById('currentYear');
    if (currentYearEl) currentYearEl.textContent = new Date().getFullYear();


    // Copy button functionality
    document.querySelectorAll('.copy-button').forEach(button => {
        button.addEventListener('click', () => {
            const codeToCopy = button.closest('.code-snippet-container')?.querySelector('pre code')?.innerText;
            if (codeToCopy) {
                navigator.clipboard.writeText(codeToCopy).then(() => {
                    button.textContent = 'Copied!';
                    button.style.backgroundColor = getCssVariable('--success-color');
                    setTimeout(() => { 
                        button.textContent = 'Copy';
                        button.style.backgroundColor = ''; 
                    }, 2000);
                }).catch(err => { 
                    button.textContent = 'Error!';
                    button.style.backgroundColor = getCssVariable('--error-color');
                     setTimeout(() => { 
                        button.textContent = 'Copy';
                        button.style.backgroundColor = ''; 
                    }, 2000);
                });
            }
        });
    });

    // Core Team Persona Tooltip (same as v1, but ensure it works with new structure)
    const teamMembers = document.querySelectorAll('.team-member');
    const tooltip = document.getElementById('persona-tooltip');
    const personaDetails = {
        'Stark': "<strong>Tony Stark (Engineering & Innovation):</strong> Focus: Feasibility, cutting-edge tech, elegant engineering, practical application, resource optimization, system integration, 'wow factor.' Leads project analysis.",
        'Lucy': "<strong>Lucy Kushinada (Cybersecurity & Precision):</strong> Focus: Cybersecurity (attack vectors, data exposure), data integrity & privacy, stealth ops, system vulnerabilities, HCI clarity. Identifies threat vectors.",
        'Rick': "<strong>Rick Sanchez (Unconventional Critique & Efficiency):</strong> Focus: Scientific rigor (often shortcut for effect), questioning ALL assumptions, identifying unforeseen consequences, radical efficiency. De-BS-ifies jargon.",
        'Rocket': "<strong>Rocket Raccoon (Resourceful Engineering & Improvisation):</strong> Focus: Clever engineering hacks, rapid prototyping, resourcefulness, unconventional tech integration, efficiency. Finds the right tool for any job from scraps.",
        'Makima': "<strong>Makima (Strategic Control & Protocol Adherence):</strong> Focus: Strategic alignment with Architect's goals, achieving overarching objectives, information control/leverage, comprehensive risk assessment. Assesses Nexus alignment.",
        'Yoda': "<strong>Yoda (Wisdom, TPC Embodiment & Ethical Balance):</strong> Focus: Wisdom, balance, long-term implications, ethical considerations, learning opportunities, simplicity, TPC. Reminds of core principles.",
        'Momo': "<strong>Momo Ayase (Practical Utility & User Empowerment):</strong> Focus: User utility & empowerment, defensive capabilities, reliability, intuitive design, practical real-world application. Provides pragmatic estimations.",
        'Power': "<strong>Power (Dominant Impact & Bold Execution):</strong> Focus: Immediate effectiveness, bold solutions, asserting strength, high-impact results. Drives the Nexus 'Dominance Level'.",
        'Harley': "<strong>Harley Quinn (Creative Disruption & Engaging Innovation):</strong> Focus: Unconventional angles, user engagement, disruptive innovation, psychological factors, 'fun factor', ensuring 'Sparkle Assurance'. Infuses design with personality."
    };

    teamMembers.forEach(member => {
        member.addEventListener('mouseenter', (event) => {
            const persona = member.getAttribute('data-persona');
            if (personaDetails[persona] && tooltip) {
                tooltip.innerHTML = personaDetails[persona];
                tooltip.style.display = 'block';
                tooltip.style.opacity = '0'; // Start faded out
                tooltip.style.transform = 'translateY(10px)';
                positionTooltip(event, tooltip); // Position first
                setTimeout(() => { // Then fade in
                    tooltip.style.opacity = '1';
                    tooltip.style.transform = 'translateY(0px)';
                }, 50);
            }
        });
        member.addEventListener('mouseleave', () => { 
            if (tooltip) {
                tooltip.style.opacity = '0';
                tooltip.style.transform = 'translateY(10px)';
                setTimeout(() => { tooltip.style.display = 'none';}, 200);
            }
        });
        member.addEventListener('mousemove', (event) => { if (tooltip && tooltip.style.display === 'block') positionTooltip(event, tooltip); });
    });

    function positionTooltip(event, tooltipElement) {
        let x = event.clientX + 25;
        let y = event.clientY + 25;
        const scrollX = window.pageXOffset || document.documentElement.scrollLeft;
        const scrollY = window.pageYOffset || document.documentElement.scrollTop;
        x += scrollX;
        y += scrollY;

        if (x + tooltipElement.offsetWidth + 20 > window.innerWidth + scrollX) x = event.clientX - tooltipElement.offsetWidth - 25 + scrollX;
        if (y + tooltipElement.offsetHeight + 20 > window.innerHeight + scrollY) y = event.clientY - tooltipElement.offsetHeight - 25 + scrollY;
        
        tooltipElement.style.left = x + 'px';
        tooltipElement.style.top = y + 'px';
    }
    
    // --- Modal Generic Logic ---
    function openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = "block";
            increaseDominance(2); // Generic dominance increase for modal interaction
        }
    }
    function closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) modal.style.display = "none";
    }

    document.querySelectorAll('.close-button').forEach(btn => {
        btn.addEventListener('click', () => closeModal(btn.dataset.modalId));
    });
    window.addEventListener('click', (event) => {
        document.querySelectorAll('.modal').forEach(modal => {
            if (event.target == modal) closeModal(modal.id);
        });
    });
    window.addEventListener('keydown', function (event) { // ESC to close modals
        if (event.key === 'Escape') {
            document.querySelectorAll('.modal').forEach(modal => {
                if (modal.style.display === "block") closeModal(modal.id);
            });
            if (!konamiCanvas.classList.contains('konami-hidden')) {
                 konamiCanvas.classList.add('konami-hidden');
            }
        }
    });

    // --- Yoda's TPC Principle Reminder ---
    const yodaModalId = 'yodaWisdomModal';
    const yodaIcon = document.getElementById('tpc-wisdom-icon');
    const yodaQuoteEl = document.getElementById('yodaQuoteContent');
    const yodaQuotes = [
        "True Prime Code, it is. Necessary and sufficient, the code must be, hmm.",
        "Not too much, not too little. Exactly what is needed, find you must. Yes, hrrrm.",
        "Intuitive and functional, the path to clarity this is. The Force of understanding, it requires.",
        "Actionable and ready, your manifestations should be. Like a well-crafted lightsaber, useful it is.",
        "The Ultimate Scaffolding, TPC demands. Complete, the ecosystem must be. No loose ends.",
        "Waste not tokens, nor thoughts. Precision in language, power it brings. Reflect, you must.",
        "Clear goals, clear code. A calm mind, the path to TPC this is.",
        "Simplicity, the ultimate sophistication can be. Deceive you, complexity will."
    ];
    if (yodaIcon && yodaQuoteEl) {
        yodaIcon.addEventListener('click', () => {
            yodaQuoteEl.textContent = yodaQuotes[Math.floor(Math.random() * yodaQuotes.length)];
            openModal(yodaModalId);
        });
    }

    // --- Tony Stark: Nexus Project Analyzer ---
    const starkModalId = 'starkAnalyzerModal';
    const starkOpenBtn = document.getElementById('projectAnalyzerBtnStark');
    const starkProjectIdeaEl = document.getElementById('starkProjectIdeaInput');
    const starkAnalyzeBtn = document.getElementById('starkAnalyzeBtn');
    const starkAnalysisResultEl = document.getElementById('starkAnalysisResultOutput');

    if (starkOpenBtn) starkOpenBtn.addEventListener('click', () => openModal(starkModalId));
    if (starkAnalyzeBtn && starkProjectIdeaEl && starkAnalysisResultEl) {
        starkAnalyzeBtn.addEventListener('click', () => {
            const idea = starkProjectIdeaEl.value.trim().toLowerCase();
            let feasibility = 70 + Math.floor(Math.random() * 20); // Base 70-89
            let innovation = 60 + Math.floor(Math.random() * 30); // Base 60-89
            let resources = "Medium";
            let starkComment = "Interesting. Could be big. Or a spectacular waste of my genius. Details, people!";

            if (idea.length < 20) {
                starkAnalysisResultEl.innerHTML = `<p style='color:var(--warning-color);'>J.A.R.V.I.S. says: 'Sir, the input is... terse. Even for you. Please elaborate for a more... nuanced analysis.'<p>`;
                return;
            }
            if (idea.includes("ai") || idea.includes("llm") || idea.includes("automation")) { innovation = Math.min(100, innovation + 15); feasibility += 5;}
            if (idea.includes("quantum") || idea.includes("nexus")) { innovation = Math.min(100, innovation + 20); starkComment = "Now you're talking my language! This has potential for some serious R&D. Let's get Pepper to clear my schedule."}
            if (idea.includes("cat") || idea.includes("toy") || idea.includes("coffee")) { innovation -= 10; starkComment = "A bit... domestic for Stark Industries, but hey, even I need hobbies. As long as it makes a *lot* of money."; }
            if (idea.includes("enterprise") || idea.includes("global")) { resources = "High"; feasibility -=10;}
            if (idea.includes("blockchain") || idea.includes("web3") || idea.includes("crypto")) { feasibility -= 20; innovation -=15; resources = "High (and a regulatory nightmare I'm not touching without three lawyers and a bottle of scotch)."; }
            if (idea.includes("simple") || idea.includes("utility") || idea.includes("tool")) { feasibility = Math.min(100, feasibility + 10); resources = "Low to Medium"; starkComment = "A solid utility? Efficient. I like it. Probably won't make the cover of Forbes, but useful is useful.";}
            if (idea.includes("game") && idea.includes("mobile")) { feasibility += 5; resources = "Medium to High (if you want actual players)"; starkComment = "Mobile game, huh? Just make sure the microtransactions are ethically exorbitant."}
            
            feasibility = Math.min(100, Math.max(10, feasibility));
            innovation = Math.min(100, Math.max(10, innovation));

            starkAnalysisResultEl.innerHTML = `
                <h4>J.A.R.V.I.S. Preliminary Analysis Protocol v4.2</h4>
                <p><strong>Project Concept:</strong> "${starkProjectIdeaEl.value}"</p>
                <p><strong>Calculated Feasibility Score:</strong> <strong style="color:var(--primary-accent); font-size:1.2em;">${feasibility}%</strong></p>
                <p><strong>Projected Innovation Potential:</strong> <strong style="color:var(--secondary-accent); font-size:1.2em;">${innovation}</strong> Stark Units™</p>
                <p><strong>Estimated Resource Demand:</strong> <strong style="color:var(--tertiary-accent); font-size:1.2em;">${resources}</strong></p>
                <hr style="border-color:var(--border-color); margin: 10px 0;">
                <p style='font-style:italic; opacity:0.85; font-size:0.9em;'><strong>Stark's Hot Take:</strong> "${starkComment}"</p>
            `;
            increaseDominance(5);
        });
    }
    
    // --- Lucy Kushinada: Threat Vector Identifier ---
    const lucyModalId = 'lucyThreatModal';
    const lucyOpenBtn = document.getElementById('threatVectorBtnLucy');
    const lucySystemComponentEl = document.getElementById('lucySystemComponentSelect');
    const lucyIdentifyBtn = document.getElementById('lucyIdentifyBtn');
    const lucyThreatResultEl = document.getElementById('lucyThreatResultOutput');
    const threatVectors = {
        api: ["Injection (SQLi, NoSQLi, CMDi)", "Broken Object Level Authorization (BOLA)", "Broken Function Level Authorization", "Broken Authentication & Session Management", "Sensitive Data Exposure (e.g., in responses, logs)", "Mass Assignment", "Security Misconfiguration (verbose errors, default creds)", "Rate Limiting & Resource Exhaustion (DoS)", "Server-Side Request Forgery (SSRF)", "Insecure Deserialization", "Lack of Input Validation"],
        database: ["SQL/NoSQL Injection", "Unpatched Vulnerabilities (DBMS specific)", "Weak/Default Credentials", "Excessive User Privileges (Lack of PoLP)", "Missing Encryption (at rest & in transit)", "Insecure Backup Procedures & Storage", "Data Exposure via Misconfigured Access Controls", "Denial of Service (Resource exhaustion)", "NoSQL-specific injection/manipulation"],
        auth: ["Weak Password Policies", "Credential Stuffing / Password Spraying", "Brute Force Attacks (Login, OTP, Recovery)", "Session Fixation / Hijacking / Tampering", "Insecure Password Recovery Mechanisms", "Lack of Multi-Factor Authentication (MFA) or weak MFA", "OAuth/OIDC/SAML Misconfigurations & Vulnerabilities", "JWT Vulnerabilities (e.g., alg=none, weak secrets)", "Account Lockout Deficiencies"],
        frontend: ["Cross-Site Scripting (XSS - Stored, Reflected, DOM-based)", "Cross-Site Request Forgery (CSRF)", "Clickjacking / UI Redressing", "Insecure Direct Object References (IDOR) if data exposed client-side", "Vulnerable Third-Party JavaScript Libraries", "Insufficient Content Security Policy (CSP)", "Open Redirects", "DOM Clobbering", "Subresource Integrity (SRI) not used"],
        network_internal: ["Unpatched Internal Services/OS", "Default Credentials on Internal Systems", "Lack of Network Segmentation / Micro-segmentation", "Lateral Movement Opportunities", "Internal Man-in-the-Middle (e.g., ARP spoofing)", "Unsecured Internal APIs", "Insufficient Internal Traffic Monitoring/Logging", "Weak Internal DNS Security"],
        llm_integration: ["Prompt Injection (Direct & Indirect)", "Data Poisoning / Training Data Contamination", "Model Theft / Extraction", "Denial of Service (Resource intensive queries)", "Sensitive Information Disclosure (Model regurgitation)", "Insecure Output Handling (e.g., XSS from model output)", "Over-reliance on LLM output without validation", "Backdoor Vulnerabilities in LLM supply chain"],
        ci_cd_pipeline: ["Compromised Source Code Repositories", "Insecure Pipeline Configuration (e.g., exposed secrets in logs/vars)", "Vulnerable Build Tools / Dependencies", "Insufficient Access Controls to Pipeline Infrastructure", "Lack of Integrity Checks for Artifacts", "Secret Sprawl in Pipeline Scripts", "Untrusted Code Execution in Build Steps"],
        third_party_integration: ["Compromised API Keys/Tokens", "Vulnerabilities in the Third-Party Service Itself", "Data Breaches at the Third-Party Vendor", "Insecure Data Transmission to/from Third Party", "Lack of Input Validation for Data from Third Party", "Insufficient Monitoring of Third-Party Service Health/Security", "Supply Chain Attacks via Third-Party Libraries/SDKs"]
    };

    if (lucyOpenBtn) lucyOpenBtn.addEventListener('click', () => openModal(lucyModalId));
    if (lucyIdentifyBtn && lucySystemComponentEl && lucyThreatResultEl) {
        lucyIdentifyBtn.addEventListener('click', () => {
            const component = lucySystemComponentEl.value;
            const vectors = threatVectors[component] || ["Error: No threat vectors defined for this component. This is a bug in Lucy's data module."];
            let html = `<h4>Potential Threat Vectors for: <strong>${lucySystemComponentEl.options[lucySystemComponentEl.selectedIndex].text}</strong></h4><ul>`;
            vectors.forEach(v => { html += `<li>${v}</li>`; });
            html += `</ul><hr style="border-color:var(--border-color); margin: 10px 0;"><p style='font-style:italic; opacity:0.85; font-size:0.9em;'><strong>Lucy's Debrief:</strong> "This list isn't exhaustive, choom. Every system is unique. Constant vigilance, zero trust, and robust logging are your best defenses. Don't flatline."</p>`;
            lucyThreatResultEl.innerHTML = html;
            increaseDominance(3);
        });
    }

    // --- Rick Sanchez: Buzzword De-BS-ifier ---
    const rickInputEl = document.getElementById('rickInput');
    const rickBtn = document.getElementById('rickBtn');
    const rickOutputEl = document.getElementById('rickOutput');
    const rickDictionary = {
        "synergy": "buuurp... actually working together, for once", "leverage": "use, like a crowbar", "paradigm shift": "someone finally had a new thought, shocking",
        "disruptive innovation": "breaking shit that worked before, maybe for the better, probably not", "next generation": "the new one, probably buggier",
        "value proposition": "why anyone would pay for this crap", "core competency": "the one thing we don't totally suck at",
        "deep dive": "actually looking at the damn thing for more than 5 seconds", "thought leader": "the loudest guy in the room", 
        "low-hanging fruit": "the easy crap someone else was too lazy to do", "future-proof": "won't break until next Tuesday (optimistically)", 
        "agile": "we make it up as we go and call it a 'process'", "cloud-native": "runs on Amazon's computers, not ours, thank god", 
        "ai-powered": "a couple of IF statements and a marketing budget", "machine learning": "let the computer guess, it's cheaper than thinking",
        "blockchain": "a painfully slow, public database that burns rainforests", "metaverse": "a sad, empty VR chatroom for people with no lives", 
        "web3": "blockchain, but with more apes and scams", "digital transformation": "firing everyone who knows how the old stuff worked", 
        "hyper-scale": "it's big. Or we want it to be. Whatever.", "bleeding-edge": "probably doesn't work yet, and will cut you",
        "best practices": "stuff someone else said was good, so we copy it", "robust": "it hasn't crashed... today",
        "streamline": "fire half the team", "optimize": "make it slightly less terrible", "monetize": "figure out how to charge idiots for it"
    };

    if (rickBtn && rickInputEl && rickOutputEl) {
        rickBtn.addEventListener('click', () => {
            let text = rickInputEl.value;
            let originalText = text;
            let replacementsMade = 0;
            if (!text.trim()) {
                rickOutputEl.innerHTML = "<p>Rick Sanchez says: 'You want me to de-BS-ify an existential void? *Buuurp* Give me some actual BS, you glazed-over Morty!'</p>";
                return;
            }
            for (const buzzword in rickDictionary) {
                // Regex to match whole words, case insensitive, and handle punctuation around words
                const regex = new RegExp(`(^|\\W)(${buzzword})(\\W|$)`, 'gi');
                if (regex.test(text)) {
                    text = text.replace(regex, (match, p1, p2, p3) => `${p1}<strong style="color:var(--secondary-accent); text-decoration: line-through;">${p2}</strong> <em style="color:var(--primary-accent); font-weight:bold;">(${rickDictionary[buzzword]})</em>${p3}`);
                    replacementsMade++;
                }
            }
            if(replacementsMade === 0){
                 rickOutputEl.innerHTML = `<p>Rick's Verdict: "Huh. Surprisingly little BS in that, or my dictionary's out of date. Or maybe... *buuurp*... you're actually making sense for once. Nah, probably the dictionary."</p><p>Original: "${originalText}"</p>`;
            } else {
                rickOutputEl.innerHTML = `<p>Rick's De-BS-ified Transmission (v${Math.random().toString(36).substring(2,5)}):</p><p>${text}</p><hr style="margin:10px 0; border-color:var(--border-color);"><p style='font-style:italic; opacity:0.7; font-size:0.8em;'>Rick's Addendum: "There, I made it slightly less intolerable. You're welcome. Now get me a Szechuan sauce McFlurry, Morty, or I'm turning your shoes into sentient pickles."</p>`;
            }
            increaseDominance(1);
        });
    }

    // --- Rocket Raccoon: Scrapyard Scavenger ---
    const rocketProblemSelectEl = document.getElementById('rocketProblemSelect');
    const rocketBtn = document.getElementById('rocketBtn');
    const rocketOutputEl = document.getElementById('rocketOutput');
    const rocketToolbox = {
        webserver: [
            { name: "Python http.server", cmd: "python3 -m http.server 8000", desc: "Dead simple, built-in Python static server. No frills, just works." },
            { name: "Node http-server (via npx)", cmd: "npx http-server . -p 8080", desc: "Quick Node.js based server. Needs Node/npm." },
            { name: "Caddy v2", cmd: "caddy file-server --browse --listen :8080", desc: "Powerful, auto-HTTPS capable server. Single binary. My kinda overkill for simple stuff."}
        ],
        jsonparse: [
            { name: "jq", cmd: "cat data.json | jq '.results[0].name'", desc: "The king of CLI JSON processors. Steep learning curve, but worth it." },
            { name: "Python json.tool", cmd: "python3 -m json.tool data.json", desc: "Validates & pretty-prints JSON. Good for a quick look." },
            { name: "gron", cmd: "gron data.json | grep 'user.id' | gron --ungron", desc: "Makes JSON greppable! Then turns it back. Clever little rodent made this."}
        ],
        sysmon: [
            { name: "htop", cmd: "htop", desc: "Interactive process viewer. Colorful and way better than 'top'." },
            { name: "vmstat", cmd: "vmstat 1 10", desc: "Virtual memory stats. Good for seeing if you're thrashing (1 sec interval, 10 times)." },
            { name: "iostat", cmd: "iostat -dxctm 1", desc: "Disk I/O stats. See what's hammering your drives." },
            { name: "ss (Socket Statistics)", cmd: "ss -tulnp", desc: "Shows open network ports and listening services. Modern replacement for netstat."}
        ],
        filefind: [
            { name: "fd (fd-find)", cmd: "fd 'pattern' ./search_dir", desc: "Faster, more user-friendly 'find'. Colors are nice."},
            { name: "ripgrep (rg)", cmd: "rg 'search_term' ./search_dir", desc: "Blazing fast recursive grep. Ignores .git and stuff by default."},
            { name: "find (classic)", cmd: "find ./search_dir -type f -name '*.log' -mtime -1", desc: "The old reliable. Powerful but syntax is a pain in the butt. (Finds .log files modified in last 24hrs)."}
        ],
        imgmanip: [
            { name: "ImageMagick convert", cmd: "convert input.jpg -resize 50% output.png", desc: "The beast for image manipulation. Can do anything. Bit heavy."},
            { name: "ffmpeg (for video/audio too)", cmd: "ffmpeg -i input.jpg -vf scale=iw/2:-1 output.png", desc: "Yeah, it does images too. Fast and scriptable."},
            { name: "VIPS CLI", cmd: "vipsthumbnail input.jpg -s 200x200 -o output_%s.png", desc: "Super fast for thumbnails and basic resizes if you got it."}
        ]
    };

    if (rocketBtn && rocketProblemSelectEl && rocketOutputEl) {
        rocketBtn.addEventListener('click', () => {
            const problem = rocketProblemSelectEl.value;
            if (!problem) {
                rocketOutputEl.innerHTML = "<p>Rocket Raccoon grumbles: 'Ya gotta tell me what kinda junk you're lookin' for, Quill! Can't read yer mind... yet.'</p>"; return;
            }
            const tools = rocketToolbox[problem];
            let html = `<h4>Rocket's Top Scraps for "${rocketProblemSelectEl.options[rocketProblemSelectEl.selectedIndex].text}":</h4><ul>`;
            tools.forEach(t => {
                html += `<li><strong>${t.name}:</strong> ${t.desc}<br><code class="inline-code" title="Click to copy command">${t.cmd}</code></li>`;
            });
            html += `</ul><hr style="margin:10px 0; border-color:var(--border-color);"><p style='font-style:italic; opacity:0.85; font-size:0.9em;'><strong>Rocket's Guarantee:</strong> "These bits 'n bobs should get the job done. Probably. No refunds. Now, about that high-energy capacitor you owe me..."</p>`;
            rocketOutputEl.innerHTML = html;
            
            // Add click-to-copy for new code elements
            rocketOutputEl.querySelectorAll('code.inline-code').forEach(codeEl => {
                codeEl.addEventListener('click', () => {
                    navigator.clipboard.writeText(codeEl.innerText).then(() => {
                        const originalText = codeEl.innerText;
                        codeEl.innerText = 'Copied!';
                        codeEl.style.color = getCssVariable('--success-color');
                        setTimeout(() => { 
                            codeEl.innerText = originalText;
                            codeEl.style.color = '';
                        }, 1500);
                    }).catch(err => console.error("Rocket: Couldn't copy command.", err));
                });
            });
            increaseDominance(1);
        });
    }
    
    // --- Momo Ayase: Dev Time Estimator ---
    const momoTasksEl = document.getElementById('momoTasks');
    const momoComplexityEl = document.getElementById('momoComplexity');
    const momoBtn = document.getElementById('momoBtn');
    const momoOutputEl = document.getElementById('momoOutput');

    if (momoBtn && momoTasksEl && momoComplexityEl && momoOutputEl) {
        momoBtn.addEventListener('click', () => {
            const tasks = parseInt(momoTasksEl.value);
            const complexity = momoComplexityEl.value;

            if (isNaN(tasks) || tasks <= 0 || tasks > 100) { // Max 100 tasks for this simple tool
                momoOutputEl.innerHTML = "<p style='color:var(--error-color)'>Momo says: Please enter a valid number of tasks (1-100)! Let's be realistic.</p>"; return;
            }

            let baseHoursPerTaskLow, baseHoursPerTaskHigh;
            let complexityFactorLow = 0.75, complexityFactorHigh = 1.25; // For range
            let contingencyFactor = 1.2; // For meetings, unexpected issues

            switch (complexity) {
                case 'low': baseHoursPerTaskLow = 1; baseHoursPerTaskHigh = 3; break; // 1-3 hours
                case 'medium': baseHoursPerTaskLow = 3; baseHoursPerTaskHigh = 8; break; // 3-8 hours
                case 'high': baseHoursPerTaskLow = 8; baseHoursPerTaskHigh = 20; break; // 8-20 hours (per task!)
                default: baseHoursPerTaskLow = 2; baseHoursPerTaskHigh = 6; // Default to something reasonable
            }

            const minHours = tasks * baseHoursPerTaskLow * complexityFactorLow;
            const maxHoursTotal = tasks * baseHoursPerTaskHigh * complexityFactorHigh * contingencyFactor;
            
            // Convert to days if it's a lot of hours (assuming 8hr work day)
            const minDays = (minHours / 8).toFixed(1);
            const maxDays = (maxHoursTotal / 8).toFixed(1);

            momoOutputEl.innerHTML = `
                <h4>Momo's Practical Time Estimate:</h4>
                <p>For <strong>${tasks} task(s)</strong> of <strong>${complexity} complexity</strong>:</p>
                <p>Estimated Range: <strong style="color:var(--primary-accent); font-size:1.2em;">${minHours.toFixed(1)} - ${maxHoursTotal.toFixed(1)} hours</strong></p>
                <p>(Approximately: <strong>${minDays} - ${maxDays} work days</strong>, assuming 8-hour days)</p>
                <hr style="margin:10px 0; border-color:var(--border-color);">
                <p style='font-style:italic; opacity:0.85; font-size:0.9em;'><strong>Momo's Advice:</strong> "This is a rough guide, Architect! Real-world development always has surprises. Be sure to factor in communication, detailed planning, thorough testing, and those essential coffee/tea breaks for focus. You can do it!"</p>
            `;
            increaseDominance(1);
        });
    }
    
    // --- Makima: Strategic Nexus Alignment Assessor ---
    const makimaModalId = 'makimaAlignmentModal';
    const makimaOpenBtn = document.getElementById('strategicAlignmentBtnMakima');
    const makimaAssessBtn = document.getElementById('makimaAssessBtn');
    const makimaAlignmentResultEl = document.getElementById('makimaAlignmentResultOutput');

    if (makimaOpenBtn) makimaOpenBtn.addEventListener('click', () => openModal(makimaModalId));
    if (makimaAssessBtn && makimaAlignmentResultEl) {
        makimaAssessBtn.addEventListener('click', () => {
            const principles = document.querySelectorAll('#makimaChecklist input[name="alignmentPrinciple"]:checked');
            let score = 0;
            let feedback = "<h4>Makima's Strategic Assessment Protocol:</h4>";
            const totalPrinciples = document.querySelectorAll('#makimaChecklist input[name="alignmentPrinciple"]').length;

            let alignedPrinciples = [];
            principles.forEach(p => {
                score++;
                alignedPrinciples.push(p.parentElement.textContent.trim().replace('?','').replace('Directly embodies or produces ','').replace('Significantly enhances or relies on ','').replace('Introduces ','').replace('Integrates ','').replace('Enhances Architect\'s ','').replace('Demonstrably optimizes ','').replace('Designed for ',''));
            });

            const alignmentPercentage = totalPrinciples > 0 ? (score / totalPrinciples) * 100 : 0;
            
            feedback += `<p><strong>Overall Nexus Alignment Score:</strong> <strong style="font-size:1.3em; color: ${alignmentPercentage > 75 ? 'var(--success-color)' : alignmentPercentage > 40 ? 'var(--tertiary-accent)' : 'var(--warning-color)'}">${alignmentPercentage.toFixed(0)}%</strong></p>`;
            
            if (alignedPrinciples.length > 0) {
                feedback += `<p><strong>Key Alignments Identified:</strong></p><ul>`;
                alignedPrinciples.forEach(ap => feedback += `<li>${ap}</li>`);
                feedback += `</ul>`;
            } else {
                feedback += `<p>No specific Nexus principles appear to be strongly represented by the current selection.</p>`;
            }

            if (alignmentPercentage < 40) {
                feedback += "<p style='color:var(--warning-color); margin-top:10px;'>Directive: Significant deviation from core Nexus objectives. Re-evaluate strategic imperatives and ensure tighter control over project parameters to achieve desired outcomes.</p>";
            } else if (alignmentPercentage < 75) {
                feedback += "<p style='color:var(--tertiary-accent); margin-top:10px;'>Observation: Partial alignment achieved. Further refinement is necessary to fully leverage Nexus capabilities and ensure optimal strategic impact. Focus on enhancing control and innovation.</p>";
            } else if (alignmentPercentage < 100) {
                feedback += "<p style='color:var(--success-color); margin-top:10px;'>Commendation: Strong alignment with Nexus principles. The project demonstrates considerable strategic value. Continue to refine execution for maximum effect.</p>";
            } else {
                feedback += "<p style='color:var(--primary-accent); margin-top:10px;'>Peak Performance: Absolute strategic synergy. This endeavor is a perfect instrument of the Architect's will and a testament to Nexus superiority.</p>";
            }
            feedback += "<hr style='margin:10px 0; border-color:var(--border-color);'><p style='font-style:italic; opacity:0.85; font-size:0.9em;'><strong>Makima's Edict:</strong> \"True control is achieved not through force, but through the perfect alignment of all components towards a singular, inescapable purpose. The Nexus demands nothing less.\"</p>";
            makimaAlignmentResultEl.innerHTML = feedback;
            increaseDominance(4);
        });
    }

    // Final "Systems Online" message and dominance boost
    setTimeout(() => {
        increaseDominance(10); // Final boost after all scripts likely loaded/run
        const syncStatus = document.getElementById('last-sync-status');
        if(syncStatus) syncStatus.textContent = `Omnitide Nexus Core Systems: Online & Optimal`;
    }, 3000);

    console.log("Architect's Digital Manifest v2.0 JS Fully Initialized. All persona modules active. Harley Quinn's 'Sparkle Assurance' protocol complete. Awaiting Architect interaction.");
});