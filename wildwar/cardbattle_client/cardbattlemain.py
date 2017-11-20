# -*- coding: utf-8 -*-

__all__ = ('CardBattleMain', )

from functools import partial
import queue

import yaml
import kivy
kivy.require(r'1.10.0')
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.factory import Factory
from kivy.resources import resource_find
from kivy.properties import (
    ObjectProperty, NumericProperty, StringProperty, ListProperty,
    BooleanProperty
)

import setup_logging
logger = setup_logging.get_logger(__name__)
from smartobject import SmartObject
from dragrecognizer import DragRecognizerDashLine
from magnetacrosslayout import MagnetAcrossLayout
from basicwidgets import (
    replace_widget, bring_widget_to_front, fadeout_widget, AutoLabel,
)
from custommodalview import CustomModalViewNoBackground
from detailviewer import UnitPrototypeDetailViewer, SpellPrototypeDetailViewer
from notificater import Notificater
from .cardbattleplayer import Player, CardBattlePlayer
from .card import UnknownCard, UnitCard, SpellCard
from .timer import Timer
from .turnendbutton import TurnEndButton


Builder.load_string(r"""
#:kivy 1.10.0

#:set OVERLAY_COLOR_DICT { r'normal': [0, 0, 0, 0], r'down': [1, 1, 1, 0.15], }

<Cell>:
    canvas:
        Color:
            rgba: 1, 1, 1, 0.2
        Line:
            rectangle: self.x, self.y, self.width, self.height
    canvas.after:
        Color:
            rgba: OVERLAY_COLOR_DICT[self.state]
        Rectangle:
            pos: self.pos
            size: self.size

<CardBattleBoardsParent@FloatLayout+StencilAll>:

<CardLayer@DragRecognizerDashLine+Widget>:

<CardBattleMain>:
    card_layer: id_card_layer
    popup_layer: id_popup_layer
    notificater: id_notificater
    timer: id_timer
    BoxLayout:
        orientation: 'vertical'
        Widget:
            id: id_playerwidget_opponent
            size_hint_y: 0.15
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: 0.7
            CardBattleBoardsParent:
                id: id_boards_parent
                size_hint_x: 0.8
            BoxLayout:
                orientation: 'vertical'
                size_hint_x: 0.2
                Widget:
                FloatLayout:
                    Timer:
                        id: id_timer
                        line_width: 4
                        pos:self.parent.pos
                    AutoLabel:
                        size_hint: 0.5, 0.5
                        pos_hint: {'center_x': 0.5, 'center_y': 0.5, }
                        text: 'Turn\n  ' + str(root.gamestate.nth_turn)
                FloatLayout:
                    TurnEndButton:
                        length: min(*self.parent.size)
                        disabled: not root.gamestate.is_myturn
                        size_hint: None, None
                        width: self.length * 0.8
                        height: self.width
                        pos_hint: {'center_x': 0.5, 'center_y': 0.5, }
                        on_press: root.on_turnendbutton_press()
        Widget:
            id: id_playerwidget_mine
            size_hint_y: 0.15
    CardLayer:
        id: id_card_layer
    FloatLayout:
        id: id_popup_layer
        Notificater:
            id: id_notificater
            size_hint: 0.5, 0.3
            pos_hint: {'center_x': 0.5, 'center_y': 0.5, }
            default_font_size: 20
""")


def copy_dictionary(dictionary, *, keys_exclude):
    return {
        key: value
        for key, value in dictionary.items() if key not in keys_exclude}


class GameState(Factory.EventDispatcher):
    nth_turn = NumericProperty()
    is_myturn = BooleanProperty()


class Cell(Factory.ButtonBehavior, Factory.FloatLayout):

    id = StringProperty()

    def __init__(self, **kwargs):
        super(Cell, self).__init__(**kwargs)
        self._card = None

    def __str__(self, **kwargs):
        return self.id

    def is_empty(self):
        return self._card is None

    def is_not_empty(self):
        return self._card is not None

    @property
    def card(self):
        return self._card

    def attach(self, card):
        if self.is_empty():
            card.pos_hint = {r'x': 0, r'y': 0, }
            card.size_hint = (1, 1,)
            self.add_widget(card)
            self._card = card
        else:
            logger.error(rf"The cell '{self.id}' already has a unit.")

    def detach(self):
        if self.is_empty():
            logger.error(rf"The cell '{self.id}' doesn't have any units.")
        else:
            card = self._card
            self.remove_widget(card)
            self._card = None
            return card


