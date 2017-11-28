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
from notificater import Notificater
from .cardbattleplayer import Player, CardBattlePlayer
from .cardwidget import UnknownCardWidget, UnitCardWidget, SpellCardWidget
from .unitinstancewidget import UnitInstanceWidget
from .timer import Timer
from .turnendbutton import TurnEndButton


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
    cardwidget_layer: id_cardwidget_layer
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
        id: id_cardwidget_layer
    FloatLayout:
        id: id_popup_layer
        Notificater:
            id: id_notificater
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
    skip_attack_animation = BooleanProperty()


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

    cardwidget_layer = ObjectProperty()
    popup_layer = ObjectProperty()
    notificater = ObjectProperty()
    timer = ObjectProperty()
    # gamestate = ObjectProperty()

    def __init__(self, *, communicator, iso639, **kwargs):
        self.gamestate = GameState(
            nth_turn=0, is_myturn=False)
        self.uioptions = UIOptions(
            skip_attack_animation=True)
        super().__init__(**kwargs)
        self._communicator = communicator
        self._player_id = communicator.player_id
        self.timer.bind(int_current_time=self.on_timer_tick)
        self._iso639 = iso639
        self._localize_str = lambda s: s  # この関数は後に実装する
        self.cardwidget_layer.bind(on_operation_drag=self.on_operation_drag)
        self._command_recieving_trigger = Clock.create_trigger(
            self._try_to_recieve_command, 0.3)

    def on_operation_drag(self, cardwidget_layer, widget_from, widget_to):
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
            actual_parent=self.cardwidget_layer)
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
            logger.critical('[C] Unknown command:' + command.type)

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
        self.cardwidget_dict = {}
        # Unitinstanceの辞書
        self.unitinstance_dict = {}
        self.unitinstance_widget_dict = {}

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
                    if key == self._player_id
                    else 'id_playerwidget_opponent'
                ],
                new=playerwidget)
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
        self.cardwidget_layer.board = self.board
        self.timer.time_limit = params.timeout

    def create_cardwidget(self, *, card_id, player):
        card = self.card_dict.get(card_id)
        if card is None:
            cardwidget = UnknownCardWidget()
        else:
            prototype_id = card.prototype_id
            prototype = self.prototype_dict[prototype_id]
            # print(prototype)
            if prototype.klass == 'UnitPrototype':
                cardwidget = UnitCardWidget(
                    prototype=prototype,
                    background_color=player.color,
                    imagefile=self.imagefile_dict[prototype_id],
                    id=card_id)
            elif prototype.klass == 'SpellPrototype':
                cardwidget = SpellCardWidget(
                    prototype=prototype,
                    background_color=player.color,
                    imagefile=self.imagefile_dict[prototype_id],
                    id=card_id)
        return cardwidget

    @doesnt_need_to_wait_for_the_animation_to_complete
    def on_command_turn_begin(self, params):
        # 全Unitの行動可能になるまでのTurn数を減らす
        for unitinstance in self.unitinstance_dict.values():
            if unitinstance.n_turns_until_movable > 0:
                unitinstance.n_turns_until_movable -= 1
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
        self.notificater.add_notification(
            text=self._localize_str(params.message),
            icon_key=params.type,
            duration=3)

    @doesnt_need_to_wait_for_the_animation_to_complete
    def on_command_draw(self, params):
        r'''drawは「描く」ではなく「(カードを)引く」の意'''
        card_id = params.card_id
        player_id = params.drawer_id
        player = self.player_dict[player_id]
        cardwidget = self.create_cardwidget(card_id=card_id, player=player)
        cardwidget_layer = self.cardwidget_layer
        cardwidget.pos = (
            cardwidget_layer.right,
            cardwidget_layer.top - cardwidget_layer.height / 2, )

        self.cardwidget_dict[card_id] = cardwidget
        playerwidget = self.playerwidget_dict[player_id]
        magnet = self.wrap_in_magnet(cardwidget)
        cardwidget.bind(on_release=self.show_detail_of_a_card)
        playerwidget.ids.id_tefuda.add_widget(magnet)
        player.n_cards_in_deck -= 1
        player.tefuda.append(card_id)
        # logger.debug(params.drawer_id)
        # logger.debug(str(playerstate.pos))
        # logger.debug(str(playerstate.size))

    def on_command_move(self, params):
        unitinstance_from_id = params.unitinstance_from_id
        unitinstance_from = self.unitinstance_dict[unitinstance_from_id]
        unitinstance_widget_from = \
            self.unitinstance_widget_dict[unitinstance_from_id]
        cell_to = self.board.cell_dict[params.cell_to_id]
        unitinstance_from.n_turns_until_movable += 1
        magnet = unitinstance_widget_from.magnet
        cell_from = magnet.parent
        cell_from.remove_widget(magnet)
        cell_to.add_widget(magnet)
        self._command_recieving_trigger()

    def on_command_attack(self, params):
        attacker_id = params.attacker_id
        defender_id = params.defender_id
        dead_id = params.dead_id
        attacker = self.unitinstance_dict[attacker_id]
        defender = self.unitinstance_dict[defender_id]
        attacker_widget = self.unitinstance_widget_dict[attacker_id]
        defender_widget = self.unitinstance_widget_dict[defender_id]
        if self.uioptions.skip_attack_animation:
            if dead_id == '$both':
                attacker.attcack = 0
                attacker.power = 0
                defender.defense = 0
                defender.power = 0
                attacker_magnet = attacker_widget.magnet
                attacker_magnet.parent.remove_widget(attacker_magnet)
                attacker_widget.parent.remove_widget(attacker_widget)
                defender_magnet = defender_widget.magnet
                defender_magnet.parent.remove_widget(defender_magnet)
                defender_widget.parent.remove_widget(defender_widget)

    @staticmethod
    def create_unitinstance(*, player, prototype):
        return UnitInstance(**prototype.__dict__, )

    def on_command_use_unitcard(self, params):
        card_id = params.card_id
        cell_to_id = params.cell_to_id
        unitinstance = params.unitinstance
        player_id = unitinstance.player_id
        player = self.player_dict[player_id]
        cardwidget = self.cardwidget_dict[card_id]
        # UnitInstanceとUnitInstanceWidgetを生成
        unitinstance = UnitInstance(**params.unitinstance.__dict__)
        unitinstance_id = unitinstance.id
        unitinstance_widget = UnitInstanceWidget(
            unitinstance=unitinstance,
            id=unitinstance_id,
            imagefile=self.imagefile_dict[unitinstance.prototype_id],
            background_color=player.color)
        self.unitinstance_dict[unitinstance_id] = unitinstance
        self.unitinstance_widget_dict[unitinstance_id] = unitinstance_widget
        # CardWidgetをUnitInstanceWidgetに置き換える
        unitinstance_widget.pos = cardwidget.pos
        unitinstance_widget.size = cardwidget.size
        magnet = cardwidget.magnet
        magnet.remove_widget(cardwidget)
        magnet.add_widget(unitinstance_widget)
        del self.cardwidget_dict[card_id]
        del self.card_dict[card_id]
        # Touchした時に詳細が見れるようにする
        unitinstance_widget.bind(on_release=self.show_detail_of_a_instance)
        # 操作したのが自分なら単純な親の付け替え
        if self._player_id == player_id:
            magnet.parent.remove_widget(magnet)
            self.board.cell_dict[cell_to_id].add_widget(magnet)
            self._command_recieving_trigger()
        # 操作したのが自分でないならunitinstance_widgetを一旦中央に拡大表示
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

    # def on_operation_click(self, cell):
    #     logger.debug(r'on_operation_click :' + cell.id)
    #     if cell.is_not_empty():
    #         self.show_detail_of_a_card(cell)

    @doesnt_need_to_wait_for_the_animation_to_complete
    def show_detail_of_a_card(self, cardwidget):
        modalview = CustomModalView(
            attach_to=self,
            auto_dismiss=True,
            size_hint=(0.95, 0.6, ),
            pos_hint={'center_x': 0.5, 'center_y': 0.5, })
        if cardwidget.klass == 'UnitCardWidget':
            viewer = UnitPrototypeDetailViewer(
                prototype=cardwidget.prototype,
                widget=UnitCardWidget(
                    prototype=cardwidget.prototype,
                    imagefile=cardwidget.imagefile,
                    background_color=cardwidget.background_color),
                localize_str=self._localize_str,
                tag_translation_dict=self.tag_translation_dict,
                skill_dict=self.skill_dict)
        elif cardwidget.klass == 'SpellCardWidget':
            viewer = SpellPrototypeDetailViewer(
                prototype=cardwidget.prototype,
                widget=SpellCardWidget(
                    prototype=cardwidget.prototype,
                    imagefile=cardwidget.imagefile,
                    background_color=cardwidget.background_color),
                localize_str=self._localize_str,
                tag_translation_dict=self.tag_translation_dict,
                skill_dict=self.skill_dict)
        else:
            viewer = None
        modalview.add_widget(viewer)
        modalview.open(self)

    @doesnt_need_to_wait_for_the_animation_to_complete
    def show_detail_of_a_instance(self, unitinstance_widget):
        unitinstance = unitinstance_widget.unitinstance
        modalview = CustomModalView(
            attach_to=self,
            auto_dismiss=True,
            size_hint=(0.95, 0.6, ),
            pos_hint={'center_x': 0.5, 'center_y': 0.5, })
        viewer = UnitInstanceDetailViewer(
            unitinstance=unitinstance,
            prototype=self.prototype_dict[unitinstance.prototype_id],
            widget=UnitInstanceWidget(
                unitinstance=unitinstance,
                imagefile=unitinstance_widget.imagefile,
                background_color=unitinstance_widget.background_color),
            localize_str=self._localize_str,
            tag_translation_dict=self.tag_translation_dict,
            skill_dict=self.skill_dict)
        modalview.add_widget(viewer)
        modalview.open(self)
