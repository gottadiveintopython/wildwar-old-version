# -*- coding: utf-8 -*-

import json
import unittest

from slotsdict import SlotsDict


class Person(SlotsDict):
    __slots__ = ('name', 'age', 'sex', )


class Team(SlotsDict):
    __slots__ = ('members', 'name', )


class SlotsDictTest(unittest.TestCase):

    def test_exception(self):
        obj = Person(name='Bob', age=20)

        # __slots__に無い属性への読み書き
        with self.assertRaises(AttributeError):
            print(obj.unknown_attr)
        with self.assertRaises(KeyError):
            print(obj['unknown_attr'])
        with self.assertRaises(AttributeError):
            obj.unknown_attr = 1
        with self.assertRaises(AttributeError):
            obj['unknown_attr'] = 1
        with self.assertRaises(AttributeError):
            obj.update(unknown_attr=1)

        # __slots__に無い属性の削除
        with self.assertRaises(AttributeError):
            del obj.unknown_attr
        with self.assertRaises(KeyError):
            del obj['unknown_attr']

        # __slots__にはあるが初期化されていない属性の読み込み
        with self.assertRaises(AttributeError):
            print(obj.sex)
        with self.assertRaises(KeyError):
            print(obj['sex'])

        # __slots__にはあるが初期化されていない属性の削除
        with self.assertRaises(AttributeError):
            del obj.sex
        with self.assertRaises(KeyError):
            del obj['sex']

        # __slots__にはあるが初期化されていない属性の書き込み
        obj.sex = 'male'
        obj['sex'] = 'male'

        # 初期化済みの属性への読み書き
        print(obj.name)
        print(obj['name'])
        obj.name = 'Ken'
        obj['name'] = 'Marina'
        obj.update(name='Peter')

        # 初期化済みの属性の削除
        del obj.sex
        del obj['name']

    def test_exception_msg(self):
        print('---- Check Error Message (START) ----')
        obj = Person(name='Bob', age=20)
        try:
            print(obj.unknown_attr)
        except AttributeError as e:
            print(e)
        try:
            print(obj['unknown_attr'])
        except KeyError as e:
            print(e)
        print('---- Check Error Message (END) ----')

    def test_syntax(self):
        obj = Person(name='Bob', age=20)
        obj.__getitem__('name')
        obj.__setitem__('name', 'Ken')
        obj.__delitem__('name')
        obj._sd_existing_values()
        obj._sd_existing_keys()
        obj.__len__()
        obj.__iter__()
        obj.items()
        obj.keys()
        obj.values()
        obj.__str__()

    def test_jsonize(self):
        rei = Person(name='Rei', age=20, sex=True)
        ken = Person(name=None, age=21.0, )
        team1 = Team(members=[rei, ken, ], name='Red')
        s = json.dumps(team1, indent=2)
        print(s)
        d = json.loads(s)
        print(d)
        print(str(team1))


def _test():
    class NeoPerson(Person):
        __slots__ = Person.__slots__ + ('blood', 'ibm', )

    obj = NeoPerson(name='neo', blood='B')
    obj.sex = 'male'
    # obj.aaaa = 20
    print(obj)


if __name__ == '__main__':
    _test()
    # unittest.main()
