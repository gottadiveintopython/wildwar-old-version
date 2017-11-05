# -*- coding: utf-8 -*-

try:
    from .notificater import Notificater
except ImportError:
    from notificater import Notificater
