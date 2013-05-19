import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("scratchtobat")


def isList(obj):
    return isinstance(obj, list)


class ScratchtobatError(Exception):
    pass
