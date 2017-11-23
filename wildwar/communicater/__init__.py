# -*- coding: utf-8 -*-

r'''ClientとServer間の通信を行うCommunicatorを提供するModule

Communicatorは以下の要件を満たしていなければならない

# 1.通信をしているClientのPlayerのidが取得できる
communicator.player_id

# 2.時間制限を設けて受信ができる。
try:
    command = communicator.recieve(20)  # in seconds
except TimeoutError:
    pass

# 3.非Blockingの受信ができる。
command = communicator.recieve_nowait()
if command is None:
    commandが受信できなかった時の処理

# 4.送信ができる
communicator.send(command)
'''

from .queuecommunicator import QueueCommunicator
