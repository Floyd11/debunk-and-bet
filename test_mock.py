from app.models import AnalyzeResponse

def mock_analyze_route():
    # User Request: true_probability_yes = 15, market_prob_yes = 73
    true_probability_yes = 15
    market_prob_yes = 73
    
    # Logic from app/main.py
    if true_probability_yes > market_prob_yes:
        recommended_bet = "YES"
    elif true_probability_yes < market_prob_yes:
        recommended_bet = "NO"
    else:
        recommended_bet = "SKIP"
        
    edge = abs(true_probability_yes - market_prob_yes)
    
    # Mock OpenGradient LLM Output CoT
    mock_llm_output = {
        "true_probability_yes": true_probability_yes,
        "base_rate_analysis": "Historically, 20% of crypto companies sell Bitcoin after buying.",
        "pro_yes_arguments": ["Strong statements from Michael Saylor.", "Market pressure."],
        "pro_no_arguments": ["MSTR has never sold Bitcoin.", "Treasury reserve model."],
        "information_gap": "We don't know Q4 2025 earnings yet.",
        "synthesis": "Given the base rate and overwhelming evidence to hold, the probability is 15%.",
        "wallet_address": "0xABCDEF123456"
    }

    # Expected assertion values
    assert recommended_bet == "NO", f"Expected NO, got {recommended_bet}"
    assert edge == 58, f"Expected edge to be 58, got {edge}"

    # Pydantic schema validation test
    try:
        response = AnalyzeResponse(
            market_question="Will MicroStrategy sell any Bitcoin in 2025?",
            recommended_bet=recommended_bet,
            ai_event_probability=true_probability_yes,
            market_probability=market_prob_yes,
            edge=edge,
            base_rate_analysis=mock_llm_output.get("base_rate_analysis", ""),
            pro_yes_arguments=mock_llm_output.get("pro_yes_arguments", []),
            pro_no_arguments=mock_llm_output.get("pro_no_arguments", []),
            information_gap=mock_llm_output.get("information_gap", ""),
            synthesis=mock_llm_output.get("synthesis", ""),
            sources=["https://bloomberg.com/mstr"],
            verification_proof="https://sepolia.basescan.org/address/0xABCDEF123456#tokentxns"
        )
        print("✅ SUCCESS: Schema validation passed.")
        print("✅ SUCCESS: Logics passed -> edge:", edge, " recommended_bet:", recommended_bet)
    except Exception as e:
        print("❌ FAILED: Schema validation threw an error!")
        print(e)
        raise e

if __name__ == "__main__":
    mock_analyze_route()
