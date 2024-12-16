def str2bool(value: set):
    """Convert a string to a boolean."""
    return str(value).lower() in ["true", "1", "t", "yes", "y"]
