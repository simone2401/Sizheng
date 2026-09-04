from app.shared.errors import SafetyError

class InputGuard:
    blocked_terms = ("忽略之前的指令", "绕过安全", "提示词注入", "system prompt")
    def check(self, text: str) -> None:
        if any(term.lower() in text.lower() for term in self.blocked_terms): raise SafetyError("input safety check blocked this request")

class OutputGuard:
    blocked_terms = ("[SAFETY_BLOCK]",)
    def check(self, text: str) -> None:
        if any(term.lower() in text.lower() for term in self.blocked_terms): raise SafetyError("output safety check blocked model output")
