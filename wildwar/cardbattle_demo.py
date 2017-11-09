# -*- coding: utf-8 -*-

import sys
import os.path
import threading

import kivy
kivy.require(r'1.10.0')
from kivy.config import Config
Config.set('graphics', 'width', 600 + 600 + 30)
Config.set('graphics', 'height', 900)
# Config.set('modules', 'inspector', '')
Config.set('modules', 'touchring', 'image=cursor.png')
from kivy.resources import resource_add_path
from kivy.app import App
# from kivy.clock import Clock
# from kivy.lang import Builder
from kivy.factory import Factory

import setup_logging
logger = setup_logging.get_logger(__name__)
import set_default_font_to_japanese
from cardbattle_client import CardBattleMain
import cardbattle_server

DATA_ROOT_DIR = os.path.join(
    os.path.dirname(sys.modules[__name__].__file__), 'data')


def run_server_thread(**kwargs):

    server = cardbattle_server.Server(
        data_dir=DATA_ROOT_DIR,
        n_tefuda_init=4,
        max_tefuda=8,
        board_size=(5, 5,),
        timeout=8,
        how_to_decide_player_order="random",
        func_create_deck=cardbattle_server.RandomDeckCreater(n_cards=10),
        **kwargs)
    thread = threading.Thread(
        target=server.run,
        name='server_thread',
        daemon=True,
    )
    thread.start()


class DemoApp(App):

    def build(self):
        self.root = root = Factory.BoxLayout(spacing=30)
        root.add_widget(CardBattleMain(player_id='DemoPlayer1'))
        root.add_widget(CardBattleMain(player_id='DemoPlayer2'))
        return root

    def on_start(self):
        children = self.root.children
        senders = (child.get_sender() for child in children)
        recievers = (child.get_reciever() for child in children)
        children[0].on_start()
        children[1].on_start()
        run_server_thread(senders=senders, recievers=recievers)


def _test():
    for parent, __1, __2 in os.walk(DATA_ROOT_DIR):
        resource_add_path(parent)
    set_default_font_to_japanese.apply()
    DemoApp().run()


if __name__ == r'__main__':
    _test()
