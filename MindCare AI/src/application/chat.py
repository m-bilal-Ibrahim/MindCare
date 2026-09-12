"""Chat assistant use case."""


class ChatAssistant:
    """Apply the assistant's safety response policy independently of HTTP."""

    def respond(self, message: str) -> str:
        """Return a bounded response for clinician-facing assistant requests."""
        return "Please consult a qualified mental-health professional."