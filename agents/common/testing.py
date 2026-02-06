import subprocess
import os

def run_tests(project_dir: str) -> tuple[bool, str]:
    """
    Runs pytest in the target project directory.
    
    Args:
        project_dir (str): Path to the project root.

    Returns:
        tuple[bool, str]: (Success, Error Log)
    """
    print("   🧪 Running tests...")
    
    # Detect Python Executable
    python_cmd = "python3"
    possible_venvs = ["venv", ".venv", "env"]
    
    for venv in possible_venvs:
        venv_python = os.path.join(project_dir, venv, "bin", "python")
        if os.path.exists(venv_python):
            python_cmd = venv_python
            print(f"   🐍 Using venv: {python_cmd}")
            break

    try:
        # Using python3 -m pytest ensures we use the python interpreter from the environment
        result = subprocess.run(
            [python_cmd, "-m", "pytest"], 
            cwd=project_dir, 
            capture_output=True, 
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print("   ✅ Tests PASSED")
            return True, ""
        else:
            print(f"   ❌ Tests FAILED")
            # Capture last 20 lines of std out and err for context
            stdout_tail = result.stdout.splitlines()[-20:]
            stderr_tail = result.stderr.splitlines()[-20:]
            error_log = "\n".join(stdout_tail + stderr_tail)
            return False, error_log
            
    except subprocess.TimeoutExpired:
        return False, "Tests timed out after 60s."
    except Exception as e:
        return False, str(e)
