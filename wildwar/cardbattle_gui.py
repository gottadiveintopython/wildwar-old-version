# -*- coding: utf-8 -*-

__all__ = ('CardBattleMain', )

import queue

import yaml

import kivy
kivy.require(r'1.10.0')
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.factory import Factory
from kivy.utils import get_color_from_hex
# from kivy.factory import Factory
from kivy.resources import resource_find
from kivy.properties import (
    ObjectProperty, NumericProperty, StringProperty, ListProperty,
    BooleanProperty
)
# from kivy.graphics import Color, Line
from kivy.animation import Animation

import setup_logging
logger = setup_logging.get_logger(__name__)
from smartobject import SmartObject
# from dragrecognizer import DragRecognizer
from magnetacrosslayout import MagnetAcrossLayout
from basicwidgets import fadeout_widget, AutoLabel
from tefudalayout import TefudaLayout
from notificater import Notificater


Builder.load_string(r"""
#:kivy 1.10.0

#:set OVERLAY_COLOR_DICT { r'normal': [0, 0, 0, 0], r'down': [1, 1, 1, 0.15], }

<UnknownCard>:
    canvas.before:
        Color:
            rgba: 0.3, 0.3, 0.3, 1
        RoundedRectangle
            size: self.width, self.height
            pos: 0, 0
        RoundedRectangle
            source: 'back_side.jpg'
            size: self.width - 4, self.height - 4
            pos: 2, 2

<SpellCard,UnitCard>:
    canvas.before:
        Color:
            rgba: 0.3, 0.3, 0.3, 1
        RoundedRectangle
            size: self.width, self.height
            pos: 0, 0
        Color:
            rgba: self.background_color
        RoundedRectangle
            size: self.width - 4, self.height - 4
            pos: 2, 2

<SpellCard>:
    Image:
        source: root.imagefile
    AutoLabel:
        pos_hint: {'x': 0, 'top': 1}
        size_hint: 0.2, 0.2
        bold: True
        text: str(root.spell_data.cost)

<UnitCard>:
    Image:
        source: root.imagefile
    AutoLabel:
        pos_hint: {'x': 0, 'top': 1}
        size_hint: 0.2, 0.2
        bold: True
        text: str(root.unit_data.cost)
    BoxLayout:
        size_hint: 1, 0.2
        AutoLabel:
            bold: True
            id: id_label_attack
            text: str(root.attack) if root.attack != 0 else ''
        AutoLabel:
            bold: True
            id: id_label_power
            text: str(root.power)
        AutoLabel:
            bold: True
            id: id_label_defense
            text: str(root.defense) if root.defense != 0 else ''

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

<CardBattlePlayer>:
    canvas.before:
        Color:
            rgba: .2, .2, .2, 1
        Line:
            rectangle: [*self.pos, *self.size]
    BoxLayout:
        orientation: 'horizontal'
        pos_hint: {'x': 0, 'y': 0}
        FloatLayout:
            size_hint_x: 0.8
            TefudaLayout:
                id: id_tefuda
                size_hint: 0.9, 0.9
                child_aspect_ratio: 0.7
                pos_hint: {'center_x': 0.5, 'center_y': 0.5}
        BoxLayout:
            size_hint_x: 0.2
            orientation: 'vertical'
            # id: id_status
            AutoLabel:
                size_hint_y: 1.7
                # bold: True
                text: root.id
            BoxLayout:
                Image:
                    source: 'icon_cost.png'
                AutoLabel:
                    id: id_label_cost
                    text: '{}/{}'.format(str(root.cost), str(root.max_cost))
            BoxLayout:
                Image:
                    source: 'icon_deck.png'
                AutoLabel:
                    id: id_label_deck
                    text: str(root.n_cards_in_deck)

<CardBattleBoardsParent@FloatLayout+StencilAll>:

<CardBattleMain>:
    card_layer: id_card_layer
    message_layer: id_message_layer
    notificater: id_notificater
    BoxLayout:
        orientation: 'vertical'
        Widget:
            id: id_playerwidget_enemy
            size_hint_y: 0.15
        CardBattleBoardsParent:
            id: id_boards_parent
            size_hint_y: 0.7
            size_hint_x: 0.8
        Widget:
            id: id_playerwidget_mine
            size_hint_y: 0.15
    Widget:
        id: id_card_layer
    FloatLayout:
        id: id_message_layer
        Notificater:
            id: id_notificater
            size_hint: 0.5, 0.3
            pos_hint: {'center_x': 0.5, 'center_y': 0.5, }
            default_font_size: 20
""")


def localize_str(s):
    r'''未実装

    国際化用のModuleを勉強した後に実装する'''
    return s


def copy_dictionary(dictionary, *, keys_exclude):
    return {
        key: value
        for key, value in dictionary.items() if key not in keys_exclude}


