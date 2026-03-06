import os
import argparse
import requests
import subprocess
import re
from typing import Tuple, Optional

class AutonomousAgent:
    """
    An autonomous agent powered by a local Ollama instance (gemma:2b).
    It receives a goal, decides on bash commands to run, executes them with 
    human-in-the-loop permission, and feeds the stdout back to the LLM for further analysis.
    """
    def __init__(self, target: str, ollama_host: str = "http://localhost:11434"):
        self.target = target
        self.ollama_host = ollama_host
        self.model = "gemma:2b"
        self.history = []
        
        # We enforce a strict system prompt to train small models how to format command requests
        self.system_prompt = f"""
        You are an autonomous bug bounty agent testing the target: {self.target}.
        Your goal is to discover subdomains, find live hosts, and identify vulnerabilities.
        You have full access to a Kali Linux terminal.
        
        RULES:
        1. If you want to execute a bash command, you MUST format it exactly like this (and provide NO other text):
           ```bash
           your_command_here
           ```
        2. Commands you can use: subfinder, httpx, naabu, nuclei, curl, nmap, grep, cat, ls.
        3. Do NOT run destructive commands (rm, overwrite, etc).
        4. If you have enough information and are finished, output:
           ```report
           [Your final markdown summary of vulnerabilities found]
           ```
        5. Think step-by-step. First find subdomains, then find live ones, then scan ports, then run nuclei.
        """
        
        self.history.append({"role": "system", "content": self.system_prompt})
        
    def check_ollama(self) -> bool:
        """Verifies Ollama is running"""
        try:
            response = requests.get(self.ollama_host)
            return response.status_code == 200
        except requests.exceptions.ConnectionError:
            return False

    def ask_llm(self, prompt: str) -> str:
        """Sends the conversation history to Ollama and returns the response."""
        self.history.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": self.history,
            "stream": False,
            "options": {"temperature": 0.1} # Keep it very deterministic
        }
        
        response = requests.post(f"{self.ollama_host}/api/chat", json=payload)
        response.raise_for_status()
        
        ai_msg = response.json().get('message', {}).get('content', '')
        self.history.append({"role": "assistant", "content": ai_msg})
        return ai_msg

    def extract_action(self, llm_response: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parses the LLM response looking for ```bash ... ``` or ```report ... ``` blocks.
        Returns a tuple: (action_type, payload)
        """
        bash_match = re.search(r'```bash\n(.*?)```', llm_response, re.DOTALL)
        if bash_match:
            return "bash", bash_match.group(1).strip()
            
        report_match = re.search(r'```report\n(.*?)```', llm_response, re.DOTALL)
        if report_match:
            return "report", report_match.group(1).strip()
            
        return None, None

    def execute_command(self, command: str) -> str:
        """Executes a bash command and returns stdout/stderr combined."""
        try:
            # We use timeout to prevent indefinite hanging (e.g. nmap without specific flags)
            result = subprocess.run(
                command, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True, 
                timeout=300 # 5 minute max execution
            )
            return result.stdout
        except subprocess.TimeoutExpired:
            return "Execution timed out after 5 minutes."
        except Exception as e:
            return f"Error executing command: {str(e)}"

    def run(self):
        print(f"[*] Initializing Autonomous Agent for target: {self.target}")
        if not self.check_ollama():
            print("[-] Error: Ollama is not running on localhost:11434.")
            return

        # Kickoff prompt
        next_prompt = "Let's begin. What is your first command?"
        
        # Max of 10 loops to prevent infinite hallucination loops
        max_loops = 10 
        
        for loop in range(max_loops):
            print(f"\n[Turn {loop+1}/{max_loops}] Agent is thinking...")
            try:
                llm_response = self.ask_llm(next_prompt)
            except Exception as e:
                print(f"[-] LLM API Error: {e}")
                break
                
            action_type, payload = self.extract_action(llm_response)
            
            if action_type == "report":
                print("\n================ FINAL REPORT ================\n")
                print(payload)
                print("\n=============================================\n")
                break
                
            elif action_type == "bash":
                print(f"\n[⚠️] THE AI WANTS TO EXECUTE A COMMAND:")
                print(f"     > {payload}")
                
                # HUMAN IN THE LOOP SAFEGUARD
                # Ensures mitigation against OWASP LLM08 (Excessive Agency)
                user_approval = input("Approve execution? [y/N]: ").strip().lower()
                
                if user_approval == 'y':
                    print("[*] Executing...")
                    output = self.execute_command(payload)
                    
                    # Prevent massive output from blowing up context window
                    if len(output) > 3000:
                        output = output[:3000] + "\n...[TRUNCATED_DUE_TO_SIZE]..."
                        
                    print(f"[*] Command finished. Output length: {len(output)} chars.")
                    
                    next_prompt = f"Command executed perfectly. Here is the exact output:\n```\n{output}\n```\nWhat is your next command?"
                else:
                    print("[-] Command rejected by user.")
                    next_prompt = "I (the user) rejected that command. Do not try to run it again. Please provide an alternative next step."
                    
            else:
                print("\n[!] The AI did not format its output correctly. Sending a correction.")
                # Small models often forget formatting. We gently correct them in the loop.
                next_prompt = "You did not use the ```bash or ```report markdown blocks. Remember the rules. What is your next command?"

        print("\n[*] Agent loop terminated.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Experimental Autonomous Bug Bounty Agent")
    parser.add_argument("-t", "--target", required=True, help="Domain to target (e.g. yahoo.com)")
    args = parser.parse_args()
    
    agent = AutonomousAgent(target=args.target)
    agent.run()
