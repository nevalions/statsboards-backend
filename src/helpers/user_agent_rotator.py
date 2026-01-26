"""User-Agent rotator for parsing requests to avoid detection."""

import random


class UserAgentRotator:
    """Rotates User-Agent strings to mimic different browsers."""

    USER_AGENTS = [
        # Chrome
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        # Firefox
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
        # Safari
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        # Edge
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    ]

    def __init__(self, user_agents: list[str] | None = None):
        """
        Initialize User-Agent rotator.

        Args:
            user_agents: Custom list of user agent strings. Defaults to built-in list.
        """
        self.user_agents = user_agents or self.USER_AGENTS

    def get_random(self) -> str:
        """
        Get a random User-Agent string.

        Returns:
            Random user agent string.
        """
        return random.choice(self.user_agents)

    def get(self, index: int) -> str:
        """
        Get User-Agent string by index.

        Args:
            index: Index of user agent.

        Returns:
            User agent string at specified index.
        """
        return self.user_agents[index % len(self.user_agents)]


_user_agent_rotator = UserAgentRotator()


def get_random_user_agent() -> str:
    """
    Get a random User-Agent string from the global rotator.

    Returns:
        Random user agent string.
    """
    return _user_agent_rotator.get_random()