class BoardWidget(Factory.GridLayout):

    def __init__(self, **kwargs):
        self.is_initialized = False
        kwargs.setdefault(r'cols', 5)
        kwargs.setdefault(r'rows', 7)
        kwargs.setdefault(r'spacing', 10)
        kwargs.setdefault(r'padding', [10])
        super(BoardWidget, self).__init__(**kwargs)

        cols = kwargs['cols']
        rows = kwargs['rows']

        for i in range(cols):
            cell = Cell(id='opponent{}'.format(i))
            self.add_widget(cell)
        self.row_list = [
            [
                Cell(id='{},{}'.format(col_index, row_index))
                for col_index in range(cols)
            ]
            for row_index in range(rows - 2)
        ]
        self.cells = [cell for row in self.row_list for cell in row]
        for cell in self.cells:
            self.add_widget(cell)
        for i in range(cols):
            cell = Cell(id='mine{}'.format(i))
            self.add_widget(cell)

        self.is_initialized = True

    def add_widget(self, *args, **kwargs):
        if self.is_initialized:
            logger.critical(r"Don't add widgets after __init__().")
        else:
            return super().add_widget(*args, **kwargs)

    def on_cols(self, __, value):
        if self.is_initialized:
            logger.critical(r"Property 'cols' has changed after __init__().")

    def on_rows(self, __, value):
        if self.is_initialized:
            logger.critical(r"Property 'rows' has changed after __init__().")


class QueueReciever:

    def __init__(self, *, player_id, queue_instance):
        self.player_id = player_id
        self.queue_instance = queue_instance

    def recieve(self, timeout):
        try:
            return self.queue_instance.get(timeout=timeout)
        except queue.Empty:
            raise TimeoutError(
                'Failed to get item from queue within {} seconds.'.format(
                    timeout))


class QueueSender:

    def __init__(self, *, player_id, queue_instance):
        self.player_id = player_id
        self.queue_instance = queue_instance

    def send(self, item):
        self.queue_instance.put(item=item)