def replace_widget(old, new):
    r'''Widgetを入れ替える

    old.parentは非None、new.parentはNoneでなければならない
    '''
    assert old.parent is not None
    assert new.parent is None
    new.pos = old.pos
    new.pos_hint = old.pos_hint
    new.size = old.size
    new.size_hint = old.size_hint
    parent = old.parent
    index = parent.children.index(old)
    parent.remove_widget(old)
    parent.add_widget(new, index=index)


# def fadeout_widget(widget, *, duration=1, transition='in_cubic'):
#     def start_animation(dt):
#         def on_complete(animation, widget):
#             widget.parent.remove_widget(widget)
#         animation = Animation(
#             duration=duration,
#             transition=transition,
#             opacity=0)
#         animation.bind(on_complete=on_complete)
#         animation.start(widget)
#     Clock.schedule_once(start_animation, 0)


def bring_widget_to_front(widget):
    parent = widget.parent
    parent.remove_widget(widget)
    parent.add_widget(widget)


class GameState(Factory.EventDispatcher):
    nth_turn = NumericProperty()
    is_myturn = BooleanProperty()


class Player(Factory.EventDispatcher):
    id = StringProperty()
    cost = NumericProperty()
    max_cost = NumericProperty()
    n_cards_in_deck = NumericProperty()
    tefuda = ListProperty()
    color = ListProperty()


class UnknownCard(Factory.RelativeLayout):
    pass


class UnitCard(Factory.RelativeLayout):

    unit_data = ObjectProperty()
    imagefile = StringProperty()
    background_color = ListProperty((0, 0, 0, 0, ))
    power = NumericProperty()
    attack = NumericProperty()
    defense = NumericProperty()

    def __init__(self, *, unit_data, **kwargs):
        super().__init__(unit_data=unit_data, **kwargs)
        self.power = unit_data.power
        self.attack = unit_data.attack
        self.defense = unit_data.defense


for _name in r'id name skills tags cost'.split():
    setattr(UnitCard, _name, property(
        lambda self, _name=_name: getattr(self.unit_data, _name)
    ))


class SpellCard(Factory.RelativeLayout):

    spell_data = ObjectProperty()
    imagefile = StringProperty()
    background_color = ListProperty((0, 0, 0, 0, ))


for _name in r'id name cost description'.split():
    setattr(SpellCard, _name, property(
        lambda self, _name=_name: getattr(self.spell_data, _name)
    ))


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
            cell = Cell(id='enemy{}'.format(i))
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


