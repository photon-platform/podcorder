"""
run the main app
"""
from .podcorder import Podcorder


def run() -> None:
    reply = Podcorder().run()
    print(reply)
