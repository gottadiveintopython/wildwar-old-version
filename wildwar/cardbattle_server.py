# -*- coding: utf-8 -*-

__all__ = ('Server', 'RandomDeckCreater', )

import os.path
import random
import time
import itertools

import yaml

import setup_logging
from smartobject import SmartObject
logger = setup_logging.get_logger(__name__)


class TurnEnd(Exception):
    pass


class Player(SmartObject):

    def __init__(self, **kwargs):
        for key, value in {
            'klass': 'Player',
            'id': '',
            'color': (0, 0, 0, 0,),
            'max_cost': 0,
            'tefuda': [],
            'deck': [],
        }.items():
            kwargs.setdefault(key, value)
        super().__init__(**kwargs)

    def to_public(self):
        obj = self.so_copy()
        obj.so_update(n_tefuda=len(self.tefuda), n_cards_in_deck=len(self.deck))
        del obj.tefuda
        del obj.deck
        return obj

    def draw_card(self):
        if len(self.deck) == 0:
            return None
        else:
            card = self.deck.pop()
            self.tefuda.append(card)
            return card


class Board(SmartObject):

    def __init__(self, **kwargs):
        for key, value in {
            'klass': 'Board',
            'cells': [],
            'size': (0, 0, ),
        }.items():
            kwargs.setdefault(key, value)
        super().__init__(**kwargs)


def load_unit_prototype_from_file(filepath):
    with open(filepath, 'rt', encoding='utf-8') as reader:
        dictionary = yaml.load(reader)
    for prototype in dictionary.values():
        stats = prototype.pop('stats')
        prototype.update(power=stats[0], attack=stats[1], defense=stats[2])
        prototype.setdefault('skill_id_list', [])
        prototype.setdefault('tag_list', [])
    return {
        key: SmartObject(klass='UnitPrototype', id=key, **value)
        for key, value in dictionary.items()
    }


def load_spell_prototype_from_file(filepath):
    with open(filepath, 'rt', encoding='utf-8') as reader:
        dictionary = yaml.load(reader)
    return {
        key: SmartObject(klass='SpellPrototype', id=key, **value)
        for key, value in dictionary.items()
    }


class CardFactory:

    def __init__(self):
        self.n_created = 0
        self.dict = {}

    def create(self, *, prototype_id):
        card = SmartObject(
            klass='Card',
            id=r'{:04}'.format(self.n_created),
            prototype_id=prototype_id
        )
        self.n_created += 1
        self.dict[card.id] = card
        return card


class UnitInstanceFactory:

    def __init__(self, prototype_dict):
        self.prototype_dict = prototype_dict
        self.dict = {}
        self.n_created = 0

    def create(self, *, prototype_id, player_id):
        prototype = self.prototype_dict[prototype_id]
        kwargs = prototype.so_to_dict()
        kwargs.update(
            klass='UnitInstance',
            id=r'{}.{:04}'.format(prototype_id, self.n_created),
            prototype_id=prototype_id,
            player_id=player_id,
            n_turns_until_movable=1,
            o_power=kwargs['power'],
            o_attack=kwargs['attack'],
            o_defense=kwargs['defense'],
        )
        self.n_created += 1
        obj = SmartObject(**kwargs)
        self.dict[obj.id] = obj
        return obj


class RandomDeckCreater:

    def __init__(self, *, n_cards, unit_ratio=0.8):
        self.n_cards = n_cards
        self.unit_ratio = unit_ratio

    def __call__(
            self, *, player_id, card_factory,
            unit_prototype_dict, spell_prototype_dict):
        unit_prototype_id_list = list(unit_prototype_dict.keys())
        spell_prototype_id_list = list(spell_prototype_dict.keys())

        unit_ratio = self.unit_ratio
        deck = []
        for __ in range(self.n_cards):
            id_list = (
                unit_prototype_id_list if random.random() <= unit_ratio
                else spell_prototype_id_list)
            deck.append(card_factory.create(
                prototype_id=random.choice(id_list)))

        return deck


