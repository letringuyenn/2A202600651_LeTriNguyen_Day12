"""
Mock LLM used by the production-ready lab.

This keeps the project fully offline and avoids requiring a real API key
while still behaving like an external model call.
"""
import random
import time


MOCK_RESPONSES = {
    "default": [
        "This is a mock response from the production agent. In a real deployment, this would come from an LLM API.",
        "The agent is running correctly and received your question.",
        "Deployment concepts are working as expected in this lab environment.",
    ],
    "docker": [
        "Docker packages your app and dependencies so it can run the same way everywhere."
    ],
    "deploy": [
        "Deployment moves your app from local development to a cloud environment."
    ],
    "health": [
        "The service is healthy and ready to receive requests."
    ],
}


def ask(question: str, delay: float = 0.05) -> str:
    """Return a short mock answer with a small artificial delay."""
    time.sleep(delay + random.uniform(0, 0.03))

    lowered = question.lower()
    for keyword, responses in MOCK_RESPONSES.items():
        if keyword in lowered:
            return random.choice(responses)

    return random.choice(MOCK_RESPONSES["default"])


def ask_stream(question: str):
    """Yield a mock streamed response token by token."""
    response = ask(question)
    for word in response.split():
        time.sleep(0.02)
        yield word + " "

