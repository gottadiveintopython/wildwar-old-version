# -*- coding: utf-8 -*-

__all__ = (r'get_logger',)

from logging import (getLogger, StreamHandler, DEBUG,)


def get_logger(name):
    logger = getLogger(name)
    stream_handler = StreamHandler()
    stream_handler.setLevel(DEBUG)
    logger.setLevel(DEBUG)
    logger.addHandler(stream_handler)
    return logger
