# -*- coding: utf-8 -*-

import json
import unittest

from slotsdict import SlotsDict


class Person(SlotsDict):
    __slotsdict__ = dict(
        name='<default_name>',
        age=0,
        sex='female',
    )


class Team(SlotsDict):
    __slotsdict__ = dict(
        name='<default_team_name>',
        members=[],
    )


class SlotsDictTest(unittest.TestCase):

    def test_exception(self):
        obj = Person(name='Bob', age=20)

        # ----------------------------------------------------------------------
        # 読み込み
        # ----------------------------------------------------------------------

        # __slotsdict__に無い属性
        with self.assertRaises(AttributeError):
            print(obj.unknown_attr)
        with self.assertRaises(KeyError):
            print(obj['unknown_attr'])
        # __slotsdict__にある属性
        temp = obj.sex
        temp = obj['sex']

        # ----------------------------------------------------------------------
        # 書き込み
        # ----------------------------------------------------------------------

        # __slotsdict__に無い属性
        with self.assertRaises(AttributeError):
            obj.unknown_attr = 1
        with self.assertRaises(KeyError):
            obj['unknown_attr'] = 1
        with self.assertRaises(KeyError):
            obj.update(unknown_attr=1)

        # __slotsdict__にある属性
        obj.sex = 'male'
        obj['sex'] = 'male'

        # ----------------------------------------------------------------------
        # 削除
        # ----------------------------------------------------------------------

        # __slotsdict__に無い属性
        with self.assertRaises(Exception):
            del obj.unknown_attr
        with self.assertRaises(Exception):
            del obj['unknown_attr']
        # __slotsdict__にある属性
        with self.assertRaises(Exception):
            del obj.sex
        with self.assertRaises(Exception):
            del obj['sex']

        # ----------------------------------------------------------------------
        # 菱型継承
        # ----------------------------------------------------------------------
        class Villager(Person): pass
        class Student(Person): pass
        with self.assertRaises(TypeError):
            class Both(Villager, Student): pass

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
        with self.assertRaises(Exception):
            obj.__delitem__('name')
        with self.assertRaises(Exception):
            obj.__delattr('name')
        obj.__len__()
        obj.__iter__()
        obj.items()
        obj.keys()
        obj.values()
        obj.__str__()

    def test_jsonize(self):
        rei = Person(name='Rei', age=20)
        ken = Person(name=None, age=21.0, sex='male')
        team1 = Team(members=[rei, ken, ], name='Red')
        s = json.dumps(team1, indent=2)
        print(s)
        d = json.loads(s)
        print(d)
        print(str(team1))


if __name__ == '__main__':
    unittest.main()
