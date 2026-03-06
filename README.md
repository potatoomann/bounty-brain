# BountyBrain

BountyBrain is a secure AI-powered cybersecurity assistant designed to analyze vulnerability scanner outputs and assist with triage, natively mitigating risks from the OWASP Top 10 for Large Language Models.

## Features & Security

- **OWASP LLM01 Mitigated (Prompt Injection):** Employs strict system prompts and clear data delimiters so the AI treats incoming scanner data strictly as untrusted text, not executable instructions.
- **OWASP LLM06 Mitigated (Data Leakage):** Features a pre-processing `Redactor` engine that locally scrubs your generic API keys, AWS keys, internal IP addresses, and emails *before* the data ever leaves your machine or reaches the LLM API.
- **OWASP LLM04 Mitigated (Model DoS):** Enforces strict maximum token limits on generation to prevent runaway execution costs or resource exhaustion.
- **OWASP LLM08 Mitigated (Excessive Agency):** Operates strictly as an advisory CLI tool. It will analyze and suggest but has zero permissions to execute shell commands, scripts, or interact with external services on your behalf.
- **OWASP LLM02/LLM09 Mitigated (Insecure Output Handling / Overreliance):** All AI-generated outputs are clearly marked as AI-generated with a prominent disclaimer urging manual verification to prevent overreliance.

## Setup

1.  **Clone / Download** this directory.
2.  **Install requirements:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Configure API Key:**
    Copy `.env.example` to `.env` and add your OpenAI API Key.
    ```bash
    cp .env.example .env
    # Edit the .env file with your key
    ```

## Usage

**Analyze a scanner output file:**
```bash
python bounty_brain.py -f nuclei_output.txt
```

**Ask a direct question:**
```bash
python bounty_brain.py -q "How do I chain a reflected XSS with this specific CSRF token weakness?"
```

## Adding Custom Redactions

If your organization has specific sensitive data formats (e.g., custom internal URLs or proprietary tokens), you can easily add new regex patterns to the `self.patterns` dictionary in the `Redactor` class inside `bounty_brain.py`.

---

## 🔥 Optional: Autonomous Agent (bounty_agent.py)

We have also included an **Autonomous Agent** version of this tool that runs locally via Ollama. 

**WARNING:** This tool circumvents OWASP LLM08 (Excessive Agency) by attempting to execute `bash` commands autonomously on your Kali machine based on AI logic. 

**Safeguard:** It features a mandatory Human-in-the-Loop review. *Always* read the command it suggests before pressing `y`.

**Usage:**
```bash
python3 bounty_agent.py --target yahoo.com
```
If it hallucinates or suggests dangerous commands, type `n` and it will attempt to rethink its approach.
