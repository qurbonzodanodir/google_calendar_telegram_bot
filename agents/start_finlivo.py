import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from agents.finlivo.agent import FinLivoAgent

if __name__ == "__main__":
    agent = FinLivoAgent()
    agent.start()