class CardBattleMain(Factory.RelativeLayout):

    card_layer = ObjectProperty()
    popup_layer = ObjectProperty()
    notificater = ObjectProperty()
    timer = ObjectProperty()
    # gamestate = ObjectProperty()

    def __init__(self, *, player_id, iso639, inqueue=None, outqueue=None, **kwargs):
        self.gamestate = GameState(
            nth_turn=0, is_myturn=False)
        super().__init__(**kwargs)
        self.inqueue = queue.Queue() if inqueue is None else inqueue
        self.outqueue = queue.Queue() if outqueue is None else outqueue
        self.player_id = player_id
        self.timer.bind(int_current_time=self.on_timer_tick)
        self._iso639 = iso639
        self._localize_str = lambda s: s  # この関数は後に実装する

    def on_timer_tick(self, timer, seconds):
        time_limit = timer.time_limit
        if self.gamestate.is_myturn:
            if seconds >= time_limit:
                self.send_command(
                    type='turn_end',
                    params=None)
            elif seconds == time_limit - 5:
                timer.color = (1, 0, 0, 1, )
                self.on_command_notification(params=SmartObject(
                    message=self._localize_str('残り5秒'), type='warning'))

    def on_turnendbutton_press(self):
        self.send_command(type='turn_end', params=None)

    def send_command(self, *, type, params):
        json_command = SmartObject(
            klass='Command',
            type=type,
            nth_turn=self.gamestate.nth_turn,
            params=params).so_to_json(indent=2)
        logger.debug('[C] CLIENT COMMAND')
        logger.debug(json_command)
        self.outqueue.put(json_command)

    def get_reciever(self):
        return QueueReciever(
            player_id=self.player_id,
            queue_instance=self.outqueue)

    def get_sender(self):
        return QueueSender(
            player_id=self.player_id,
            queue_instance=self.inqueue)

    def wrap_in_magnet(self, card):
        magnet = MagnetAcrossLayout(
            duration=0.5,
            actual_parent=self.card_layer)
        magnet.add_widget(card)
        return magnet

    def on_start(self):
        # 受信Queueの監視を始める
        Clock.schedule_interval(self.check_inqueue, 0.3)

    def check_inqueue(self, __):
        inqueue = self.inqueue
        try:
            command = SmartObject.load_from_json(inqueue.get_nowait())
            command_handler = getattr(self, 'on_command_' + command.type, None)
            if command_handler:
                command_handler(command.params)
            else:
                logger.critical('[C] Unknown command:' + command.type)
        except queue.Empty as e:
            pass

    @staticmethod
    def _merge_database(smartobject_dict, dict_dict):
        r'''internal use'''
        keys = frozenset(smartobject_dict.keys())
        if keys != frozenset(dict_dict.keys()):
            logger.critical('databaseのkeyが一致していません。')
            return
        return {
            key: SmartObject(**dict_dict[key], **smartobject_dict[key].__dict__)
            for key in keys
        }

    def on_command_game_begin(self, params):
        if hasattr(self, '_on_command_game_begin_called'):
            logger.critical("[C] Don't call on_command_game_begin multiple times.")
            return
        self._on_command_game_begin_called = True

        # ----------------------------------------------------------------------
        # Databaseを初期化
        # ----------------------------------------------------------------------

        # UnitPrototypeの辞書
        with open(
                resource_find('unit_prototype_{}.yaml'.format(self._iso639)),
                'rt', encoding='utf-8') as reader:
            self.unit_prototype_dict = CardBattleMain._merge_database(
                params.unit_prototype_dict.__dict__,
                yaml.load(reader))
        # SpellPrototypeの辞書
        with open(
                resource_find('spell_prototype_{}.yaml'.format(self._iso639)),
                'rt', encoding='utf-8') as reader:
            self.spell_prototype_dict = CardBattleMain._merge_database(
                params.spell_prototype_dict.__dict__,
                yaml.load(reader))
        # 利便性の為、UnitPrototypeの辞書とSpellPrototypeの辞書を合成した辞書も作る
        self.prototype_dict = {
            **self.unit_prototype_dict, **self.spell_prototype_dict, }
        # Skillの辞書
        with open(
                resource_find('skill_{}.yaml'.format(self._iso639)),
                'rt', encoding='utf-8') as reader:
            self.skill_dict = {
                key: SmartObject(type='Skill', id=key, **value)
                for key, value in yaml.load(reader).items()
            }
        # Tagの翻訳用辞書
        with open(
                resource_find('tag_translation_{}.yaml'.format(self._iso639)),
                'rt', encoding='utf-8') as reader:
            self.tag_translation_dict = yaml.load(reader)

        # 画像Fileの辞書
        with open(
                resource_find('imagefile_dict.yaml'),
                'rt', encoding='utf-8') as reader:
            self.imagefile_dict = yaml.load(reader)
        # Cardの辞書
        self.card_dict = {}

        # ----------------------------------------------------------------------
        # Playerを初期化
        # ----------------------------------------------------------------------
        self.player_list = [
            Player(**copy_dictionary(
                player.__dict__,
                keys_exclude=('n_tefuda', 'klass', )
            )) for player in params.player_list]
        self.player_dict = {
            player.id: player for player in self.player_list
        }
        self.playerwidget_dict = {
            player.id: CardBattlePlayer(player=player)
            for player in self.player_list
        }
        for key, playerwidget in self.playerwidget_dict.items():
            replace_widget(
                old=self.ids[
                    'id_playerwidget_mine'
                    if key == self.player_id
                    else 'id_playerwidget_opponent'
                ],
                new=playerwidget)
        # ----------------------------------------------------------------------
        #
        # ----------------------------------------------------------------------
        self.is_black = self.player_list[0].id == self.player_id  # 先手か否か
        self.board = BoardWidget(
            cols=params.board_size[0],
            rows=params.board_size[1] + 2,
            size_hint=(1, 1.25, ),
            pos_hint={'center_y': 0.5, 'center_x': 0.5}
        )
        self.ids.id_boards_parent.add_widget(self.board)
        self.timer.time_limit = params.timeout

    def on_command_turn_begin(self, params):
        gamestate = self.gamestate
        is_myturn = params.player_id == self.player_id
        gamestate.is_myturn = is_myturn
        gamestate.nth_turn = params.nth_turn
        label = AutoLabel(
            text=(
                self._localize_str('あなたの番') if is_myturn
                else self._localize_str(' 相手の番 ')),
            color=(0, 0, 0, 1),
            outline_color=(1, 1, 1, ),
            outline_width=3,
        )
        self.popup_layer.add_widget(label)
        fadeout_widget(label)
        self.timer.color = (1, 1, 1, 1, )
        self.timer.start()

    def on_command_turn_end(self, params):
        gamestate = self.gamestate
        if gamestate.nth_turn != params.nth_turn:
            logger.critical("[C] 'nth_turn' mismatched on 'on_command_turn_end'.")
        self.gamestate.is_myturn = False
        self.timer.stop()

    def on_command_notification(self, params):
        self.notificater.add_notification(
            text=params.message,
            icon_key=params.type,
            duration=3)

    def on_command_draw(self, params):
        r'''drawは「描く」ではなく「(カードを)引く」の意'''
        card_layer = self.card_layer
        card_id = params.card_id
        card_pos = (card_layer.right, card_layer.top - card_layer.height / 2, )
        if params.drawer_id == self.player_id:
            prototype_id = self.card_dict[card_id].prototype_id
            prototype = self.prototype_dict[prototype_id]
            # print(prototype)
            if prototype.klass == 'UnitPrototype':
                card = UnitCard(
                    prototype=prototype,
                    background_color=self.player_dict[self.player_id].color,
                    imagefile=self.imagefile_dict[prototype_id],
                    id=card_id,
                    pos=card_pos)
            elif prototype.klass == 'SpellPrototype':
                card = SpellCard(
                    prototype=prototype,
                    background_color=self.player_dict[self.player_id].color,
                    imagefile=self.imagefile_dict[prototype_id],
                    id=card_id,
                    pos=card_pos)
        else:
            card = UnknownCard(pos=card_pos)
        playerwidget = self.playerwidget_dict[params.drawer_id]
        magnet = self.wrap_in_magnet(card)
        card.bind(on_release=partial(self.show_detail_of_a_card, magnet=magnet))
        playerwidget.ids.id_tefuda.add_widget(magnet)
        player = self.player_dict[params.drawer_id]
        player.n_cards_in_deck -= 1
        player.tefuda.append(params.card_id)
        # logger.debug(params.drawer_id)
        # logger.debug(str(playerstate.pos))
        # logger.debug(str(playerstate.size))

    def on_command_set_card_info(self, params):
        self.card_dict[params.card.id] = params.card

    # def on_operation_click(self, cell):
    #     logger.debug(r'on_operation_click :' + cell.id)
    #     if cell.is_not_empty():
    #         self.show_detail_of_a_card(cell)

    def show_detail_of_a_card(self, card, *, magnet):
        tefuda_layout = magnet.parent
        tefuda_layout.remove_widget(magnet)
        # modalview = ModalViewWithoutBackground(
        modalview = CustomModalViewNoBackground(
            attach_to=self,
            auto_dismiss=True,
            size_hint=(0.95, 0.6, ),
            pos_hint={'center_x': 0.5, 'center_y': 0.5, })
        if isinstance(card, UnitCard):
            viewer = UnitPrototypeDetailViewer(
                card=card, magnet=magnet,
                tag_translation_dict=self.tag_translation_dict,
                skill_dict=self.skill_dict)
        elif isinstance(card, SpellCard):
            viewer = SpellPrototypeDetailViewer(
                prototype=card.prototype,
                widget=magnet,
                localize_str=self._localize_str,
                tag_translation_dict=self.tag_translation_dict,
                skill_dict=self.skill_dict)
        else:
            viewer = magnet
        modalview.add_widget(viewer)

        def on_dismiss(*args):
            bring_widget_to_front(card)
            magnet.parent.remove_widget(magnet)
            tefuda_layout.add_widget(magnet)
        modalview.bind(on_dismiss=on_dismiss)
        bring_widget_to_front(card)
        modalview.open(self)

    # def show_detail_of_a_card(self, cell):
    #     modalview = Factory.ModalView(
    #         auto_dismiss=True,
    #         size_hint=(None, 0.9,),
    #         width=self.height * 0.66
    #     )
    #     modalview.bind(height=(
    #         lambda widget, value: setattr(widget, r'width', value * 0.66)
    #     ))
    #     cell_temp = Cell()
    #     cell_temp.attach(cell.detach())
    #     modalview.add_widget(cell_temp)
    #     modalview.bind(
    #         on_dismiss=lambda *args: cell.attach(cell_temp.detach())
    #     )
    #     modalview.open(self)

