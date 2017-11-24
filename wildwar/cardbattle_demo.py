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
        database_dir=os.path.join(DATA_ROOT_DIR, 'database'),
        n_tefuda_init=4,
        max_tefuda=8,
        board_size=(5, 7,),
        timeout=10,
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
        from communicater import QueueCommunicator

        PLAYER1_ID = 'DemoPlayer1'
        PLAYER2_ID = 'DemoPlayer2'
        s_to_p1, p1_to_s = \
            QueueCommunicator.create_pair_of_communicators(player_id=PLAYER1_ID)
        s_to_p2, p2_to_s = \
            QueueCommunicator.create_pair_of_communicators(player_id=PLAYER2_ID)
        self.root = root = Factory.BoxLayout(spacing=30)

        def on_touch_down(touch):
            # touch.push()
            # touch.apply_transform_2d(root.to_local)
            for child in root.children:
                if child.collide_point(*touch.pos):
                    if child.on_touch_down(touch):
                        return True
            # touch.pop()
        root.on_touch_down = on_touch_down

        root.add_widget(CardBattleMain(communicator=p1_to_s, iso639='ja'))
        root.add_widget(CardBattleMain(communicator=p2_to_s, iso639='ja'))
        self.server_communicators = (s_to_p1, s_to_p2, )
        return root

    def on_start(self):
        for child in self.root.children:
            child.on_start()
        run_server_thread(communicators=self.server_communicators)


def _test():
    for parent, __1, __2 in os.walk(DATA_ROOT_DIR):
        resource_add_path(parent)
    set_default_font_to_japanese.apply()
    DemoApp().run()


if __name__ == r'__main__':
    _test()
