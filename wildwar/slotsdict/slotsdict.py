# -*- coding: utf-8 -*-

from collections.abc import MutableMapping
import json


class SlotsDict(MutableMapping):
    __slots__ = ()

    @property
    def __class__(self):
        return dict

    def __init__(self, *args, **kwargs):
        self.update(*args, **kwargs)

    def __getitem__(self, key):
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(key)
            # raise KeyError("KeyError: '{}'".format(key))

    def __setitem__(self, key, value):
        return setattr(self, key, value)

    def __delitem__(self, key):
        try:
            delattr(self, key)
        except AttributeError:
            raise KeyError(key)
            # raise KeyError("KeyError: '{}'".format(key))

    def _sd_existing_values(self):
        for key in self.__slots__:
            try:
                yield getattr(self, key)
            except AttributeError:
                pass

    def _sd_existing_keys(self):
        for key in self.__slots__:
            try:
                getattr(self, key)
                yield key
            except AttributeError:
                pass

    def __len__(self):
        return len(tuple(self._sd_existing_values()))

    def __iter__(self):
        return self._sd_existing_keys()

    def items(self):
        for key in self.__slots__:
            try:
                yield (key, getattr(self, key), )
            except AttributeError:
                pass

    def keys(self):
        return self._sd_existing_keys()

    def values(self):
        return self._sd_existing_values()

    def __str__(self):
        return json.dumps(self, indent=2)
