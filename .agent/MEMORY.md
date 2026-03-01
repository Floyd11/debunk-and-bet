# Debunk & Bet - Project Memory

## 1. Project Overview
"Debunk & Bet" is a web application that helps users analyze Polymarket events by gathering news context and using an LLM to determine the actual likelihood of an event occurring.
- **Goal:** Provide an "AI Verdict" (Yes / No / Uncertain) with reasoning, odds, and verifiable inference for Polymarket markets.

## 2. Architecture & Tech Stack
- **Backend:** FastAPI (Python 3) serving a REST API and static files.
- **Frontend:** Vanilla HTML/JS with Tailwind CSS (served statically from `static/index.html`).
- **Data Integrations:**
  - **Polymarket Gamma API:** Fetches event details, rules, and current market odds given an event URL.
  - **DuckDuckGo Search:** Gathers latest news and context related to the event (Replaced Google/X APIs for rate limit reasons).
  - **OpenGradient LLM:** Analyzes the market rules and DuckDuckGo context using `og.TEE_LLM.CLAUDE_SONNET_4_5`. It generates an AI Verdict along with the transaction hash for the TEE (Trusted Execution Environment) proof.

## 3. Project State
- ✅ **Core Implementation:** Complete `/analyze` endpoint integrating all 3 services.
- ✅ **Frontend:** Basic UI with input, loader, and results rendering.
- ✅ **Error Handling:** Robust error management for APIs and LLM timeouts.
- ✅ **Version Control:** Pushed to GitHub repository.
- 🔧 **Next Steps:** Open for new features, extended testing, or UI improvements.

## 4. Environment Variables
Requires an `.env` file with:
- `OPENGRADIENT_PRIVATE_KEY`

## 5. Major Decisions
- Transitioned from Google Custom Search/X API to `duckduckgo-search` for free and rate-limit-free context gathering.
- Re-assigned LLM fallback for non-strict JSON to ensure stable API responses (`app/services/opengradient_client.py`).
