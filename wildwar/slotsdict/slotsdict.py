# -*- coding: utf-8 -*-

from collections.abc import MutableMapping
from abc import ABCMeta

import json


class SlotsDict(MutableMapping):
    __slots__ = ()

    @property
    def __class__(self):
        return dict

    def __init__(self, *args, **kwargs):
        self.update(*args, **kwargs)
        for key, value in self.__slotsdict__.items():
            self.setdefault(key, value)

    def __getitem__(self, key):
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError("KeyError: '{}'".format(key))

    def __setitem__(self, key, value):
        try:
            return setattr(self, key, value)
        except AttributeError:
            raise KeyError("KeyError: '{}'".format(key))

    def __delitem__(self, key):
        raise Exception("__delitem__() is not allowed.")

    def __delattr__(self, key):
        raise Exception("__delattr__() is not allowed.")

    def __len__(self):
        return len(self.__slots__)

    def __iter__(self):
        return iter(self.__slots__)

    def items(self):
        for key in self.__slots__:
            try:
                yield (key, getattr(self, key), )
            except AttributeError:
                pass

    def keys(self):
        return self.__slots__

    def values(self):
        return (getattr(self, key) for key in self.__slots__)

    def __str__(self):
        return json.dumps(self, indent=2)


class SlotsDictMeta(ABCMeta):

    def __new__(cls, name, bases, attributes):
        if len(bases) != 0:
            raise Exception('SuperClassは指定できません。強制的にSlotsDictになります。')
        attributes['__slots__'] = tuple(attributes['__slotsdict__'].keys())
        return super().__new__(cls, name, (SlotsDict, ), attributes)
