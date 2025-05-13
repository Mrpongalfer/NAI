// script.js - v2.0 Fully Functional
document.addEventListener('DOMContentLoaded', () => {
    const body = document.getElementById('nexus-body');
    const logo = document.getElementById('logo');
    let logoClicks = 0;
    const konamiCode = ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight', 'b', 'a'];
    let konamiIndex = 0;

    // --- Harley's Synapse Flare Theme Toggle ---
    logo.addEventListener('click', () => {
        logoClicks++;
        if (logoClicks >= 3) { // Toggle on 3 clicks
            body.classList.toggle('synapse-flare-active');
            logoClicks = 0; // Reset
            // Store theme preference if desired
            if (body.classList.contains('synapse-flare-active')) {
                localStorage.setItem('theme', 'synapse-flare');
            } else {
                localStorage.removeItem('theme');
            }
        }
        // Subtle visual feedback on click
        logo.style.transform = 'scale(0.95)';
        setTimeout(() => { logo.style.transform = 'scale(1)'; }, 150);
    });

    // Load saved theme
    if (localStorage.getItem('theme') === 'synapse-flare') {
        body.classList.add('synapse-flare-active');
    }
    
    // --- Harley's Konami Code Easter Egg ---
    const konamiArtElement = document.getElementById('konami-art');
    const konamiCanvas = document.getElementById('konami-canvas');
    // ASCII Art for Omnitide Nexus Symbol (simplified)
    const nexusAsciiArt = `
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    @@@@@@       @@@@@@@@@@@@@@@@@@@       @@@@@@
    @@@@     @@@@@@@@@@@@@@@@@@@@@@@@@@@     @@@@
    @@@    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@    @@@
    @@@  @@@@@@@                     @@@@@@@  @@@
    @@  @@@@@@@                       @@@@@@@  @@
    @@  @@@@@                           @@@@@  @@
    @  @@@@@                             @@@@@  @
    @  @@@@                               @@@@  @
    @  @@@                                 @@@  @
    @  @@@             OMNITIDE            @@@  @
    @  @@@              NEXUS              @@@  @
    @  @@@                                 @@@  @
    @  @@@@                               @@@@  @
    @  @@@@@                             @@@@@  @
    @@  @@@@@                           @@@@@  @@
    @@  @@@@@@@                       @@@@@@@  @@
    @@@  @@@@@@@                     @@@@@@@  @@@
    @@@    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@    @@@
    @@@@     @@@@@@@@@@@@@@@@@@@@@@@@@@@     @@@@
    @@@@@@       @@@@@@@@@@@@@@@@@@@       @@@@@@
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    `;
    if (konamiArtElement) konamiArtElement.textContent = nexusAsciiArt;

    document.addEventListener('keydown', (e) => {
        if (e.key === konamiCode[konamiIndex]) {
            konamiIndex++;
            if (konamiIndex === konamiCode.length) {
                konamiCanvas.style.display = 'block';
                setTimeout(() => {
                    konamiCanvas.style.display = 'none';
                }, 5000); // Display for 5 seconds
                konamiIndex = 0; // Reset
            }
        } else {
            konamiIndex = 0; // Reset if wrong key
        }
    });
    if(konamiCanvas) {
        konamiCanvas.addEventListener('click', () => konamiCanvas.style.display = 'none'); // Click to close
    }


    // Smooth scrolling for navigation links
    document.querySelectorAll('nav a[href^="#"]').forEach(link => {
        link.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href'))?.scrollIntoView({ behavior: 'smooth' });
        });
    });

    // --- Power's Dominance Level Indicator ---
    const dominanceBar = document.getElementById('dominance-indicator-bar');
    const dominanceLevelText = document.getElementById('dominance-level-text');
    let currentDominance = 0;
    function updateDominance(level) {
        currentDominance = Math.min(100, Math.max(0, level));
        if (dominanceBar) dominanceBar.style.width = currentDominance + '%';
        if (dominanceLevelText) dominanceLevelText.textContent = `${currentDominance.toFixed(0)}%`;
    }
    // Initial "charge up"
    setTimeout(() => updateDominance(25), 500);
    setTimeout(() => updateDominance(65), 1500);
    setTimeout(() => updateDominance(95), 2500); // Max visual impact

    // Increase dominance on scroll (simple example)
    let lastScrollTop = 0;
    window.addEventListener('scroll', () => {
        const st = window.pageYOffset || document.documentElement.scrollTop;
        if (st > lastScrollTop) { // Scrolling down
            updateDominance(currentDominance + 0.1);
        } else { // Scrolling up
            // updateDominance(currentDominance - 0.05); // Optional: decrease on scroll up
        }
        lastScrollTop = st <= 0 ? 0 : st; // For Mobile or negative scrolling
    }, false);


    // Copy button functionality
    document.querySelectorAll('.copy-button').forEach(button => {
        button.addEventListener('click', () => {
            const codeToCopy = button.previousElementSibling?.querySelector('code')?.innerText;
            if (codeToCopy) {
                navigator.clipboard.writeText(codeToCopy).then(() => {
                    button.innerText = 'Copied!';
                    setTimeout(() => { button.innerText = 'Copy'; }, 2000);
                }).catch(err => { button.innerText = 'Error'; });
            }
        });
    });

    // Core Team Persona Tooltip
    const teamMembers = document.querySelectorAll('.team-member');
    const tooltip = document.getElementById('persona-tooltip');
    const personaDetails = {
        'Stark': "<strong>Tony Stark (Engineering):</strong> Project analysis, feasibility, cutting-edge tech, elegant solutions.",
        'Lucy': "<strong>Lucy Kushinada (Security):</strong> Cybersecurity, data integrity, privacy, vulnerability assessment.",
        'Rick': "<strong>Rick Sanchez (Critique):</strong> Unconventional analysis, bullshit detection, radical efficiency.",
        'Rocket': "<strong>Rocket Raccoon (Resourcefulness):</strong> Practical engineering, improvisation, tool finding.",
        'Makima': "<strong>Makima (Strategy):</strong> Strategic alignment, control, long-term planning, protocol adherence.",
        'Yoda': "<strong>Yoda (Wisdom):</strong> Balance, ethics, TPC principles, simplicity, synergy.",
        'Momo': "<strong>Momo Ayase (Utility):</strong> User utility, practical solutions, empowerment, dev time estimation.",
        'Power': "<strong>Power (Impact):</strong> Boldness, dominance display, immediate high-impact results.",
        'Harley': "<strong>Harley Quinn (Innovation):</strong> Creative angles, user engagement, 'sparkle assurance', joyful disruption."
    };
    teamMembers.forEach(member => {
        member.addEventListener('mouseenter', (event) => {
            const persona = member.getAttribute('data-persona');
            if (personaDetails[persona] && tooltip) {
                tooltip.innerHTML = personaDetails[persona];
                tooltip.style.display = 'block';
                positionTooltip(event, tooltip);
            }
        });
        member.addEventListener('mouseleave', () => { if (tooltip) tooltip.style.display = 'none'; });
        member.addEventListener('mousemove', (event) => { if (tooltip && tooltip.style.display === 'block') positionTooltip(event, tooltip); });
    });

    function positionTooltip(event, tooltipElement) {
        let x = event.clientX + 20;
        let y = event.clientY + 20;
        if (x + tooltipElement.offsetWidth + 20 > window.innerWidth) x = event.clientX - tooltipElement.offsetWidth - 20;
        if (y + tooltipElement.offsetHeight + 20 > window.innerHeight) y = event.clientY - tooltipElement.offsetHeight - 20;
        tooltipElement.style.left = x + 'px';
        tooltipElement.style.top = y + 'px';
    }
    
    // Update current year in footer
    document.getElementById('currentYear').textContent = new Date().getFullYear();

    // --- Modal Logic ---
    function setupModal(modalId, openBtnId, closeBtnClass) {
        const modal = document.getElementById(modalId);
        const openBtn = document.getElementById(openBtnId);
        const closeBtn = modal?.querySelector(closeBtnClass);

        if (modal && openBtn && closeBtn) {
            openBtn.onclick = () => { modal.style.display = "block"; updateDominance(currentDominance + 2); }
            closeBtn.onclick = () => { modal.style.display = "none"; }
        }
        // Close modal if clicked outside content
        window.onclick = (event) => {
            if (event.target == modal) {
                modal.style.display = "none";
            }
        }
    }

    // --- Yoda's TPC Principle Reminder ---
    setupModal('yodaWisdomModal', 'tpc-wisdom-icon', '.yoda-close');
    const yodaQuoteEl = document.getElementById('yodaQuote');
    const yodaQuotes = [
        "TPC, it is. Necessary and sufficient, the code must be.",
        "Not too much, not too little. Exactly what is needed, find you must.",
        "Intuitive and functional, the path to clarity this is.",
        "Actionable and ready, your manifestations should be.",
        "The Ultimate Scaffolding, TPC demands. Complete, the ecosystem must be.",
        "Waste not tokens. Precision in language, power it brings."
    ];
    if (document.getElementById('tpc-wisdom-icon') && yodaQuoteEl) {
        document.getElementById('tpc-wisdom-icon').addEventListener('click', () => {
            yodaQuoteEl.textContent = yodaQuotes[Math.floor(Math.random() * yodaQuotes.length)];
        });
    }

    // --- Tony Stark: Nexus Project Analyzer ---
    setupModal('starkAnalyzerModal', 'projectAnalyzerBtn', '.stark-close');
    const starkProjectIdeaEl = document.getElementById('starkProjectIdea');
    const starkAnalyzeBtn = document.getElementById('starkAnalyzeBtn');
    const starkAnalysisResultEl = document.getElementById('starkAnalysisResult');

    if (starkAnalyzeBtn && starkProjectIdeaEl && starkAnalysisResultEl) {
        starkAnalyzeBtn.addEventListener('click', () => {
            const idea = starkProjectIdeaEl.value.trim().toLowerCase();
            let feasibility = Math.floor(Math.random() * 30) + 70; // 70-99%
            let innovation = Math.floor(Math.random() * 50) + 50; // 50-99%
            let resources = "Medium";

            if (idea.length < 10) {
                starkAnalysisResultEl.innerHTML = "<p style='color:var(--error-color)'>Jarvis says: 'Sir, the idea is... rather brief. More data required for a meaningful analysis.'<p>";
                return;
            }
            if (idea.includes("cat") || idea.includes("toy")) innovation = Math.min(100, innovation + 15);
            if (idea.includes("global") || idea.includes("enterprise")) feasibility -= 20;
            if (idea.includes("blockchain") || idea.includes("web3")) { feasibility -=10; innovation -=10; resources = "High (and probably questionable)";}
            if (idea.includes("simple") || idea.includes("utility")) { feasibility +=10; resources = "Low"; }
            
            starkAnalysisResultEl.innerHTML = `
                <p><strong>J.A.R.V.I.S. Preliminary Analysis for:</strong> "${starkProjectIdeaEl.value}"</p>
                <p><strong>Feasibility Score:</strong> ${feasibility}%</p>
                <p><strong>Innovation Potential:</strong> ${innovation}% (Stark Units)</p>
                <p><strong>Estimated Resources:</strong> ${resources}</p>
                <p style='font-style:italic; opacity:0.7; font-size:0.8em;'>Stark's Note: "Looks promising. Or utterly insane. Let's build a prototype by EOD."</p>
            `;
            updateDominance(currentDominance + 5);
        });
    }
    
    // --- Lucy Kushinada: Threat Vector Identifier ---
    setupModal('lucyThreatModal', 'threatVectorBtn', '.lucy-close');
    const lucySystemComponentEl = document.getElementById('lucySystemComponent');
    const lucyIdentifyBtn = document.getElementById('lucyIdentifyBtn');
    const lucyThreatResultEl = document.getElementById('lucyThreatResult');
    const threatVectors = {
        api: ["Injection (SQL, NoSQL, OS Command)", "Broken Authentication", "Sensitive Data Exposure", "XXE", "Broken Access Control", "Security Misconfiguration (e.g., verbose errors)", "Rate Limiting & DoS", "Insecure Deserialization"],
        database: ["SQL Injection", "Unpatched Vulnerabilities", "Weak Credentials/Defaults", "Excessive Privileges", "Lack of Encryption (at rest/transit)", "Insecure Backups", "Data Exposure via Misconfiguration"],
        auth: ["Weak Passwords", "Credential Stuffing", "Brute Force Attacks", "Session Hijacking", "Insecure Password Recovery", " mancanza di MFA", "OAuth/OIDC Misconfigurations"],
        frontend: ["XSS (Cross-Site Scripting)", "CSRF (Cross-Site Request Forgery)", "Clickjacking", "Insecure Direct Object References (IDOR)", "Dependency Vulnerabilities (JS libs)", "Content Security Policy (CSP) issues"],
        network: ["Unpatched Services", "Open/Unnecessary Ports", "Weak Segmentation", "Man-in-the-Middle (MitM) attacks", "Denial of Service (DoS/DDoS)", "Lateral Movement opportunities", "Poor Firewall Configuration"]
    };
    if (lucyIdentifyBtn && lucySystemComponentEl && lucyThreatResultEl) {
        lucyIdentifyBtn.addEventListener('click', () => {
            const component = lucySystemComponentEl.value;
            const vectors = threatVectors[component] || ["No specific vectors pre-defined for this component type."];
            let html = `<h4>Potential Threat Vectors for ${component.toUpperCase()}:</h4><ul>`;
            vectors.forEach(v => { html += `<li>${v}</li>`; });
            html += `</ul><p style='font-style:italic; opacity:0.7; font-size:0.8em;'>Lucy's Analysis: "Prioritize defense in depth. Assume breach. Log everything."</p>`;
            lucyThreatResultEl.innerHTML = html;
            updateDominance(currentDominance + 3);
        });
    }

    // --- Rick Sanchez: Buzzword De-BS-ifier ---
    const rickInputEl = document.getElementById('rickInput');
    const rickBtn = document.getElementById('rickBtn');
    const rickOutputEl = document.getElementById('rickOutput');
    const rickDictionary = {
        "synergy": "buuurp... cooperation, I guess", "leverage": "use", "paradigm shift": "a new idea, maybe",
        "disruptive innovation": "something new that breaks old stuff", "next generation": "the new one",
        "value proposition": "what it's good for", "core competency": "what we're actually good at",
        "deep dive": "actually look at it", "thought leader": "loudmouth", "low-hanging fruit": "easy stuff",
        "future-proof": "won't break tomorrow (yeah, right)", "agile": "we make it up as we go",
        "cloud-native": "runs on someone else's computer", "AI-powered": "probably just a bunch of if-statements",
        "blockchain": "slow database with extra steps", "metaverse": "sad VR chatroom", "web3": "see blockchain",
        "digital transformation": "buying new software", "hyper-scale": "really, really big... or not"
    };
    if (rickBtn && rickInputEl && rickOutputEl) {
        rickBtn.addEventListener('click', () => {
            let text = rickInputEl.value;
            if (!text.trim()) {
                rickOutputEl.textContent = "Rick says: 'You expect me to de-BS-ify NOTHING? Get outta here!'";
                return;
            }
            for (const buzzword in rickDictionary) {
                const regex = new RegExp(`\\b${buzzword}\\b`, 'gi'); // Case insensitive, whole word
                text = text.replace(regex, rickDictionary[buzzword]);
            }
            rickOutputEl.textContent = `Rick's Translation: "${text}" \n\nMorty, it's still mostly gibberish, but slightly less pretentious gibberish.`;
            updateDominance(currentDominance + 1);
        });
    }

    // --- Rocket Raccoon: Scrapyard Scavenger ---
    const rocketProblemSelectEl = document.getElementById('rocketProblemSelect');
    const rocketBtn = document.getElementById('rocketBtn');
    const rocketOutputEl = document.getElementById('rocketOutput');
    const rocketToolbox = {
        webserver: [
            { name: "Python http.server", cmd: "python -m http.server 8000", desc: "Simple, built-in Python server." },
            { name: "Node http-server", cmd: "npx http-server .", desc: "Quick Node.js based server." },
            { name: "Caddy", cmd: "caddy file-server --browse", desc: "Powerful, auto-HTTPS server."}
        ],
        jsonparse: [
            { name: "jq", cmd: "cat file.json | jq '.key'", desc: "CLI JSON processor. Powerful." },
            { name: "Python json.tool", cmd: "python -m json.tool file.json", desc: "Validate & pretty-print JSON." }
        ],
        sysmon: [
            { name: "htop", cmd: "htop", desc: "Interactive process viewer." },
            { name: "vmstat", cmd: "vmstat 1 5", desc: "Report virtual memory statistics (1 sec interval, 5 times)." },
            { name: "iostat", cmd: "iostat -xz 1", desc: "Report CPU and I/O statistics."}
        ]
    };
    if (rocketBtn && rocketProblemSelectEl && rocketOutputEl) {
        rocketBtn.addEventListener('click', () => {
            const problem = rocketProblemSelectEl.value;
            if (!problem) {
                rocketOutputEl.innerHTML = "Rocket says: 'Ya gotta pick a problem, ya flarkin' idiot!'"; return;
            }
            const tools = rocketToolbox[problem];
            let html = `Rocket's Picks for "${problem}":<ul>`;
            tools.forEach(t => {
                html += `<li><strong>${t.name}:</strong> ${t.desc}<br><code class="inline-code">${t.cmd}</code></li>`;
            });
            html += `</ul><p style='font-style:italic; opacity:0.7; font-size:0.8em;'>Rocket's Note: "These'll get ya started. Don't blow anything up... unless that's the goal."</p>`;
            rocketOutputEl.innerHTML = html;
            updateDominance(currentDominance + 1);
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
            if (isNaN(tasks) || tasks <= 0) {
                momoOutputEl.textContent = "Momo says: Please enter a valid number of tasks!"; return;
            }
            let baseHoursPerTask;
            switch (complexity) {
                case 'low': baseHoursPerTask = 2; break;
                case 'medium': baseHoursPerTask = 5; break;
                case 'high': baseHoursPerTask = 10; break;
                default: baseHoursPerTask = 4;
            }
            const minHours = tasks * baseHoursPerTask * 0.8; // 80% for optimistic
            const maxHours = tasks * baseHoursPerTask * 1.5; // 150% for pessimistic + meetings
            momoOutputEl.innerHTML = `
                <p>Momo's Estimate for ${tasks} task(s) of ${complexity} complexity:</p>
                <p><strong>Roughly: ${minHours.toFixed(1)} - ${maxHours.toFixed(1)} hours</strong></p>
                <p style='font-style:italic; opacity:0.7; font-size:0.8em;'>Momo's Note: "Remember to add time for testing, unexpected issues, and maybe a tea break! Good luck, Architect!"</p>
            `;
            updateDominance(currentDominance + 1);
        });
    }

    // --- Makima: Strategic Nexus Alignment ---
    setupModal('makimaAlignmentModal', 'strategicAlignmentBtn', '.makima-close');
    const makimaAssessBtn = document.getElementById('makimaAssessBtn');
    const makimaAlignmentResultEl = document.getElementById('makimaAlignmentResult');

    if (makimaAssessBtn && makimaAlignmentResultEl) {
        makimaAssessBtn.addEventListener('click', () => {
            const principles = document.querySelectorAll('input[name="alignmentPrinciple"]:checked');
            let score = 0;
            let feedback = "<h4>Makima's Strategic Assessment:</h4>";
            const totalPrinciples = 4; // Keep this updated if you add more checkboxes

            principles.forEach(p => {
                score++;
                feedback += `<p style='color:var(--success-color)'>✓ Aligns with: ${p.value}</p>`;
            });

            const alignmentPercentage = (score / totalPrinciples) * 100;
            feedback += `<p><strong>Overall Nexus Alignment Score: ${alignmentPercentage.toFixed(0)}%</strong></p>`;

            if (alignmentPercentage < 50) {
                feedback += "<p style='color:var(--warning-color)'>Consider refining project goals for stronger Nexus synergy. Control is key.</p>";
            } else if (alignmentPercentage < 100) {
                feedback += "<p style='color:var(--tertiary-accent)'>Good alignment. Potential for greater strategic impact exists.</p>";
            } else {
                feedback += "<p style='color:var(--primary-accent)'>Excellent. This project is a direct manifestation of Nexus will.</p>";
            }
            feedback += "<p style='font-style:italic; opacity:0.7; font-size:0.8em;'>Makima's Directive: \"Ensure all endeavors ultimately serve the Architect's overarching vision for the Nexus.\"</p>";
            makimaAlignmentResultEl.innerHTML = feedback;
            updateDominance(currentDominance + 4);
        });
    }


    // --- Harley's Dynamic Nexus Visualizer (Hero) ---
    const visualizer = document.getElementById('nexus-visualizer-v2');
    if (visualizer) {
        const numParticles = 25; // More particles for Harley!
        for (let i = 0; i < numParticles; i++) {
            const p = document.createElement('div');
            p.classList.add('particle');
            p.style.width = p.style.height = `${Math.random() * 4 + 2}px`; // Vary size
            p.style.left = `${Math.random() * 100}%`;
            p.style.top = `${Math.random() * 100}%`;
            // Custom properties for animation variance
            p.style.setProperty('--dx', `${Math.random() * 40 - 20}px`); // Random drift x
            p.style.setProperty('--dy', `${Math.random() * 40 - 20}px`); // Random drift y
            p.style.animationDelay = `${Math.random() * 5}s`;
            p.style.animationDuration = `${Math.random() * 10 + 10}s`; // Longer, varied drift
            p.style.backgroundColor = Math.random() > 0.66 ? varCss('--primary-accent') : (Math.random() > 0.5 ? varCss('--secondary-accent') : varCss('--tertiary-accent'));
            visualizer.appendChild(p);
        }
    }
    // Helper to get CSS var values in JS
    function varCss(varName) { return getComputedStyle(document.documentElement).getPropertyValue(varName).trim(); }


    console.log("Architect's Digital Manifest v2.0 JS Fully Initialized. All systems nominal. Harley was here!");
});