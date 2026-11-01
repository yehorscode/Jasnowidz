from utils.logmanager import error, info, success, warn


def test_logging():
    info("This is how info looks like")
    success("This is how success looks like")
    error("This is how error looks like")
    warn("This is how warn looks like")
