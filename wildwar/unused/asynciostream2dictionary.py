# -*- coding: utf-8 -*-
r'''asyncioのStreamReader及びStreamWriterによる読み書きを、辞書単位で行う為のModule

# StreamWriter型のインスタンスwriter、StreamReader型のインスタンスreaderが既にあっ
# たとして
dictwriter = Writer(writer)
# max_value_sizeは辞書一つあたりの最大サイズ。この値を超えるサイズの辞書が送られて
# 来た時、そのデータは破棄される。既定値は0で無制限。
dictreader = Reader(reader, max_value_size=4096*4)

# データを送る時は
writer.write({r'key': r'Value'})
await writer.drain()
# データを受け取る時は
try:
    dictionary = await reader.read()
except asyncio.IncompleteReadError as e:
    # 読み込むべきデータはもう無い
    if e.partial:
        # データが中途半端な状態で終わった
    else:
        # データを丁度読み込み終えた
except json.JsonDecodeError as e:
    # 読み込んだデータを辞書に変換出来なかった
'''

__all__ = (r'Reader', r'Writer',)

import struct
import json


BLOCK_SIZE = 4096
STRUCT_TLV_HEADER = struct.Struct(r'!4sI')


class Reader:

    def __init__(self, reader, *, max_value_size=0):
        self.reader = reader
        self.max_value_size = max_value_size
        self.userdata = {}

    async def disposeexactly(self, size):
        r'''internal use'''

        reader = self.reader
        quotient = size // BLOCK_SIZE
        remainder = size % BLOCK_SIZE

        for i in range(quotient):
            await reader.readexactly(BLOCK_SIZE)
        if remainder != 0:
            await reader.readexactly(remainder)

    async def read_tlv(self):
        r'''internal use'''

        reader = self.reader
        while True:
            header = await reader.readexactly(STRUCT_TLV_HEADER.size)
            tag, size = STRUCT_TLV_HEADER.unpack(header)
            if self.max_value_size == 0 or size <= self.max_value_size:
                break
            else:
                await self.disposeexactly(size)

        return tag, await reader.readexactly(size),

    async def read(self):
        r'''ストリームからデータを読み込み、それを返す(辞書型)'''
        tag, value = None, None
        while tag != b'json':
            tag, value = await self.read_tlv()
        return json.loads(
            value.decode(r'utf-8'),
            parse_constant=bool,
            parse_int=int
        )


class Writer:

    def __init__(self, writer):
        self.writer = writer
        self.userdata = {}

    def write_tlv(self, tag, data):
        r'''internal use'''

        writer = self.writer
        header = STRUCT_TLV_HEADER.pack(tag, len(data))
        writer.write(header)
        writer.write(data)

    def write(self, dictionary):
        self.write_tlv(b'json', json.dumps(dictionary).encode(r'utf-8'))