# class CardBattleMain2(DragRecognizerDashLine):

#     def on_drag_start(self, touch):
#         super().on_drag_start(touch)
#         cell_from = None
#         for cell in self.board.children:
#             if cell.collide_point(*touch.opos):
#                 cell_from = cell
#                 cell_from.state = r'down'

#         ud_key = self._get_uid(prefix=r'CardBattleMain')  # _get_uidは親ClassのMethod
#         touch.ud[ud_key] = {
#             r'inst_list': inst_list,
#             r'cell_from': cell_from,
#             r'cell_to': cell_from,
#         }

#     def on_being_dragged(self, touch):
#         super().on_being_dragged(touch)
#         ud_key = self._get_uid(prefix=r'CardBattleMain')
#         ud = touch.ud[ud_key]

#         cell_from = ud[r'cell_from']
#         previous_cell_to = ud[r'cell_to']
#         current_cell_to = None
#         for cell in self.board.children:
#             if cell.collide_point(*touch.pos):
#                 current_cell_to = cell
#         ud[r'cell_to'] = current_cell_to

#         if current_cell_to is previous_cell_to:
#             pass
#         else:
#             condition1 = previous_cell_to is not None
#             condition2 = previous_cell_to is not cell_from
#             if condition1 and condition2:
#                 previous_cell_to.state = r'normal'
#             if current_cell_to is not None:
#                 current_cell_to.state = r'down'

