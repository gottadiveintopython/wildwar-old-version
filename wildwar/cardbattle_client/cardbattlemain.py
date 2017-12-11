# -*- coding: utf-8 -*-

__all__ = ('CardBattleMain', )

import functools

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
from custommodalview import CustomModalView, CustomModalViewNoBackground
from detailviewer import (
    UnitPrototypeDetailViewer, SpellPrototypeDetailViewer,
    UnitInstanceDetailViewer, )
from notificator import Notificator
from .cardbattleplayer import Player, CardBattlePlayer
from .cardwidget import UnknownCardWidget, UnitCardWidget, SpellCardWidget
from .unitinstancewidget import UnitInstanceWidget
from .timer import Timer
from .turnendbutton import TurnEndButton
from arrowanimation import play_stretch_animation, OutlinedPolygon
from .battleanimation import play_battle_animation


Builder.load_string(r"""
#:kivy 1.10.0

#:set OVERLAYCOLOR_DICT { 'normal': [0, 0, 0, 0], 'down': [1, 1, 1, 0.15], }

<Cell>:
    canvas:
        Color:
            rgba: 1, 1, 1, 0.2
        Line:
            rectangle: self.x, self.y, self.width, self.height
    canvas.after:
        Color:
            rgba: OVERLAYCOLOR_DICT[self.state]
        Rectangle:
            pos: self.pos
            size: self.size

<CardBattleBoardsParent@FloatLayout+StencilAll>:

<CardBattleMain>:
    card_widget_layer: id_card_widget_layer
    popup_layer: id_popup_layer
    notificator: id_notificator
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
        id: id_card_widget_layer
    FloatLayout:
        id: id_popup_layer
        Notificator:
            id: id_notificator
            size_hint: 0.7, 0.3
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


class UIOptions(Factory.EventDispatcher):
    skip_battle_animation = BooleanProperty()


class UnitInstance(Factory.EventDispatcher):
    klass = StringProperty()
    id = StringProperty()
    prototype_id = StringProperty()
    player_id = StringProperty()
    n_turns_until_movable = NumericProperty()
    skill_id_list = ListProperty()
    tag_list = ListProperty()
    cost = NumericProperty()
    o_power = NumericProperty()
    o_attack = NumericProperty()
    o_defense = NumericProperty()
    power = NumericProperty()
    attack = NumericProperty()
    defense = NumericProperty()


class Cell(Factory.ButtonBehavior, Factory.FloatLayout):

    id = StringProperty()
    klass = StringProperty('Cell')

    def __str__(self, **kwargs):
        return self.id

    def is_empty(self):
        return len(self.children) == 0

    def is_not_empty(self):
        return len(self.children) != 0

    def add_widget(self, widget, *args, **kwargs):
        if self.is_empty():
            widget.pos_hint = {r'x': 0, r'y': 0, }
            widget.size_hint = (1, 1,)
            return super().add_widget(widget, *args, **kwargs)
        else:
            logger.error("[C] The cell '{}' already has a unit.".format(self.id))

    def remove_widget(self, widget, *args, **kwargs):
        if self.is_empty():
            logger.error("[C] The cell '{}' doesn't have unit.".format(self.id))
        elif self.children[0] is widget:
            return super().remove_widget(widget, *args, **kwargs)
        else:
            logger.error("[C] That's not my child: " + str(widget))


class BoardWidget(Factory.GridLayout):

    def __init__(self, *, is_black, **kwargs):
        self.is_initialized = False
        kwargs.setdefault(r'cols', 5)
        kwargs.setdefault(r'rows', 7)
        kwargs.setdefault(r'spacing', 10)
        kwargs.setdefault(r'padding', [10])
        super(BoardWidget, self).__init__(**kwargs)

        cols = kwargs['cols']
        rows = kwargs['rows']

        self.cell_list = cell_list = []
        if is_black:
            cell_list.extend(Cell(id='w' + str(i)) for i in range(cols))
            cell_list.extend(
                Cell(id=(str(row_index) + str(col_index)))
                for row_index in range(rows - 2)
                for col_index in range(cols))
            cell_list.extend(Cell(id='b' + str(i)) for i in range(cols))
        else:
            cell_list.extend(
                Cell(id='b' + str(cols - i - 1))
                for i in range(cols))
            cell_list.extend(
                Cell(id=(str(rows - row_index - 3) + str(cols - col_index - 1)))
                for row_index in range(rows - 2)
                for col_index in range(cols))
            cell_list.extend(
                Cell(id='w' + str(cols - i - 1))
                for i in range(cols))

        for cell in cell_list:
            self.add_widget(cell)
        self.cell_dict = {cell.id: cell for cell in cell_list}

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


class CardLayer(DragRecognizerDashLine, Factory.Widget):

    board = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_event_type('on_operation_drag')
        # Don't use self.__class__.__name__ instead of 'CardLayer.'
        self.__ud_key = 'CardLayer.' + str(self.uid)

    def on_drag_start(self, touch):
        super().on_drag_start(touch)
        widget_from = None
        for child in self.children:
            if child.collide_point(*touch.opos):
                widget_from = child
                widget_from.state = 'down'
                break
        if widget_from is None:
            touch.push()
            touch.apply_transform_2d(self.to_window)
            touch.apply_transform_2d(self.board.to_widget)
            for cell in self.board.cell_list:
                if cell.collide_point(*touch.opos):
                    widget_from = cell
                    widget_from.state = 'down'
                    break
            touch.pop()

        touch.ud[self.__ud_key] = {
            'widget_from': widget_from,
            'widget_to': widget_from,
        }

    def on_being_dragged(self, touch):
        super().on_being_dragged(touch)
        ud = touch.ud[self.__ud_key]

        widget_from = ud['widget_from']
        previous_widget_to = ud['widget_to']
        current_widget_to = None
        for child in self.children:
            if child.collide_point(*touch.pos):
                current_widget_to = child
                break
        if current_widget_to is None:
            touch.push()
            touch.apply_transform_2d(self.to_window)
            touch.apply_transform_2d(self.board.to_widget)
            for cell in self.board.cell_list:
                if cell.collide_point(*touch.pos):
                    current_widget_to = cell
                    break
            touch.pop()
        ud['widget_to'] = current_widget_to

        if current_widget_to is previous_widget_to:
            pass
        else:
            condition1 = previous_widget_to is not None
            condition2 = previous_widget_to is not widget_from
            if condition1 and condition2:
                previous_widget_to.state = 'normal'
            if current_widget_to is not None:
                current_widget_to.state = 'down'

    def on_drag_finish(self, touch):
        super().on_drag_finish(touch)
        ud = touch.ud[self.__ud_key]

        widget_from = ud['widget_from']
        widget_to = ud['widget_to']

        if widget_from is not None:
            widget_from.state = 'normal'
        if widget_to is not None:
            widget_to.state = 'normal'

        if widget_from is None or widget_to is None:
            return
        if widget_from is widget_to:
            pass
        else:
            self.dispatch('on_operation_drag', widget_from, widget_to)

    def on_operation_drag(*args):
        pass
        # logger.debug(rf"on_operation_drag : {cell_from} to {cell_to}")
        # if (
        #     cell_from.is_not_empty() and
        #     self.gamestate.current_player.klass is PlayerType.HUMAN and
        #     self.gamestate.current_player is cell_from.card.player
        # ):
        #     if cell_to.is_empty():
        #         self.send_command(
        #             CommandType.MOVE, cell_from, cell_to
        #         )
        #     elif cell_from.card.player is cell_to.card.player:
        #         self.send_command(
        #             CommandType.SUPPORT, cell_from, cell_to
        #         )
        #     else:
        #         self.send_command(
        #             CommandType.ATTACK, cell_from, cell_to
        #         )


class CardBattleMain(Factory.RelativeLayout):

    card_widget_layer = ObjectProperty()
    popup_layer = ObjectProperty()
    notificator = ObjectProperty()
    timer = ObjectProperty()
    # gamestate = ObjectProperty()

    def __init__(self, *, communicator, iso639, **kwargs):
        self.gamestate = GameState(
            nth_turn=0, is_myturn=False)
        self.uioptions = UIOptions(
            skip_battle_animation=False)
        super().__init__(**kwargs)
        self._communicator = communicator
        self._player_id = communicator.player_id
        self.timer.bind(int_current_time=self.on_timer_tick)
        self._iso639 = iso639
        self._localize_str = lambda s: s  # この関数は後に実装する
        self.card_widget_layer.bind(on_operation_drag=self.on_operation_drag)
        self._command_recieving_trigger = Clock.create_trigger(
            self._try_to_recieve_command, 0.3)

    def on_operation_drag(self, card_widget_layer, widget_from, widget_to):
        if not self.gamestate.is_myturn:
            self.on_command_notification(params=SmartObject(
                message=self._localize_str('今はあなたの番ではありません'),
                type='disallowed'))
            return
        elif widget_from.klass == 'UnitInstanceWidget':
            cell_from_id = widget_from.magnet.parent.id
            if widget_to.klass == 'Cell':
                cell_to = widget_to
            elif widget_to.klass == 'UnitInstanceWidget':
                cell_to = widget_to.magnet.parent
            else:
                cell_to = None
            if cell_to:
                self.send_command(
                    type='cell_to_cell',
                    params=SmartObject(
                        cell_from_id=cell_from_id,
                        cell_to_id=cell_to.id))
                return
        elif widget_from.klass == 'UnitCardWidget':
            if widget_to.klass == 'Cell':
                self.send_command(
                    type='use_unitcard',
                    params=SmartObject(
                        card_id=widget_from.id,
                        cell_to_id=widget_to.id))
                return
        elif widget_from.klass == 'SpellCardWidget':
            if widget_to.klass == 'Cell':
                cell_to = widget_to
            elif widget_to.klass == 'UnitInstanceWidget':
                cell_to = widget_to.magnet.parent
            else:
                cell_to = None
            if cell_to:
                self.send_command(
                    type='use_spellcard',
                    params=SmartObject(
                        card_id=widget_from.id,
                        cell_to_id=cell_to.id))
                return
        elif widget_from.klass == 'Cell':
            return
        self.on_command_notification(params=SmartObject(
            message=self._localize_str('無効な操作です'), type='disallowed'))

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
        self._communicator.send(json_command)

    def wrap_in_magnet(self, card):
        magnet = MagnetAcrossLayout(
            duration=0.5,
            actual_parent=self.card_widget_layer)
        magnet.add_widget(card)
        return magnet

    def on_start(self):
        self._command_recieving_trigger()

    def _try_to_recieve_command(self, __):
        jsonstr = self._communicator.recieve_nowait()
        if jsonstr is None:
            self._command_recieving_trigger()
            return
        command = SmartObject.load_from_json(jsonstr)
        command_handler = getattr(self, 'on_command_' + command.type, None)
        if command_handler:
            command_handler(command.params)
        else:
            logger.critical('[C] Unknown command: ' + command.type)
            self._command_recieving_trigger()

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

    def doesnt_need_to_wait_for_the_animation_to_complete(command_handler):
        @functools.wraps(command_handler)
        def wrapper(self, *args, **kwargs):
            try:
                return command_handler(self, *args, **kwargs)
            finally:
                self._command_recieving_trigger()
        return wrapper

    @doesnt_need_to_wait_for_the_animation_to_complete
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
            self.unitp_dict = CardBattleMain._merge_database(
                params.unitp_dict.__dict__,
                yaml.load(reader))
        # SpellPrototypeの辞書
        with open(
                resource_find('spell_prototype_{}.yaml'.format(self._iso639)),
                'rt', encoding='utf-8') as reader:
            self.spellp_dict = CardBattleMain._merge_database(
                params.spellp_dict.__dict__,
                yaml.load(reader))
        # 利便性の為、UnitPrototypeの辞書とSpellPrototypeの辞書を合成した辞書も作る
        self.prototype_dict = {
            **self.unitp_dict, **self.spellp_dict, }
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
        self.card_widget_dict = {}
        # Unitinstanceの辞書
        self.uniti_dict = {}
        self.uniti_widget_dict = {}

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
                self.ids[
                    'id_playerwidget_mine'
                    if key == self._player_id
                    else 'id_playerwidget_opponent'
                ],
                playerwidget)
        # ----------------------------------------------------------------------
        #
        # ----------------------------------------------------------------------
        self.is_black = self.player_list[0].id == self._player_id  # 先手か否か
        self.board = BoardWidget(
            is_black=self.is_black,
            cols=params.board_size[0],
            rows=params.board_size[1],
            size_hint=(1, 1.25, ),
            pos_hint={'center_y': 0.5, 'center_x': 0.5}
        )
        self.ids.id_boards_parent.add_widget(self.board)
        self.card_widget_layer.board = self.board
        self.timer.time_limit = params.timeout

    def create_card_widget(self, *, card_id, player):
        card = self.card_dict.get(card_id)
        if card is None:
            card_widget = UnknownCardWidget()
        else:
            prototype_id = card.prototype_id
            prototype = self.prototype_dict[prototype_id]
            # print(prototype)
            if prototype.klass == 'UnitPrototype':
                card_widget = UnitCardWidget(
                    prototype=prototype,
                    background_color=player.color,
                    imagefile=self.imagefile_dict[prototype_id],
                    id=card_id)
            elif prototype.klass == 'SpellPrototype':
                card_widget = SpellCardWidget(
                    prototype=prototype,
                    background_color=player.color,
                    imagefile=self.imagefile_dict[prototype_id],
                    id=card_id)
        return card_widget

    @doesnt_need_to_wait_for_the_animation_to_complete
    def on_command_game_end(self, params):
        localize_str = self._localize_str
        winner_id = params.winner_id
        text = localize_str('引き分け') if winner_id == '$draw' else (
            localize_str('勝利') if winner_id == self._player_id else
            localize_str('敗北'))
        label = AutoLabel(
            text=text,
            color=(0, 0, 0, 1),
            outline_color=(1, 1, 1, ),
            outline_width=3,
            pos_hint={'center_x': .5, 'center_y': .5, },
            size_hint=(.6, .1, ),
        )
        self.popup_layer.add_widget(label)
        for card_widget in self.card_widget_dict.values():
            card_widget.opacity = 0
        for playerwidget in self.playerwidget_dict.values():
            playerwidget.opacity = 0
        fadeout_widget(label, duration=4)

    @doesnt_need_to_wait_for_the_animation_to_complete
    def on_command_reset_stats(self, params):
        for uniti in self.uniti_dict.values():
            uniti.power = uniti.o_power
            uniti.attack = uniti.o_attack
            uniti.defense = uniti.o_defense

    @doesnt_need_to_wait_for_the_animation_to_complete
    def on_command_set_max_cost(self, params):
        player = self.player_dict[params.player_id]
        player.max_cost = params.value

    @doesnt_need_to_wait_for_the_animation_to_complete
    def on_command_reduce_n_turns_until_movable_by(self, params):
        def internal(uniti):
            if uniti.n_turns_until_movable > n:
                uniti.n_turns_until_movable -= n
            else:
                uniti.n_turns_until_movable = 0
        n = params.n
        target_id = params.target_id
        if target_id == '$all':
            for uniti in self.uniti_dict.values():
                internal(uniti)
        else:
            internal(self.uniti_dict[target_id])

    @doesnt_need_to_wait_for_the_animation_to_complete
    def on_command_turn_begin(self, params):
        gamestate = self.gamestate
        is_myturn = params.player_id == self._player_id
        gamestate.is_myturn = is_myturn
        gamestate.nth_turn = params.nth_turn
        label = AutoLabel(
            text=(
                self._localize_str('あなたの番') if is_myturn
                else self._localize_str(' 相手の番 ')),
            color=(0, 0, 0, 1),
            outline_color=(1, 1, 1, ),
            outline_width=3,
            pos_hint={'center_x': .5, 'center_y': .5, },
            size_hint=(.6, .1, ),
        )
        self.popup_layer.add_widget(label)
        fadeout_widget(label)
        self.timer.color = (1, 1, 1, 1, )
        self.timer.start()

    @doesnt_need_to_wait_for_the_animation_to_complete
    def on_command_turn_end(self, params):
        gamestate = self.gamestate
        if gamestate.nth_turn != params.nth_turn:
            logger.critical("[C] 'nth_turn' mismatched on 'on_command_turn_end'.")
        self.gamestate.is_myturn = False
        self.timer.stop()

    @doesnt_need_to_wait_for_the_animation_to_complete
    def on_command_notification(self, params):
        self.notificator.add_notification(
            text=self._localize_str(params.message),
            icon_key=params.type,
            duration=3)

    @doesnt_need_to_wait_for_the_animation_to_complete
    def on_command_draw(self, params):
        r'''drawは「描く」ではなく「(カードを)引く」の意'''
        card_id = params.card_id
        player_id = params.drawer_id
        player = self.player_dict[player_id]
        card_widget = self.create_card_widget(card_id=card_id, player=player)
        card_widget_layer = self.card_widget_layer
        card_widget.pos = (
            card_widget_layer.right,
            card_widget_layer.top - card_widget_layer.height / 2, )

        self.card_widget_dict[card_id] = card_widget
        playerwidget = self.playerwidget_dict[player_id]
        magnet = self.wrap_in_magnet(card_widget)
        card_widget.bind(on_release=self.show_detail_of_a_card)
        playerwidget.ids.id_tefuda.add_widget(magnet)
        player.n_cards_in_deck -= 1
        player.tefuda.append(card_id)
        # logger.debug(params.drawer_id)
        # logger.debug(str(playerstate.pos))
        # logger.debug(str(playerstate.size))

    def on_command_move(self, params):
        uniti_from_id = params.uniti_from_id
        uniti_from = self.uniti_dict[uniti_from_id]
        uniti_widget_from = \
            self.uniti_widget_dict[uniti_from_id]
        cell_to = self.board.cell_dict[params.cell_to_id]
        uniti_from.n_turns_until_movable += 1
        magnet = uniti_widget_from.magnet
        cell_from = magnet.parent
        cell_from.remove_widget(magnet)
        cell_to.add_widget(magnet)
        self._command_recieving_trigger()

    def on_command_attack(self, params):
        a_id = params.attacker_id
        d_id = params.defender_id
        dead_id = params.dead_id
        uniti_wid_dict = self.uniti_widget_dict
        uniti_dict = self.uniti_dict
        a = uniti_dict[a_id]
        d = uniti_dict[d_id]
        a_wid = uniti_wid_dict[a_id]
        d_wid = uniti_wid_dict[d_id]
        a_mag = a_wid.magnet
        d_mag = d_wid.magnet

        def internal():
            if dead_id == '$both':
                a_mag.parent.remove_widget(a_mag)
                a_mag.remove_widget(a_wid)
                d_mag.parent.remove_widget(d_mag)
                d_mag.remove_widget(d_wid)
                del uniti_wid_dict[a_id]
                del uniti_wid_dict[d_id]
                del uniti_dict[a_id]
                del uniti_dict[d_id]
            elif dead_id == a_id:
                a_mag.parent.remove_widget(a_mag)
                a_mag.remove_widget(a_wid)
                del uniti_wid_dict[a_id]
                del uniti_dict[a_id]
            elif dead_id == d_id:
                d_cell = d_mag.parent
                d_cell.remove_widget(d_mag)
                d_mag.remove_widget(d_wid)
                del uniti_wid_dict[d_id]
                del uniti_dict[d_id]
                a_mag.parent.remove_widget(a_mag)
                d_cell.add_widget(a_mag)
                a.n_turns_until_movable += 1
            self._compute_current_cost()
            self._command_recieving_trigger()

        def on_animation_complete():
            if self.uioptions.skip_battle_animation:
                a.power += a.attack
                a.attack = 0
                d.power += d.defense
                d.defense = 0
                a.power, d.power = a.power - d.power, d.power - a.power
                internal()
            else:
                if a.player_id == self._player_id:
                    is_attacker_mine = True
                    left_wid = a_wid
                    right_wid = d_wid
                else:
                    is_attacker_mine = False
                    left_wid = d_wid
                    right_wid = a_wid
                play_battle_animation(
                    parent=self, is_left_attacking_to_right=is_attacker_mine,
                    left_uniti_widget=left_wid, right_uniti_widget=right_wid,
                    on_complete=internal)

        card_widget_layer = self.card_widget_layer
        play_stretch_animation(
            parent=self,
            widget=OutlinedPolygon.create_from_template(
                'arrow2', line_width=2, line_color=(0, 1, 0, 1, )),
            root_pos=card_widget_layer.to_parent(*a_wid.center),
            head_pos=card_widget_layer.to_parent(*d_wid.center),
            anim_duration=0.6,
            on_complete=on_animation_complete)
        # from kivy.graphics import Line, Color
        # with self.canvas:
        #     Color(1, 1, 1, 1, )
        #     Line(
        #         points=(*attacker_widget.center, *defender_widget.center, ),
        #         width=2)

    def on_command_use_unitcard(self, params):
        card_id = params.card_id
        cell_to_id = params.cell_to_id
        uniti = params.uniti
        player_id = uniti.player_id
        player = self.player_dict[player_id]
        card_widget = self.card_widget_dict[card_id]
        # UnitInstanceとUnitInstanceWidgetを生成
        uniti = UnitInstance(**params.uniti.__dict__)
        uniti_id = uniti.id
        uniti_widget = UnitInstanceWidget(
            uniti=uniti,
            id=uniti_id,
            imagefile=self.imagefile_dict[uniti.prototype_id],
            background_color=player.color)
        self.uniti_dict[uniti_id] = uniti
        self.uniti_widget_dict[uniti_id] = uniti_widget
        # CardWidgetをUnitInstanceWidgetに置き換える
        uniti_widget.pos = card_widget.pos
        uniti_widget.size = card_widget.size
        magnet = card_widget.magnet
        magnet.remove_widget(card_widget)
        magnet.add_widget(uniti_widget)
        del self.card_widget_dict[card_id]
        del self.card_dict[card_id]
        # Touchした時に詳細が見れるようにする
        uniti_widget.bind(on_release=self.show_detail_of_a_unitinstance)
        #
        self._compute_current_cost()
        # 操作したのが自分なら単純な親の付け替え
        if self._player_id == player_id:
            magnet.parent.remove_widget(magnet)
            self.board.cell_dict[cell_to_id].add_widget(magnet)
            self._command_recieving_trigger()
        # 操作したのが自分でないならuniti_widgetを一旦中央に拡大表示
        else:
            modalview = CustomModalViewNoBackground(
                attach_to=self,
                auto_dismiss=False,
                size_hint=(0.4, 0.4, ),
                pos_hint={'center_x': 0.5, 'center_y': 0.5, })

            def on_open(modalview):
                magnet.parent.remove_widget(magnet)
                modalview.add_widget(magnet)
                Clock.schedule_once(lambda __: modalview.dismiss(), 0.8)

            def on_dismiss(modalview):
                modalview.remove_widget(magnet)
                self.board.cell_dict[cell_to_id].add_widget(magnet)
                self._command_recieving_trigger()
            modalview.bind(on_open=on_open, on_dismiss=on_dismiss)
            modalview.open()

    @doesnt_need_to_wait_for_the_animation_to_complete
    def on_command_set_card_info(self, params):
        self.card_dict[params.card.id] = params.card

    def _compute_current_cost(self):
        player_dict = self.player_dict
        cost_dict = {player_id: 0 for player_id in player_dict.keys()}
        for uniti in self.uniti_dict.values():
            cost_dict[uniti.player_id] += uniti.cost
        for player_id, cost in cost_dict.items():
            player_dict[player_id].cost = cost

    # def on_operation_click(self, cell):
    #     logger.debug(r'on_operation_click :' + cell.id)
    #     if cell.is_not_empty():
    #         self.show_detail_of_a_card(cell)

    def show_detail_of_a_card(self, card_widget):
        modalview = CustomModalView(
            attach_to=self,
            auto_dismiss=True,
            size_hint=(0.95, 0.6, ),)
        if card_widget.klass == 'UnitCardWidget':
            viewer = UnitPrototypeDetailViewer(
                prototype=card_widget.prototype,
                widget=UnitCardWidget(
                    prototype=card_widget.prototype,
                    imagefile=card_widget.imagefile,
                    background_color=card_widget.background_color),
                localize_str=self._localize_str,
                tag_translation_dict=self.tag_translation_dict,
                skill_dict=self.skill_dict)
        elif card_widget.klass == 'SpellCardWidget':
            viewer = SpellPrototypeDetailViewer(
                prototype=card_widget.prototype,
                widget=SpellCardWidget(
                    prototype=card_widget.prototype,
                    imagefile=card_widget.imagefile,
                    background_color=card_widget.background_color),
                localize_str=self._localize_str,
                tag_translation_dict=self.tag_translation_dict,
                skill_dict=self.skill_dict)
        else:
            viewer = None
        modalview.add_widget(viewer)
        modalview.open(self)

    def show_detail_of_a_unitinstance(self, uniti_widget):
        uniti = uniti_widget.uniti
        modalview = CustomModalView(
            attach_to=self,
            auto_dismiss=True,
            size_hint=(0.95, 0.6, ), )
        viewer = UnitInstanceDetailViewer(
            uniti=uniti,
            prototype=self.prototype_dict[uniti.prototype_id],
            widget=UnitInstanceWidget(
                uniti=uniti,
                imagefile=uniti_widget.imagefile,
                background_color=uniti_widget.background_color),
            localize_str=self._localize_str,
            tag_translation_dict=self.tag_translation_dict,
            skill_dict=self.skill_dict)
        modalview.add_widget(viewer)
        modalview.open(self)
