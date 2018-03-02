# -*- coding: utf-8 -*-

r'''__slots__によって作れる属性が制限された辞書


使い方:

from collections.abc import MutableMapping
from slotsdict import SlotsDict

class Book(SlotsDict):
    __slots__ = ('title', 'price', 'isbn', )  # 許可する属性名

book = Book(title='Dive Into Python', price=100)

isinstance(book, MutableMapping)  # => True
isinstance(book, dict)            # => False

book['title']            # 属性へアクセス
book.title               # ドットでも可

book.isbn         # 存在しないので AttributeError
book['isbn']      # 辞書としてアクセスした為 KeyError
book.weight       # 存在しないので AttributeError
book['weight']    # 辞書としてアクセスした為 KeyError
del book.weight       # 存在しないので AttributeError
del book['weight']    # 辞書としてアクセスした為 KeyError

book.weight = 10     # __slots__に無いので AttributeError
book['weight'] = 10  # 注意! 辞書としてアクセスしているが AttributeError



問題点:

上のBookの派生クラスを作る時には

class SubBook(Book):
    __slots__ = Book.__slots__ + ('new_attr1', 'new_attr2', )

のようにBookの__slots__を加えてやる必要があり不便。metaprogrammingを学んだら改善す
る。
'''

try:
    from .slotsdict import SlotsDict
except ImportError:
    from slotsdict import SlotsDict
