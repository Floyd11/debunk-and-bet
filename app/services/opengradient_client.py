import os
from dotenv import load_dotenv
import opengradient as og
import json
from typing import Dict, Any, Tuple

load_dotenv()

PRIVATE_KEY = os.getenv("OPENGRADIENT_PRIVATE_KEY")

def analyze_with_llm(question: str, rules: str, odds: Dict[str, float], context: str) -> Tuple[str, str, str]:
    """
    Uses OpenGradient to analyze the market and return an AI verdict.
    Returns: (ai_verdict, reasoning, verification_proof)
    """
    if not PRIVATE_KEY:
        raise ValueError("OPENGRADIENT_PRIVATE_KEY is not set in the environment.")

    client = og.init(private_key=PRIVATE_KEY)
    
    try:
        client.llm.ensure_opg_approval(opg_amount=5)
    except Exception as e:
        print(f"Warning: OPG approval check issue: {e}")

    system_prompt = (
        "Ты — независимый финансовый аналитик и факт-чекер. Оцени рынок предсказаний Polymarket. "
        "Тебе дано название рынка, правила, текущие шансы и последние новости. "
        "Сделай вывод: событие скорее произойдет (Yes), скорее не произойдет (No), или данных недостаточно (Uncertain). "
        "Свой ответ строго форматируй в JSON с двумя полями: 'ai_verdict' (значения: 'Yes', 'No', или 'Uncertain') и 'reasoning' (краткий анализ)."
    )

    user_prompt = f"""
    Рынок: {question}
    Правила: {rules}
    Текущие коэффициенты (шансы): {json.dumps(odds)}
    
    Последние новости / Контекст:
    {context}
    """

    try:
        response = client.llm.chat(
            model=og.TEE_LLM.CLAUDE_SONNET_4_5, 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3, # Low temp for factual analysis
            max_tokens=1024
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
                 if "```json" in answer:
                     answer = answer.split("```json")[1].split("```")[0].strip()
                 elif "```" in answer:
                     answer = answer.split("```")[1].split("```")[0].strip()
                     
                 result_data = json.loads(answer)
             elif isinstance(answer, dict) and "ai_verdict" in answer:
                 result_data = answer
             else:
                 result_data = {}
                 
             verdict = result_data.get("ai_verdict", "Uncertain")
             reasoning = result_data.get("reasoning", "No analysis provided.")
             
             # Validate verdict
             if verdict not in ["Yes", "No", "Uncertain"]:
                  original_verdict = verdict
                  verdict = "Uncertain"
                  reasoning += f" (Note: Original verdict was {original_verdict})"
                  
             return verdict, reasoning, tx_hash
        except json.JSONDecodeError:
             # Fallback if the LLM didn't return strict JSON
             return "Uncertain", f"Analysis block could not be parsed as JSON. Raw answer: {answer}", tx_hash
             
    except Exception as e:
        print(f"Error during OpenGradient inference: {e}")
        return "Uncertain", "An error occurred while connecting to the OpenGradient network.", "0xERROR"
