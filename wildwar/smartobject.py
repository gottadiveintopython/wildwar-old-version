# -*- coding: utf-8 -*-

r'''意図しない属性の書き換えを防ぐ機能 と 冗長な記述を防ぐ機能を持つオブジェクト
(python2/python3両対応)

現状、Pythonのオブジェクトにはいかの問題があると思う。

1. 既存の属性に書き込んだつもりが、新しく別の属性を作ってしまう。
obj.time = 100
obj.tine = 90  # miss typing

2. 何度も同じオブジェクトの属性に値を入れる時、記述が冗長。
obj.attr1 = 1
obj.attr2 = 2  # annoying
obj.attr3 = 3  # annoying

このモジュールのSmartObjectでは以下の様に問題が解消されている
obj = SmartObject(attr1=1, attr2=1)  # 作る時は自由に属性を決めれる
obj.attr1 = 1                        # OK
obj.attr3 = 1                        # AttributeError! "attr3" doesn't exist
obj.so_overwrite(attr1=2, attr2=2)   # OK
obj.so_overwrite(attr1=3, attr3=3)   # AttributeError! "attr3" doesn't exist
obj.so_update(attr1=4, attr3=4)      # OK "so_update" is able to create new attributes.

又、以下の様にobjを読み取り専用にする事も可能
ro = obj.so_as_readonly()  #  make it read only
print(ro.attr1)            #  OK
ro.attr1 = 0               #  AttributeError! It's read only
ro.so_overwrite(attr1=0)   #  AttributeError! It's read only
ro.so_update(attr1=0)      #  AttributeError! It's read only
temp = ro.so_as_writable() #  make it back writable
temp.attr1 = 0             #  OK
'''

import json

__all__ = (r'SmartObject', )


class ReadOnly(object):
    r'''internal use'''

    def __init__(self, obj):
        self.__dict__[r'__obj'] = obj

    def so_raise_error(self):
        r'internal use'
        raise AttributeError(
            r"You can't set attributes through 'ReadOnly' object"
        )

    def __getattr__(self, key):
        return getattr(self.__dict__[r'__obj'], key)

    def __setattr__(self, key, value):
        self.so_raise_error()

    def __str__(self):
        return self.__dict__[r'__obj'].__str__()

    def so_to_json(self, **json_dumps_kwargs):
        return self.__dict__[r'__obj'].so_to_json(**json_dumps_kwargs)

    def so_overwrite(self, **kwargs):
        self.so_raise_error()

    def so_update(self, **kwargs):
        self.so_raise_error()

    def so_as_readonly(self):
        return self

    def so_as_writable(self):
        return self.__dict__[r'__obj']

    def so_to_dict(self):
        return self.__dict__[r'__obj'].so_to_dict()

    def so_copy(self):
        return self.__dict__[r'__obj'].so_copy()


def _is_smartobject(obj):
    r'''internal use'''
    return isinstance(obj, (ReadOnly, SmartObject, ))


def _convert_lists_items_to_dict_recursively(list_obj):
    r'''internal use'''
    return [
        item.so_to_dict() if _is_smartobject(item) else (
            _convert_lists_items_to_dict_recursively(item)
            if isinstance(item, (list, )) else item
        )
        for item in list_obj
    ]


def _convert_lists_items_to_smartobject_recursively(list_obj):
    r'''internal use'''
    return [
        SmartObject(**item) if isinstance(item, (dict, )) else (
            _convert_lists_items_to_smartobject_recursively(item)
            if isinstance(item, (list, )) else item
        )
        for item in list_obj
    ]


