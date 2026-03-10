import os
from dotenv import load_dotenv
import opengradient as og
import json
from typing import Dict, Any, Tuple
from datetime import datetime

load_dotenv()

PRIVATE_KEY = os.getenv("OPENGRADIENT_PRIVATE_KEY")

def rewrite_query_with_llm(question: str) -> list[str]:
    """
    Uses OpenGradient LLM to convert a Polymarket question into 2-3 targeted English search queries.
    """
    if not PRIVATE_KEY:
        raise ValueError("OPENGRADIENT_PRIVATE_KEY is not set.")
        
    client = og.init(private_key=PRIVATE_KEY)
    
    system_prompt = (
        "You are an expert intelligence gatherer. Convert the given prediction market question into exactly 3 highly targeted English-language search queries. "
        "RULES: "
        "1. Query 1: Official/primary source query. For corporate events use company name + official action + year. Example: 'MicroStrategy Bitcoin purchase announcement March 2026 strategy.com' "
        "2. Query 2: News aggregator query. Use major news outlets keywords. Example: 'MicroStrategy MSTR Bitcoin buy 2026 site:coindesk.com OR site:bloomberg.com' "
        "3. Query 3: Broad recent news query with current year. "
        "CRITICAL: Always include the current year in ALL queries. "
        "Return the output STRICTLY as a raw JSON list of 3 strings, nothing else."
    )
    
    current_year = datetime.now().year
    user_prompt = f"Current Year: {current_year}\nQuestion: {question}"
    
    try:
        response = client.llm.chat(
            model=og.TEE_LLM.CLAUDE_SONNET_4_5,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=300
        )
        
        answer = response.chat_output
        if isinstance(answer, dict) and "content" in answer:
            answer = answer["content"]
            
        if isinstance(answer, str):
            if "```json" in answer:
                 answer = answer.split("```json")[1].split("```")[0].strip()
            elif "```" in answer:
                 answer = answer.split("```")[1].split("```")[0].strip()
            queries = json.loads(answer)
        elif isinstance(answer, list):
            queries = answer
        else:
            queries = [question]
            
        if not isinstance(queries, list) or len(queries) == 0:
            queries = [question]
            
        return [str(q) for q in queries][:3]
    except Exception as e:
        print(f"Error rewriting query: {e}")
        return [question]

