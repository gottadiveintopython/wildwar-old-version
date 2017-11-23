# -*- coding: utf-8 -*-

__all__ = ('QueueCommunicator', )

import queue


class QueueCommunicator:

    @staticmethod
    def create_pair_of_communicators(*, player_id):
        queue1 = queue.Queue()
        queue2 = queue.Queue()
        communicator1 = QueueCommunicator(
            player_id=player_id,
            send_queue=queue1,
            recieve_queue=queue2)
        communicator2 = QueueCommunicator(
            player_id=player_id,
            send_queue=queue2,
            recieve_queue=queue1)
        return (communicator1, communicator2, )

    def __init__(self, *, player_id, recieve_queue, send_queue):
        self.player_id = player_id
        self.send_queue = send_queue
        self.recieve_queue = recieve_queue

    def recieve(self, timeout):
        try:
            return self.recieve_queue.get(timeout=timeout)
        except queue.Empty:
            raise TimeoutError(
                'Failed to get item from queue within {} seconds.'.format(
                    timeout))

    def recieve_nowait(self):
        try:
            return self.recieve_queue.get_nowait()
        except queue.Empty:
            return None

    def send(self, item):
        self.send_queue.put(item=item)


def _test():
    server_communicator, client_communicator = \
        QueueCommunicator.create_pair_of_communicators(player_id='Player1')

    print(client_communicator.player_id)
    print(server_communicator.player_id)

    client_communicator.send('client command1')
    client_communicator.send('client command2')
    print(server_communicator.recieve(1))
    print(server_communicator.recieve(1))

    server_communicator.send('server command1')
    server_communicator.send('server command2')
    print(client_communicator.recieve(1))
    print(client_communicator.recieve(1))

    print(server_communicator.recieve_nowait())
    try:
        print(server_communicator.recieve(1))
    except TimeoutError:
        print('Timeout!')


if __name__ == '__main__':
    _test()