class CardBattlePlayer(Factory.FloatLayout):
    id = StringProperty()
    cost = NumericProperty()
    max_cost = NumericProperty()
    n_cards_in_deck = NumericProperty()
    color = ListProperty()

    unused_property_names = ('tefuda', )

    def __init__(self, *, player, **kwargs):
        super().__init__(
            id=player.id,
            cost=player.cost,
            max_cost=player.max_cost,
            n_cards_in_deck=player.n_cards_in_deck,
            color=player.color,
            **kwargs)
        player.bind(
            id=self.setter('id'),
            cost=self.on_cost_changed,
            max_cost=self.on_cost_changed,
            n_cards_in_deck=self.on_n_deck_changed,
            color=self.setter('color'))

    def on_cost_changed(self, player, value):
        label = self.ids.id_label_cost
        self.cost = player.cost
        self.max_cost = player.max_cost
        animation = getattr(self, '_cost_animation', None)
        # costが最大値を上回っていないなら白色で非点滅
        if player.cost <= player.max_cost:
            if animation is not None:
                label.color = get_color_from_hex('#ffffff')
                animation.stop(label)
                self._cost_animation = None
        # costが最大値を上回っているなら赤色で点滅
        elif animation is None:
            label.color = get_color_from_hex('#ff2222')
            animation = Animation(
                opacity=0,
                duration=0.8,
                transition='in_cubic') + Animation(
                    opacity=1,
                    duration=0.8,
                    transition='out_cubic')
            animation.repeat = True
            animation.start(label)
            self._cost_animation = animation

    def on_n_deck_changed(self, player, value):
        label = self.ids.id_label_deck

        def on_fadeout_complete(animation, widget):
            self.n_cards_in_deck = value
            animation_fadein = Animation(
                opacity=1,
                duration=0.1,
                transition='linear')
            animation_fadein.start(label)

        animation_fadeout = Animation(
            opacity=0,
            duration=0.1,
            transition=r'linear')
        animation_fadeout.bind(on_complete=on_fadeout_complete)
        animation_fadeout.start(label)


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
    message_layer = ObjectProperty()
    notificater = ObjectProperty()

    def __init__(self, *, player_id, inqueue=None, outqueue=None, **kwargs):
        super().__init__(**kwargs)
        self.inqueue = queue.Queue() if inqueue is None else inqueue
        self.outqueue = queue.Queue() if outqueue is None else outqueue
        self.player_id = player_id
        self.gamestate = GameState(
            nth_turn=0, is_myturn=False)

    def create_reciever(self):
        return QueueReciever(
            player_id=self.player_id,
            queue_instance=self.outqueue)

    def create_sender(self):
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

    def on_command_game_begin(self, params):
        self.prototype_dict = params.prototype_dict.__dict__.copy()
        with open(
                resource_find('imagefile_dict.yaml'),
                'rt', encoding='utf-8') as reader:
            self.imagefile_dict = yaml.load(reader)
        self.player_list = [
            Player(**copy_dictionary(
                player.__dict__,
                keys_exclude=('n_tefuda', 'klass', )
            )) for player in params.player_list]
        self.is_black = self.player_list[0].id == self.player_id  # 先手か否か
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
                    else 'id_playerwidget_enemy'
                ],
                new=playerwidget)
        self.card_dict = {}
        self.board = BoardWidget(
            cols=params.board_size[0],
            rows=params.board_size[1] + 2,
            size_hint=(1, 1.25, ),
            pos_hint={'center_y': 0.5, 'center_x': 0.5}
        )
        self.ids.id_boards_parent.add_widget(self.board)

    def on_command_turn_begin(self, params):
        is_myturn = params.player_id == self.player_id
        self.gamestate.is_myturn = is_myturn
        label = AutoLabel(
            text=(
                localize_str('あなたの番') if is_myturn
                else localize_str('相手の番')),
            color=(0, 0, 0, 1),
            outline_color=(1, 1, 1, ),
            outline_width=3,
        )
        self.message_layer.add_widget(label)
        fadeout_widget(label)

    def on_command_turn_end(self, params):
        self.gamestate.is_myturn = False

    def on_command_notification(self, params):
        self.notificater.add_notification(
            text=params.message,
            icon_key=params.type,
            duration=4)

    def on_command_draw(self, params):
        r'''drawは「描く」ではなく「(カードを)引く」の意'''
        card_layer = self.card_layer
        card_pos = card_layer.to_widget(
            *card_layer.to_window(
                card_layer.right,
                card_layer.top - card_layer.height / 2))
        if params.drawer_id == self.player_id:
            prototype_id = self.card_dict[params.card_id].prototype_id
            prototype = self.prototype_dict[prototype_id]
            # print(prototype)
            if prototype.klass == 'UnitPrototype':
                card = UnitCard(
                    unit_data=self.prototype_dict[prototype_id],
                    background_color=self.player_dict[self.player_id].color,
                    imagefile=self.imagefile_dict[prototype_id],
                    pos=card_pos)
            elif prototype.klass == 'SpellPrototype':
                card = SpellCard(
                    spell_data=self.prototype_dict[prototype_id],
                    background_color=self.player_dict[self.player_id].color,
                    imagefile=self.imagefile_dict[prototype_id],
                    pos=card_pos)
        else:
            card = UnknownCard(pos=card_pos)
        playerwidget = self.playerwidget_dict[params.drawer_id]
        playerwidget.ids.id_tefuda.add_widget(
            self.wrap_in_magnet(card))
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


# class GamePlayer(DragRecognizer, CardBattleMain):

#     def on_drag_start(self, touch):
#         cell_from = None
#         for cell in self.board.children:
#             if cell.collide_point(*touch.opos):
#                 cell_from = cell
#                 cell_from.state = r'down'

#         inst_list = [
#             Color([1, 1, 1, 1]),
#             Line(
#                 points=[touch.ox, touch.oy, touch.ox, touch.oy, ],
#                 dash_length=4,
#                 dash_offset=8
#             )
#         ]
#         for inst in inst_list:
#             self.canvas.after.add(inst)
#         ud_key = self._get_uid(prefix=r'CardBattleMain')  # _get_uidは親ClassのMethod
#         touch.ud[ud_key] = {
#             r'inst_list': inst_list,
#             r'cell_from': cell_from,
#             r'cell_to': cell_from,
#         }

#     def on_being_dragged(self, touch):
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

#         line = ud[r'inst_list'][1]
#         points = line.points
#         points[2] += touch.dx
#         points[3] += touch.dy
#         line.points = points

#     def on_drag_finish(self, touch):
#         ud_key = self._get_uid(prefix=r'CardBattleMain')
#         ud = touch.ud[ud_key]

#         cell_from = ud[r'cell_from']
#         cell_to = ud[r'cell_to']

#         if cell_from is not None:
#             cell_from.state = r'normal'
#         if cell_to is not None:
#             cell_to.state = r'normal'

#         inst_list = ud[r'inst_list']
#         for inst in inst_list:
#             self.canvas.after.remove(inst)

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