def func_judge_default(**kwargs):
    return SmartObject(is_settled=False)


def untrusted_json_to_smartobject(json_str):
    try:
        obj = SmartObject.load_from_json(json_str)
        if (
            obj.klass == 'Command' and
            isinstance(obj.type, str) and
            (obj.params is None or isinstance(obj.params, SmartObject)) and
            isinstance(obj.nth_turn, int)
        ):
            return obj
    except Exception as e:
        logger.debug('[S] Failed to decode json.')
        logger.debug(str(e))

    return None


class Server:

    # def __init__(
    #         self, *,
    #         senders, recievers,
    #         database_dir, board_size, timeout, how_to_decide_player_order,
    #         n_tefuda_init, max_tefuda,
    #         func_judge=None, func_create_deck):
    def __init__(
            self, *, senders, recievers, database_dir, board_size, timeout,
            how_to_decide_player_order, n_tefuda_init, max_tefuda,
            func_judge=None, func_create_deck):
        r'''引数解説

        senders
        recievers
        database_dir  # GameのDatabseであるunit_prototype.yamlがあるDirectory
        board_size  # (横のマス目の数, 縦のマス目の数, )
        timeout  # Turn毎の制限時間
        how_to_decide_player_order
        n_tefuda_init  # 手札の初期枚数
        max_tefuda  # 手札の上限枚数
        func_judge  # 勝敗判定を行うcallable
        func_create_deck  # 山札を作るcallable
        '''
        self.sender_list = list(senders)
        self.board_size = board_size
        self.timeout = timeout
        self.n_tefuda_init = n_tefuda_init
        self.max_tefuda = max_tefuda
        self.func_judge = (
            func_judge_default if func_judge is None else func_judge)

        # ----------------------------------------------------------------------
        # Prototype
        # ----------------------------------------------------------------------
        unit_prototype_dict = load_unit_prototype_from_file(
            os.path.join(database_dir, 'unit_prototype.yaml')
        )
        spell_prototype_dict = load_spell_prototype_from_file(
            os.path.join(database_dir, 'spell_prototype.yaml')
        )
        if set(unit_prototype_dict.keys()) & set(spell_prototype_dict.keys()):
            logger.critical('[S] unitとspellのidに被りがあります')
            return
        prototype_dict = {**unit_prototype_dict, **spell_prototype_dict, }
        self.unit_prototype_dict = unit_prototype_dict
        self.spell_prototype_dict = spell_prototype_dict
        self.prototype_dict = prototype_dict

        # ----------------------------------------------------------------------
        # Factory
        # ----------------------------------------------------------------------
        self.card_factory = card_factory = CardFactory()
        self.unit_instance_factory = UnitInstanceFactory(unit_prototype_dict)

        # ----------------------------------------------------------------------
        # Player
        # ----------------------------------------------------------------------
        self.reciever_list = reciever_list = list(recievers)
        if how_to_decide_player_order == 'iteration':
            pass
        elif how_to_decide_player_order == 'random':
            random.shuffle(reciever_list)
        else:
            raise ValueError('Unknown method to decide player order')
        player_colors = ((0.4, 0, 0, 1, ), (0, 0.2, 0, 1, ),)
        self.player_list = [
            Player(
                id=reciever.player_id,
                color=color,
                deck=func_create_deck(
                    player_id=reciever.player_id,
                    card_factory=card_factory,
                    unit_prototype_dict=unit_prototype_dict,
                    spell_prototype_dict=spell_prototype_dict))
            for reciever, color in zip(reciever_list, player_colors)
        ]
        self.player_dict = {player.id: player for player in self.player_list}

        # ----------------------------------------------------------------------
        # Board
        # ----------------------------------------------------------------------
        self.board = Board(
            all_cells=[None] * (board_size[0] * board_size[1]),
            size=board_size
        )

    def run(self):
        sender_list = self.sender_list
        for command in self.corerun():
            json_command = command.so_to_json(indent=2)
            logger.debug('[S] SERVER COMMAND')
            logger.debug(json_command)
            for sender in sender_list:
                if (
                        command.send_to == '$all' or
                        command.send_to == sender.player_id):
                    sender.send(json_command)

    def draw_card(self, player):
        card = player.draw_card()
        if card is not None:
            yield SmartObject(
                klass='Command',
                type='set_card_info',
                send_to=player.id,
                params=SmartObject(card=card)
            )
            yield SmartObject(
                klass='Command',
                type='draw',
                send_to='$all',
                params=SmartObject(drawer_id=player.id, card_id=card.id)
            )

    def corerun(self):
        prototype_dict = self.prototype_dict
        unit_prototype_dict = self.unit_prototype_dict
        spell_prototype_dict = self.spell_prototype_dict
        board_size = self.board_size
        player_list = self.player_list

        nth_turn = 0

        # ----------------------------------------------------------------------
        # Game開始の合図
        # ----------------------------------------------------------------------
        yield SmartObject(
            klass='Command',
            type='game_begin',
            send_to='$all',
            params=SmartObject(
                unit_prototype_dict=unit_prototype_dict,
                spell_prototype_dict=spell_prototype_dict,
                timeout=self.timeout,
                board_size=board_size,
                player_list=[player.to_public() for player in player_list],
            )
        )

        # ----------------------------------------------------------------------
        # 両Playerともに手札をn_tefuda_init枚引く
        # ----------------------------------------------------------------------
        for player in player_list:
            for i in range(self.n_tefuda_init):
                yield from self.draw_card(player)

        # ----------------------------------------------------------------------
        # 各PlayerのTurnを回すLoop
        # ----------------------------------------------------------------------

        # 通信の遅延や時計の精度を考慮して実際の制限時間は少し多めにする
        actual_timeout = self.timeout + 5

        CLIENT_COMMANDS = 'unit spell cell_to_cell resign turn_end'.split()

        # Main Loop
        for reciever in itertools.cycle(self.reciever_list):
            player = self.player_dict[reciever.player_id]
            nth_turn += 1
            yield SmartObject(
                klass='Command',
                type='turn_begin',
                send_to='$all',
                params=SmartObject(
                    nth_turn=nth_turn,
                    player_id=reciever.player_id)
            )
            yield from self.draw_card(player)
            time_limit = time.time() + actual_timeout
            # print('time_limit:', time_limit)
            try:
                while True:
                    current_time = time.time()
                    print(time_limit - current_time)
                    if current_time < time_limit:
                        command = untrusted_json_to_smartobject(
                            reciever.recieve(timeout=time_limit - current_time))
                        if command is None:
                            continue
                        if command.nth_turn != nth_turn:
                            logger.debug(
                                '[S] nth_turn unmatched. ({} != {})'.format(
                                    nth_turn, command.nth_turn))
                            logger.debug(str(command))
                            continue
                        # logger.debug(command)
                        if command.type not in CLIENT_COMMANDS:
                            logger.debug(
                                r"[S] Unknown command '{}'".format(command.type))
                            continue
                        else:
                            command_handler = getattr(
                                self, 'on_command_' + command.type)
                            command_handler(
                                nth_turn=nth_turn,
                                params=command.params)
                        # elif command.type == 'turn_end':
                        #     raise TurnEnd()
                        # elif command.type == 'resign':
                        #     self.resigned(reciever.player_id)
                        #     return
                        # else:
                        #     pass
                    else:
                        raise TimeoutError()

            except TimeoutError:
                yield SmartObject(
                    klass='Command',
                    type='notification',
                    send_to=reciever.player_id,
                    params=SmartObject(
                        message="Time's up.",
                        type='information'),
                )
            except TurnEnd:
                pass
            finally:
                yield SmartObject(
                    klass='Command',
                    type='turn_end',
                    send_to='$all',
                    params=SmartObject(nth_turn=nth_turn)
                )

    def on_command_turn_end(self, *, nth_turn, params):
        raise TurnEnd()
