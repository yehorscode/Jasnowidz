from openrouter import OpenRouter
import requests


def check_ratelimit(router: OpenRouter) -> int:
    """Makes a request to the ai provider and tries to return how many seconds left until reset"""
    ...
