
import os

from .http_adapter import HttpAgentAdapter


REMINDER_AGENT_URL = os.getenv(
    "REMINDER_AGENT_URL",
    "http://127.0.0.1:8001",
)


ADAPTERS = {
    "reminder_agent": HttpAgentAdapter(
        base_url=REMINDER_AGENT_URL,
        timeout=15,
    ),
}


def get_adapter(agent_name: str):
    adapter = ADAPTERS.get(agent_name)

    if adapter is None:
        raise ValueError(
            f"No integration adapter registered for agent: {agent_name}"
        )

    return adapter
