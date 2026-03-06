from bounty_brain import Redactor

def test_redaction():
    redactor = Redactor()
    
    test_text = "Here is an IP 192.168.1.1 and a token ghp_1234567890abcdefghijklmnopqrstuvwxyzABCD and my email test@example.com."
    
    redacted = redactor.redact(test_text)
    
    print("Original:", test_text)
    print("Redacted:", redacted)
    
    # Assertions
    assert "192.168.1.1" not in redacted
    assert "ghp_1234567890abcdefghijklmnopqrstuvwxyzABCD" not in redacted
    assert "test@example.com" not in redacted
    
    assert "[REDACTED IPv4 Address]" in redacted
    assert "[REDACTED Generic API Key]" in redacted
    assert "[REDACTED Email Address]" in redacted
    
    print("[+] All redaction tests passed safely!")

if __name__ == "__main__":
    test_redaction()
