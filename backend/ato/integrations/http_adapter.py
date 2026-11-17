
import requests


class HttpAgentAdapter:
    """Generic HTTP adapter for external agents."""

    def __init__(self, base_url: str, timeout: int = 15):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    def post(self, endpoint: str, payload: dict):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            response = self.session.post(
                url,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()

        except requests.Timeout as exc:
            raise RuntimeError(
                f"Agent API timed out: {url}"
            ) from exc

        except requests.ConnectionError as exc:
            raise RuntimeError(
                f"Cannot connect to Agent API: {url}"
            ) from exc

        except requests.HTTPError as exc:
            detail = exc.response.text[:1000] if exc.response is not None else str(exc)
            raise RuntimeError(
                f"Agent API returned an HTTP error: {detail}"
            ) from exc

        try:
            return response.json()

        except ValueError:
            raise RuntimeError(
                f"Agent API returned invalid JSON: {url}"
            )
