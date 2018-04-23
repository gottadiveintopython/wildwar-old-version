# -*- coding: utf-8 -*-

r'''__slots__によって作れる属性が制限された辞書



使い方:

from slotsdict import SlotsDict

class Book(SlotsDict):
    # 許可する辞書のKeyとその既定値
    __slotsdict__ = {
        'title': 'default title',
        'price': 0,
        'isbn': 'default isbn',
    }

book = Book(title='Dive Into Python', price=100)

isinstance(book, dict)   # => True

book['title']            # 属性へアクセス
book.title               # ドットでも可

book.weight        # 存在しないので AttributeError
book['weight']     # 辞書としてアクセスした為 KeyError
del book.title     # 削除はできずExceptionが投げられる
del book['title']  # 削除はできずExceptionが投げられる

book.weight = 10     # __slotsdict__に無いので AttributeError
book['weight'] = 10  # 辞書としてアクセスした為 KeyError
'''

from .slotsdict import SlotsDict
