import logging

try:
    from .orjson import serialize

    logging.debug("Using fast serialization (orjson)")
except:
    from .json import serialize

    logging.debug("Using slow serialization (built-in json)")
