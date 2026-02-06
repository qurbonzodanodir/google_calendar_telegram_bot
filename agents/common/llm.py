import os
import shutil
from app.services.ai.client import groq_client
from agents.common import config, testing

def query_groq(prompt: str) -> str:
    """Sends a prompt to Groq and returns the response."""
    try:
        response = groq_client.get_client().chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.1
        )
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"Groq API Error: {e}")

def clean_code_block(text: str) -> str:
    """Extracts code from markdown blocks if present."""
    if text.startswith("```python"): text = text[9:]
    elif text.startswith("```"): text = text[3:]
    if text.endswith("```"): text = text[:-3]
    return text.strip()

def apply_senior_edit(file_path: str, instruction: str, project_context: str, project_root: str, max_retries: int = 3) -> str:
    """
    Applies an AI edit with strict 'Senior Developer' standards.
    Retries up to max_retries if tests fail.
    """
    if not os.path.exists(file_path):
        return f"File not found: {file_path}"
    
    print(f"   📖 Reading {os.path.basename(file_path)}...")
    with open(file_path, 'r') as f:
        original_code = f.read()

    # Backup
    backup_path = file_path + ".bak"
    shutil.copy(file_path, backup_path)

    current_code = original_code
    error_context = ""

    for attempt in range(1, max_retries + 1):
        print(f"   🤖 Attempt {attempt}/{max_retries}...")
        
        # SMART CONTEXT:
        # We try to fit as much as possible. Llama 3 70b on Groq has ~8k-128k context depending on implementation.
        # Let's try 30,000 chars (approx 7-8k tokens) to be safe but impactful.
        SAFE_CONTEXT_LIMIT = 50000 
        
        prompt = f"""
        You are a SENIOR PYTHON ARCHITECT & TEAM LEADER.
        
        GOAL: Implement the requested feature/fix while ensuring:
        1. NO REGRESSIONS: Do not break existing logic.
        2. CLEAN CODE: Strict PEP8, Typing, Docstrings.
        3. SOLID PRINCIPLES: Modular, maintainable code.
        
        PROJECT KNOWLEDGE BASE (Truncated to {SAFE_CONTEXT_LIMIT} chars):
        {project_context[:SAFE_CONTEXT_LIMIT]}...
        
        TASK INSTRUCTION: {instruction}
        
        TARGET FILE: {os.path.basename(file_path)}
        CURRENT CONTENT:
        {current_code}
        
        {f"PREVIOUS ERROR (Files reverted, please FIX this): {error_context}" if error_context else ""}
        
        RESPONSE FORMAT:
        1. First, provide a short <analysis> block:
           - Explain your plan.
           - List potential risks/dependencies (what other files look at this?).
           - Confirm you will maintain backward compatibility or update callers.
        2. Then, provide the FULL VALID PYTHON CODE for the file.
        
        Do not output markdown backticks (```) around the code if possible, or use standard python blocks.
        """

        try:
            raw_response = query_groq(prompt)
            
            # Extract Code from Response (handling the Analysis block)
            # We look for the code block usually.
            new_code = clean_code_block(raw_response)
            
            # If the model included the <analysis> text in the same block, we need to strip it.
            # Simple heuristic: Look for imports or def/class as start of code.
            # Ideally the model puts code in ```python ```.
            
            # Apply Edit
            with open(file_path, 'w') as f:
                f.write(new_code)
            
            # Verify
            success, error_msg = testing.run_tests(project_root)
            
            if success:
                return f"✅ Fixed & Verified {os.path.basename(file_path)} (Attempt {attempt})"
            else:
                print(f"   ⚠️ Test Failure: {error_msg[:200]}...")
                error_context = error_msg
                current_code = new_code 
                
        except Exception as e:
            print(f"   ❌ AI Exception: {e}")
            break
    
    # Failure -> Revert
    print(f"   ❌ All attempts failed. Reverting to backup.")
    shutil.copy(backup_path, file_path)
    return f"❌ Failed after {max_retries} questions attempts. Reverted."