#     def on_drag_finish(self, touch):
#         super().on_drag_finish(touch)
#         ud_key = self._get_uid(prefix=r'CardBattleMain')
#         ud = touch.ud[ud_key]

#         cell_from = ud[r'cell_from']
#         cell_to = ud[r'cell_to']

#         if cell_from is not None:
#             cell_from.state = r'normal'
#         if cell_to is not None:
#             cell_to.state = r'normal'

#         if cell_from is None or cell_to is None:
#             return
#         if cell_from is cell_to:
#             pass
#         else:
#             self.on_operation_drag(cell_from, cell_to)

#     def on_operation_click(self, cell):
#         logger.debug(r'on_operation_click :' + cell.id)
#         if cell.is_not_empty():
#             self.show_detail_of_a_card(cell)

#     def on_operation_drag(self, cell_from, cell_to):
#         logger.debug(rf"on_operation_drag : {cell_from} to {cell_to}")
#         if (
#             cell_from.is_not_empty() and
#             self.gamestate.current_player.klass is PlayerType.HUMAN and
#             self.gamestate.current_player is cell_from.card.player
#         ):
#             if cell_to.is_empty():
#                 self.send_command(
#                     CommandType.MOVE, cell_from, cell_to
#                 )
#             elif cell_from.card.player is cell_to.card.player:
#                 self.send_command(
#                     CommandType.SUPPORT, cell_from, cell_to
#                 )
#             else:
#                 self.send_command(
#                     CommandType.ATTACK, cell_from, cell_to
#                 )

#     def show_detail_of_a_card(self, cell):
#         modalview = Factory.ModalView(
#             auto_dismiss=True,
#             size_hint=(None, 0.9,),
#             width=self.height * 0.66
#         )
#         modalview.bind(
#             height=(
#                 lambda widget, value: setattr(widget, r'width', value * 0.66)
#             )
#         )
#         cell_temp = Cell()
#         cell_temp.attach(cell.detach())
#         modalview.add_widget(cell_temp)
#         modalview.bind(
#             on_dismiss=lambda *args: cell.attach(cell_temp.detach())
#         )
#         modalview.open(self)

#     def send_command(self, klass, cell_from, cell_to):
#         logger.debug(rf"send command : {klass} : {cell_from} to {cell_to}")

