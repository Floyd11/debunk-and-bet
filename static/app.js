document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('analyze-form');
    const input = document.getElementById('market-url');
    const submitBtn = document.getElementById('submit-btn');

    const loadingIndicator = document.getElementById('loadingIndicator');
    const loadingText = document.getElementById('loadingText');
    const verdictContainer = document.getElementById('verdict-container');
    const detailedContainer = document.getElementById('detailed-analysis-container');
    const disclaimerText = document.getElementById('disclaimer-text');
    const errorContainer = document.getElementById('error-container');
    const errorText = document.getElementById('error-text');

    // Verdict nodes
    const resQuestion = document.getElementById('res-question');
    const resVerdictBox = document.getElementById('res-verdict-box');
    const resVerdict = document.getElementById('res-verdict');
    const resVerdictDivider = document.getElementById('res-verdict-divider');
    const resAiProb = document.getElementById('res-ai-prob');
    const resMarketProb = document.getElementById('res-market-prob');
    const resEdge = document.getElementById('res-edge');
    const resSynthesisMain = document.getElementById('res-synthesis-main');

    // Detailed nodes
    const resBaseRate = document.getElementById('res-base-rate');
    const resProYes = document.getElementById('res-pro-yes');
    const resProNo = document.getElementById('res-pro-no');
    const resInfoGap = document.getElementById('res-info-gap');
    const resSynthesisFull = document.getElementById('res-synthesis-full');
    const resSources = document.getElementById('res-sources');
    const resProof = document.getElementById('res-proof');

    // Toggler
    const toggleDetailedBtn = document.getElementById('toggle-detailed-btn');
    const toggleDetailedText = document.getElementById('toggle-detailed-text');
    const toggleDetailedIcon = document.getElementById('toggle-detailed-icon');

    const loadingStages = [
        "Fetching market rules and odds from Polymarket...",
        "Rewriting query for optimal research...",
        "Gathering fresh news context from trusted sources...",
        "Sending encrypted payload to OpenGradient TEE...",
        "Waiting for AI Analysis...",
        "Calculating Edge..."
    ];

    // Accordions Toggle Event Logic structure natively handled by <details> tag in HTML5
    // But we need to handle the "Detailed Analysis" hidden state
    toggleDetailedBtn.addEventListener('click', (e) => {
        e.preventDefault();
        const isHidden = detailedContainer.classList.contains('hidden');
        if (isHidden) {
            detailedContainer.classList.remove('hidden');
            toggleDetailedText.textContent = "Hide Detailed Analysis";
            toggleDetailedIcon.textContent = "arrow_upward";
        } else {
            detailedContainer.classList.add('hidden');
            toggleDetailedText.textContent = "View Detailed Analysis";
            toggleDetailedIcon.textContent = "arrow_downward";
        }
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const url = input.value.trim();

        if (!url) return;

        // Reset UI to Loading State
        verdictContainer.classList.add('hidden');
        detailedContainer.classList.add('hidden');
        disclaimerText.classList.add('hidden');
        errorContainer.classList.add('hidden');
        errorText.textContent = '';

        // Reset toggle to default
        toggleDetailedText.textContent = "View Detailed Analysis";
        toggleDetailedIcon.textContent = "arrow_downward";

        loadingIndicator.classList.remove('hidden');
        loadingIndicator.classList.add('flex');

        submitBtn.disabled = true;
        input.disabled = true;
        const orgBtnText = submitBtn.textContent;
        submitBtn.textContent = "Analyzing...";

        // Fun loading text loop
        let stage = 0;
        loadingText.textContent = loadingStages[0];
        const loadingInterval = setInterval(() => {
            stage = (stage + 1) % loadingStages.length;
            loadingText.textContent = loadingStages[stage];
        }, 3000);

        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url })
            });

            if (!response.ok) {
                // Handle non-JSON responses (e.g. 504 Gateway Timeout HTML)
                const contentType = response.headers.get("content-type");
                if (contentType && contentType.includes("application/json")) {
                    const errData = await response.json();
                    throw new Error(errData.detail || "Server error occurred.");
                } else {
                    const errText = await response.text();
                    console.error("Non-JSON Server Error:", errText);
                    if (response.status === 504) {
                        throw new Error("Analysis took too long (Gateway Timeout). Please try again.");
                    }
                    throw new Error(`Server returned status ${response.status}.`);
                }
            }

            const data = await response.json();

            // Note: `hidden_thought_process` exists in the payload but is intentionally ignored

            // State 3: Populate and Show Verdict
            resQuestion.textContent = data.market_question;

            // Base styling reset for the verdict box
            resVerdictBox.className = "w-full md:w-1/3 flex flex-col items-center justify-center p-8 rounded-xl border-2";
            resVerdictDivider.className = "w-full space-y-3 pt-6 border-t";
            resVerdict.className = "text-6xl font-black mb-6";
            resEdge.className = "font-bold";

            resVerdict.textContent = data.recommended_bet;
            resAiProb.textContent = `${data.ai_event_probability}%`;
            resMarketProb.textContent = `${data.market_probability}%`;
            resEdge.textContent = `${data.edge}%`;

            if (data.recommended_bet === "YES") {
                resVerdictBox.classList.add("bg-[#162e24]", "border-[#162e24]");
                resVerdict.classList.add("text-[#22c55e]");
                resVerdictDivider.classList.add("border-[#22c55e]/20");
                resEdge.classList.add("text-[#22c55e]");
            } else if (data.recommended_bet === "NO") {
                resVerdictBox.classList.add("bg-[#4c1d24]", "border-[#4c1d24]");
                resVerdict.classList.add("text-[#ef4444]");
                resVerdictDivider.classList.add("border-[#ef4444]/20");
                resEdge.classList.add("text-[#ef4444]");
            } else {
                resVerdictBox.classList.add("bg-slate-800", "border-slate-700");
                resVerdict.classList.add("text-white");
                resVerdictDivider.classList.add("border-slate-600/50");
                resEdge.classList.add("text-[#a855f7]");
            }

            // Text content
            resSynthesisMain.textContent = data.synthesis || "No synthesis available.";

            // Detailed Analysis population
            resBaseRate.textContent = data.base_rate_analysis || "No base rate provided.";

            resProYes.innerHTML = '';
            if (data.pro_yes_arguments && data.pro_yes_arguments.length > 0) {
                data.pro_yes_arguments.forEach(arg => { resProYes.innerHTML += `<li>${arg}</li>`; });
            } else { resProYes.innerHTML = '<li>None identified.</li>'; }

            resProNo.innerHTML = '';
            if (data.pro_no_arguments && data.pro_no_arguments.length > 0) {
                data.pro_no_arguments.forEach(arg => { resProNo.innerHTML += `<li>${arg}</li>`; });
            } else { resProNo.innerHTML = '<li>None identified.</li>'; }

            resInfoGap.textContent = data.information_gap || "None identified.";
            resSynthesisFull.textContent = data.synthesis || "No synthesis available.";

            // Sources
            resSources.innerHTML = '';
            if (data.context_sources && data.context_sources.length > 0) {
                data.context_sources.forEach(src => {
                    let domain = src;
                    try {
                        domain = new URL(src).hostname.replace('www.', '');
                    } catch (e) { }

                    resSources.innerHTML += `
                        <a href="${src}" target="_blank" class="hover:text-white transition-colors underline decoration-slate-600 underline-offset-2">
                            ${domain}
                        </a>
                    `;
                });
            } else {
                resSources.innerHTML = '<span class="text-slate-500">No external sources cited.</span>';
            }

            // TX Proof link
            if (data.verification_proof) {
                resProof.href = data.verification_proof;
                resProof.style.display = "inline-block";
                const shortTx = data.verification_proof.split('/').pop();
                resProof.title = shortTx;
                resProof.textContent = "View Tx";
            } else {
                resProof.style.display = "none";
            }

            verdictContainer.classList.remove('hidden');
            disclaimerText.classList.remove('hidden');

        } catch (error) {
            verdictContainer.classList.add('hidden');
            detailedContainer.classList.add('hidden');
            errorText.textContent = error.message.replace('Error: ', '');
            errorContainer.classList.remove('hidden');
        } finally {
            clearInterval(loadingInterval);
            loadingIndicator.classList.add('hidden');
            loadingIndicator.classList.remove('flex');
            submitBtn.disabled = false;
            input.disabled = false;
            submitBtn.textContent = orgBtnText;
        }
    });
});
