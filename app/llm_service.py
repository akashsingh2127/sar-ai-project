import subprocess

def call_llama(prompt: str) -> str:
    """Helper function to communicate with Ollama."""
    try:
        result = subprocess.run(
            ["ollama", "run", "llama3"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=300,
            encoding='utf-8'
        )
        return result.stdout.strip() if result.returncode == 0 else f"Error: {result.stderr}"
    except Exception as e:
        return f"LLM Connection Failed: {str(e)}"

def generate_sar(prompt: str) -> str:
    """Agent 1: The Writer - Generates the formal SAR narrative."""
    return call_llama(prompt)

def run_adversarial_audit(narrative: str, txn_data: dict) -> str:
    """Agent 2: The Auditor - Cross-references the narrative with raw data."""
    audit_prompt = f"""
    SYSTEM: You are a Senior AML Auditor at Barclays. 
    TASK: Verify if the following SAR narrative accurately reflects the transaction data.
    DATA: {txn_data}
    NARRATIVE: {narrative}
    
    Check for:
    1. Correct Transaction ID and Amount.
    2. Any 'hallucinations' (facts not in the data).
    
    If accurate, start with 'VERIFIED:'. If there is an error, start with 'DISCREPANCY:'. 
    Keep it to 2 sentences.
    """
    return call_llama(audit_prompt)