def analyze_with_llm(question: str, rules: str, odds: Dict[str, float], context: str) -> Tuple[int, str, str]:
    """
    Uses OpenGradient to analyze the market and return the true probability.
    Returns: (true_probability_yes, reasoning, verification_proof)
    """
    if not PRIVATE_KEY:
        raise ValueError("OPENGRADIENT_PRIVATE_KEY is not set in the environment.")

    client = og.init(private_key=PRIVATE_KEY)
    
    try:
        client.llm.ensure_opg_approval(opg_amount=5)
    except Exception as e:
        print(f"Warning: OPG approval check issue: {e}")

    system_prompt = "You are a highly advanced Superforecaster AI."

    current_date = datetime.now().strftime("%B %d, %Y")

    user_prompt = f"""
You are an expert superforecaster, known for your high accuracy, emotional detachment, and excellent calibration (similar to Philip Tetlock's superforecasters).
Your task is to estimate the true probability (0-100%) that the following Polymarket event will resolve as "YES".
CRITICAL TEMPORAL ANCHOR: Today's date is {current_date}. All news context provided must be evaluated relative to this exact date. Any events in the news that supposedly happened in the future (after {current_date}) are likely reporting errors or misinterpretations of historical data and should be heavily scrutinized or discarded.

Event Details:
Title: {question}
Resolution Criteria: {rules}

Verified News & Context:
{context}

Strict Instructions:
You must think step-by-step. Do not rush to a conclusion. Do not consider current market odds. Focus ONLY on the likelihood of the event resolving to 'YES'.
When analyzing the Verified News & Context, give the absolute highest weight to events listed under [🔴 URGENT: LAST 24 HOURS]. Breaking news, military actions, and recent official statements supersede historical context. Use the background data only to understand the baseline.

Base Rate Analysis: What is the historical base rate for events of this exact type? If this is a novel event, what is the closest historical analogue?

Evidence for YES: List the strongest factual arguments from the context supporting the event happening.

Evidence for NO: List the strongest factual arguments from the context against the event happening.

Information Gap: What crucial information is missing that could change the outcome?

Probability Synthesis: Start from the base rate and explicitly adjust it based on the weight of the evidence for YES vs NO.

Final Output Format:
CRITICAL INSTRUCTION: You are strictly constrained by output tokens. You must keep all text fields compact to prevent JSON truncation. Ensure your reasoning is highly dense.

Return your response STRICTLY as a raw JSON object. Use this exact schema:
{{
"hidden_thought_process": "<string> Use this field as your scratchpad. Think out loud, weigh the evidence deeply, and do your raw analytical math here. STRICT LIMIT: UNDER 150 WORDS. Be extremely dense.",
"base_rate_analysis": "<string> A concise 2-3 sentence summary for the UI.",
"pro_yes_arguments": ["<string> Concise argument (max 2 sentences)", "<string> Concise argument (max 2 sentences)"],
"pro_no_arguments": ["<string> Concise argument (max 2 sentences)", "<string> Concise argument (max 2 sentences)"],
"information_gap": "<string> A concise 2-3 sentence summary.",
"synthesis": "<string> A concise 3-4 sentence final verdict for the UI.",
"true_probability_yes": <int 0-100>
}}
"""

    try:
        response = client.llm.chat(
            model=og.TEE_LLM.CLAUDE_SONNET_4_5, 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3, # Low temp for factual analysis
            max_tokens=4096
        )
        
        tx_hash = response.transaction_hash
        answer = response.chat_output
        
        # Try to parse JSON from response
        try:
             print(f"DEBUG RAW OUTPUT: {repr(answer)}")
             # Some SDK versions return a dict with 'content'
             if isinstance(answer, dict) and "content" in answer:
                 answer = answer["content"]
             elif isinstance(answer, dict):
                 # fallback if it was already the exact dict
                 pass
             
             if isinstance(answer, str):
                 # Find start of JSON block if LLM added markdown wrappers
                 import re
                 # Aggressively remove ```json and ``` or any leading/trailing non-json text
                 match = re.search(r'(?s:\{.*\})', answer)
                 if match:
                     answer = match.group(0)
                 else:
                     # Fallback string manipulation
                     answer = answer.strip()
                     if answer.startswith("```json"):
                         answer = answer[7:]
                     if answer.startswith("```"):
                         answer = answer[3:]
                     if answer.endswith("```"):
                         answer = answer[:-3]
                     answer = answer.strip()
                     
                 result_data = json.loads(answer)
             elif isinstance(answer, dict) and "true_probability_yes" in answer:
                 result_data = answer
             else:
                 result_data = {}
                 
             # Enforce bounds
             try:
                 true_prob = int(float(result_data.get("true_probability_yes", 50)))
                 result_data["true_probability_yes"] = max(0, min(100, true_prob))
             except (ValueError, TypeError):
                 result_data["true_probability_yes"] = 50
                  
             wallet_address = client.llm._wallet_account.address
             result_data["wallet_address"] = wallet_address
             return result_data
             
        except json.JSONDecodeError:
             # Fallback if the LLM didn't return strict JSON
             wallet_address = client.llm._wallet_account.address if 'client' in locals() else "0xERROR"
             return {
                 "true_probability_yes": 50,
                 "base_rate_analysis": "The network generated an overly detailed response that exceeded the maximum allowed length, resulting in a truncated analysis. Please try the request again.",
                 "pro_yes_arguments": ["Response truncated due to length limits."],
                 "pro_no_arguments": ["Response truncated due to length limits."],
                 "information_gap": "Truncated response.",
                 "synthesis": "Analysis could not be fully completed due to length constraints.",
                 "wallet_address": wallet_address
             }
             
    except Exception as e:
        print(f"Error during OpenGradient inference: {e}")
        return {
            "true_probability_yes": 50,
            "base_rate_analysis": "An error occurred while connecting to the OpenGradient network.",
            "pro_yes_arguments": [],
            "pro_no_arguments": [],
            "information_gap": "Connection error.",
            "synthesis": "Connection error.",
            "wallet_address": "0xERROR"
        }
