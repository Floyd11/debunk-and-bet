document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('analyze-form');
    const input = document.getElementById('market-url');
    const submitBtn = document.getElementById('submit-btn');

    const loadingIndicator = document.getElementById('loadingIndicator');
    const loadingText = document.getElementById('loadingText');
    const resultsDiv = document.getElementById('results');

    const resQuestion = document.getElementById('res-question');
    const resOddsContainer = document.getElementById('res-odds-container');
    const resVerdictBox = document.getElementById('verdict-box');
    const resVerdict = document.getElementById('res-verdict');
    const resReasoning = document.getElementById('res-reasoning');
    const resSources = document.getElementById('res-sources');
    const resProof = document.getElementById('res-proof');

    const loadingStages = [
        "Fetching market rules and odds from Polymarket...",
        "Gathering fresh news context from Google & X...",
        "Sending encrypted payload to OpenGradient TEE...",
        "Waiting for AI Verdict...",
        "Finalizing reasoning..."
    ];

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const url = input.value.trim();

        if (!url) return;

        // Reset UI
        resultsDiv.classList.add('hidden');
        loadingIndicator.classList.remove('hidden');
        loadingIndicator.classList.add('flex');
        submitBtn.disabled = true;

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
                const errData = await response.json();
                throw new Error(errData.detail || "Server error occurred.");
            }

            const data = await response.json();

            // Populate Results
            resQuestion.textContent = data.market_question;

            // Odds
            resOddsContainer.innerHTML = '';
            for (const [outcome, price] of Object.entries(data.current_odds)) {
                const percentage = (price * 100).toFixed(1) + "%";
                resOddsContainer.innerHTML += `
                    <div class="px-4 py-2 bg-gray-800 rounded-lg border border-gray-700">
                        <span class="text-sm text-gray-400 mr-2">${outcome}:</span>
                        <span class="font-bold text-white">${percentage}</span>
                    </div>
                `;
            }

            // Verdict Styling
            resVerdict.textContent = data.ai_verdict;
            resVerdictBox.className = "col-span-1 border rounded-xl p-6 flex flex-col items-center justify-center text-center";

            if (data.ai_verdict === "Yes") {
                resVerdictBox.classList.add("bg-green-900/20", "border-green-500/50");
                resVerdict.classList.add("text-green-400");
            } else if (data.ai_verdict === "No") {
                resVerdictBox.classList.add("bg-red-900/20", "border-red-500/50");
                resVerdict.classList.add("text-red-400");
            } else {
                resVerdictBox.classList.add("bg-gray-800/50", "border-gray-600");
                resVerdict.classList.add("text-gray-300");
            }

            // Reasoning
            resReasoning.textContent = data.reasoning;

            // Sources
            resSources.innerHTML = '';
            if (data.sources && data.sources.length > 0) {
                data.sources.forEach(src => {
                    // Try to make a clean domain name
                    let domain = src;
                    try {
                        domain = new URL(src).hostname.replace('www.', '');
                    } catch (e) { }

                    resSources.innerHTML += `
                        <li>
                            <a href="${src}" target="_blank" class="text-blue-400 hover:text-blue-300 hover:underline flex items-center gap-2">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg>
                                ${domain}
                            </a>
                        </li>
                    `;
                });
            } else {
                resSources.innerHTML = '<li class="text-gray-500">No external sources cited.</li>';
            }

            // Proof
            resProof.href = data.verification_proof;

            // Show results
            resultsDiv.classList.remove('hidden');

        } catch (error) {
            alert(`Error: ${error.message}`);
        } finally {
            clearInterval(loadingInterval);
            loadingIndicator.classList.add('hidden');
            loadingIndicator.classList.remove('flex');
            submitBtn.disabled = false;
        }
    });
});
