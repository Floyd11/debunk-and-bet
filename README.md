# Debunk & Bet - Polymarket Fact-Checker

An AI-powered application that assesses Polymarket probabilities by fetching live news context via Google Search/X API and verifying facts through the OpenGradient LLM.

## Architecture
- **Backend:** Python + FastAPI
- **Search Provider:** DuckDuckGo Search (via `duckduckgo-search`)
- **AI Verification:** OpenGradient SDK (meta-llama/Meta-Llama-3-70B-Instruct)
- **Frontend:** Vanilla HTML/JS directly served by FastAPI + Tailwind CSS

## Prerequisites
- Python 3.10+
- OpenGradient Private Key

## Setup & Run Locally

1. **Clone and setup virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Or `venv\Scripts\activate` on Windows
   ```

2. **Install requirements**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**
   Rename `.env.example` to `.env` and fill in your API keys:
   ```env
   OPENGRADIENT_PRIVATE_KEY="your_private_key_here"
   ```

4. **Run the Application**
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Open in Browser**
   Navigate to `http://localhost:8000`

## Testing
To run the basic service tests:
```bash
pytest tests.py
```