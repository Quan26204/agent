
"""Allowlist of agents and capabilities known to the orchestrator."""

AGENTS = {
    "reminder_agent": {
        "capabilities": ["create_reminder"],
        "description": "Creates a reminder for the user at a specified time.",
    },
    "research_agent": {
        "capabilities": ["web_research"],
        "description": "Finds and verifies information from approved research sources.",
    },
    "summarization_agent": {
        "capabilities": ["summarize"],
        "description": "Summarizes supplied research or text.",
    },
    "chatbot_agent": {
        "capabilities": ["summarize_document"],
        "description": "Uses the existing chatbot knowledge base to retrieve and summarize uploaded documents.",
    },
    "email_agent": {
        "capabilities": ["send_email"],
        "description": "Prepares or sends email after the required user approval.",
    },
}