class SmartObject(object):

    @staticmethod
    def load_from_json(json_string, **json_loads_kwargs):
        json_loads_kwargs.setdefault(r'parse_int', int)
        json_loads_kwargs.setdefault(r'parse_constant', bool)
        return SmartObject(**json.loads(json_string, **json_loads_kwargs))

    def __init__(self, **kwargs):
        self.so_update(**kwargs)

    def __getattr__(self, key):
        raise AttributeError(
            r"'{}' has no attribute named '{}'.".format(repr(self), key)
        )

    def __setattr__(self, key, value):
        r'''overwrite a attribute that already exist'''
        if key in self.__dict__:
            self.__dict__[key] = value
        else:
            raise AttributeError(
                r"'{}' has no attribute named '{}'.".format(repr(self), key)
            )

    def __str__(self):
        return json.dumps(self.so_to_dict(), indent=2)

    def so_to_json(self, **json_dumps_kwargs):
        return json.dumps(self.so_to_dict(), **json_dumps_kwargs)

    def so_overwrite(self, **kwargs):
        r'''overwrite attributes that already exist'''
        self_keys = set(self.__dict__.keys())
        kwarg_keys = set(kwargs.keys())
        if self_keys.issuperset(kwarg_keys):
            self.so_update(**kwargs)
        else:
            raise AttributeError(
                r"'{}' doesn't have those attributes: '{}'.".format(
                    repr(self), kwarg_keys - self_keys))

    def so_update(self, **kwargs):
        r'''similar to dict.update() but only accepts keyword arguments'''
        self.__dict__.update({
            key:
            SmartObject(**value) if isinstance(value, (dict, )) else (
                _convert_lists_items_to_smartobject_recursively(value)
                if isinstance(value, (list, )) else value
            )
            for key, value in kwargs.items()
        })

    def so_as_readonly(self):
        r'''returns read-only interface'''
        return ReadOnly(self)

    def so_as_writable(self):
        r'''returns writable interface'''
        return self

    def so_to_dict(self):
        r'''SmartObjectを辞書に変換する。もし自身の属性にSmartObjectかlistがあれば、
        その要素を再帰的に辞書に変換する'''
        return {
            key:
            value.so_to_dict() if _is_smartobject(value) else (
                _convert_lists_items_to_dict_recursively(value)
                if isinstance(value, (list, )) else value
            )
            for key, value in self.__dict__.items()
        }

    def so_copy(self):
        r'''shallow copy'''
        return SmartObject(**self.__dict__)


import unittest


class SmartObjectTest(unittest.TestCase):

    def test_exception(self):
        obj = SmartObject(attr1=r'A', attr2=r'B')

        # 存在しない属性を読み込むことは勿論出来ない
        with self.assertRaises(AttributeError):
            print(obj.unknown_attr)

        # 存在しない属性への書き込みはso_update()以外では出来ない
        with self.assertRaises(AttributeError):
            obj.unknown_attr = 1
        with self.assertRaises(AttributeError):
            obj.overwrite(unknown_attr=1)

        # 読み取り専用のInterfaceを取得
        ro = obj.so_as_readonly()

        # 存在しない属性を読み込むことは勿論出来ない
        with self.assertRaises(AttributeError):
            print(ro.unknown_attr)

        # 読み取り専用なので全ての書き込み操作が行えない
        with self.assertRaises(AttributeError):
            ro.attr1 = r'AA'
        with self.assertRaises(AttributeError):
            ro.overwrite(attr1=r'AA')
        with self.assertRaises(AttributeError):
            ro.update(attr1=r'AA')
        with self.assertRaises(AttributeError):
            ro.unknown_attr = 1
        with self.assertRaises(AttributeError):
            ro.overwrite(unknown_attr=1)
        with self.assertRaises(AttributeError):
            ro.update(unknown_attr=1)

    def test_exception_msg(self):
        print(r'---- Check Error Message ----')
        obj = SmartObject(attr1=r'A')
        try:
            print(obj.unknown_attr)
        except AttributeError as e:
            print(e)
        try:
            obj.so_overwrite(attr1=r'AA', attr2=r'BB', attr3=r'CC')
        except AttributeError as e:
            print(e)

        ro = obj.so_as_readonly()
        try:
            ro.attr1 = r'B'
        except AttributeError as e:
            print(e)
            print(r'---- Check Error Message (END)----')

    def test_syntax(self):
        obj = SmartObject(attr=r'A')
        obj.attr = r'B'
        obj.so_overwrite()
        obj.so_update()
        obj.so_as_readonly()
        obj.so_as_writable()
        obj.so_copy()
        obj.so_to_dict()
        obj.so_to_json()
        print(obj)
        ro = obj.so_as_writable()
        ro.so_as_readonly()
        ro.so_as_writable()
        ro.so_copy()
        ro.so_to_dict()
        ro.so_to_json()
        print(ro)

    def test_nested(self):
        obj = SmartObject(
            msg=r'Love Python',
            data={
                r'msg': r'World',
                r'child': SmartObject(
                    msg=r'Hello',
                    child={
                        r'msg': r'Python'
                    }
                ),
            },
        )
        print(obj)
        print(SmartObject.load_from_json(obj.so_to_json()))


if __name__ == '__main__':
    unittest.main()
