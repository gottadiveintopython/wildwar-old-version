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
            'index': None,
            'color': (0, 0, 0, 0,),
            'max_cost': 0,
            'is_black': False,
            'tefuda': [],
            'deck': [],
            'honjin_prefix': '',  # 本陣(敵Unitに入られたら負けになる領域)のCellのidの接頭辞
            'first_row_prefix': '',  # 全ての自分のUnitが置ける領域のCellの接頭辞
            'second_row_prefix': '',  # 一部の特殊な自分のUnitが置ける領域のCellの接頭辞
        }.items():
            kwargs.setdefault(key, value)
        super().__init__(**kwargs)

    def to_public(self):
        obj = self.so_copy()
        obj.so_update(n_tefuda=len(self.tefuda), n_cards_in_deck=len(self.deck))
        del obj.tefuda
        del obj.deck
        del obj.index
        return obj

    def draw_card(self):
        if len(self.deck) == 0:
            return None
        else:
            card = self.deck.pop()
            self.tefuda.append(card)
            return card


class Cell(SmartObject):

    def __init__(self, **kwargs):
        for key, value in {
            'klass': 'Cell',
            'id': None,
            'index': None,
            'unit_instance_id': None,
        }.items():
            kwargs.setdefault(key, value)
        super().__init__(**kwargs)

    def is_empty(self):
        return self.unit_instance_id is None

    def is_not_empty(self):
        return self.unit_instance_id is not None

    def attach(self, unit_instance_id):
        if self.is_empty():
            self.unit_instance_id = unit_instance_id
        else:
            logger.error("The cell '{}' already has a unit.".format(self.id))

    def detach(self):
        if self.is_empty():
            logger.error("The cell '{}' doesn't have unit.".format(self.id))
        else:
            previous_unit_instance_id = self.unit_instance_id
            self.unit_instance_id = None
            return previous_unit_instance_id


class Board(SmartObject):

    def __init__(self, *, size):
        cols, rows = size
        cell_list = (
            *(Cell(id='w' + str(i)) for i in range(cols)),
            *(Cell(id=(str(row_index) + str(col_index)))
                for row_index in range(rows - 2)
                for col_index in range(cols)),
            *(Cell(id='b' + str(i)) for i in range(cols))
        )
        for index, cell in enumerate(cell_list):
            cell.index = index
        super().__init__(
            klass='Board', size=size,
            cell_list=cell_list, cell_dict=None,
            center_row_prefix=(None if rows % 2 == 0 else rows // 2 + 1))
        self.cell_dict = {cell.id: cell for cell in cell_list}

    def __str__(self):
        return '\n  '.join(
            ('Board:', *[
                '{}: {}'.format(cell.id, cell.unit_instance_id)
                for cell in self.cell_list]))



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


class GameState(SmartObject):

    def __init__(self, **kwargs):
        for key, value in {
            'klass': 'GameState',
            'nth_turn': None,
            'current_player_id': None,
        }.items():
            kwargs.setdefault(key, value)
        super().__init__(**kwargs)


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
    #         communicators, viewer,
    #         database_dir, board_size, timeout, how_to_decide_player_order,
    #         n_tefuda_init, max_tefuda,
    #         func_judge=None, func_create_deck):
    def __init__(
            self, *, communicators, viewer=None, database_dir, board_size, timeout,
            how_to_decide_player_order, n_tefuda_init, max_tefuda,
            func_judge=None, func_create_deck):
        r'''引数解説

        communicators  # Playerと通信しあう窓口
        viewer  # 観戦者へ情報を送るだけの窓口
        database_dir  # GameのDatabseであるunit_prototype.yamlがあるDirectory
        board_size  # (横のマス目の数, 縦のマス目の数, )
        timeout  # Turn毎の制限時間
        how_to_decide_player_order
        n_tefuda_init  # 手札の初期枚数
        max_tefuda  # 手札の上限枚数
        func_judge  # 勝敗判定を行うcallable
        func_create_deck  # 山札を作るcallable
        '''
        self.viewer = viewer or SmartObject(
            klass='DummyViewer',
            player_id='$dummy',
            send=(lambda __: None))
        self.board_size = board_size
        self.timeout = timeout
        self.n_tefuda_init = n_tefuda_init
        self.max_tefuda = max_tefuda
        self.func_judge = (
            func_judge_default if func_judge is None else func_judge)
        self.gamestate = GameState()

        N_PLAYERS = 2

        # ----------------------------------------------------------------------
        # check arguments
        # ----------------------------------------------------------------------
        assert os.path.isdir(database_dir)
        assert 3 <= board_size[0] <= 9
        assert 7 <= board_size[1] <= 9
        assert timeout > 0
        assert how_to_decide_player_order in ('iteration', 'random', )
        assert n_tefuda_init >= 0
        assert max_tefuda >= 1

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
        self.communicator_list = communicator_list = list(communicators)
        assert len(communicator_list) == N_PLAYERS
        if how_to_decide_player_order == 'iteration':
            pass
        elif how_to_decide_player_order == 'random':
            random.shuffle(communicator_list)
        else:
            raise ValueError('Unknown method to decide player order')
        player_colors = ((0.4, 0, 0, 1, ), (0, 0.2, 0, 1, ), )
        player_indices = range(N_PLAYERS)
        self.player_list = player_list = [
            Player(
                id=communicator.player_id,
                index=index,
                color=color,
                deck=func_create_deck(
                    player_id=communicator.player_id,
                    card_factory=card_factory,
                    unit_prototype_dict=unit_prototype_dict,
                    spell_prototype_dict=spell_prototype_dict))
            for communicator, color, index in zip(
                communicator_list, player_colors, player_indices)
        ]
        self.player_dict = {player.id: player for player in player_list}
        self.player_list[0].so_overwrite(
            is_black=True,
            honjin_prefix='b',
            first_row_prefix=str(board_size[1] - 3),
            second_row_prefix=str(board_size[1] - 4))
        self.player_list[1].so_overwrite(
            is_black=False,
            honjin_prefix='w',
            first_row_prefix='0',
            second_row_prefix='1')

        # ----------------------------------------------------------------------
        # Board
        # ----------------------------------------------------------------------
        self.board = Board(size=board_size)
        # print(self.board)

    def run(self):
        communicator_list = (*self.communicator_list, self.viewer, )
        for command in self.corerun():
            json_command = command.so_to_json(indent=2)
            logger.debug('[S] SERVER COMMAND')
            logger.debug(json_command)
            for communicator in communicator_list:
                if (
                        command.send_to == '$all' or
                        command.send_to == communicator.player_id):
                    communicator.send(json_command)

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
        unit_prototype_dict = self.unit_prototype_dict
        spell_prototype_dict = self.spell_prototype_dict
        board_size = self.board_size
        player_list = self.player_list
        gamestate = self.gamestate

        gamestate.nth_turn = 0

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

        CLIENT_COMMANDS = 'put_unit use_spell cell_to_cell resign turn_end'.split()

        # Main Loop
        for communicator in itertools.cycle(self.communicator_list):
            current_player = self.player_dict[communicator.player_id]
            gamestate.nth_turn += 1
            nth_turn = gamestate.nth_turn
            gamestate.current_player_id = current_player.id
            yield SmartObject(
                klass='Command',
                type='turn_begin',
                send_to='$all',
                params=SmartObject(
                    nth_turn=nth_turn,
                    player_id=communicator.player_id)
            )
            yield from self.draw_card(current_player)
            time_limit = time.time() + actual_timeout
            # print('time_limit:', time_limit)
            try:
                while True:
                    current_time = time.time()
                    # print(time_limit - current_time)
                    if current_time < time_limit:
                        command = untrusted_json_to_smartobject(
                            communicator.recieve(timeout=time_limit - current_time))
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
                            r = command_handler(params=command.params)
                            if r is not None:
                                yield r
                        # elif command.type == 'turn_end':
                        #     raise TurnEnd()
                        # elif command.type == 'resign':
                        #     self.resigned(communicator.player_id)
                        #     return
                        # else:
                        #     pass
                    else:
                        raise TimeoutError()

            except TimeoutError:
                yield self.create_notification("時間切れです", 'information')
            except TurnEnd:
                pass
            finally:
                yield SmartObject(
                    klass='Command',
                    type='turn_end',
                    send_to='$all',
                    params=SmartObject(nth_turn=nth_turn)
                )

    def on_command_turn_end(self, *, params):
        raise TurnEnd()

    def create_notification(self, message, type, *, send_to=None):
        return SmartObject(
            klass='Command',
            type='notification',
            send_to=(send_to or self.gamestate.current_player_id),
            params=SmartObject(message=message, type=type)
        )

    def on_command_put_unit(self, *, params):
        r'''clientからput_unitコマンドが送られて来た時に呼ばれるMethod

        paramsは外部からやってくるデータなので不正なデータが入っていないか厳重に確認
        しなければならない。
        '''
        print('[S] on_command_put_unit', params)
        card_id = getattr(params, 'card_id', None)
        cell_to_id = getattr(params, 'cell_to_id', None)
        # paramsが必要な属性を持っているか確認
        if card_id is None or cell_to_id is None:
            logger.debug('[S] on_command_put_unit: params is broken')
            logger.debug(str(params))
            return
        #
        gamestate = self.gamestate
        current_player_id = gamestate.current_player_id
        current_player = self.player_dict[current_player_id]
        card = self.card_factory.dict.get(card_id)
        # card_idの正当性を確認
        if card is None:
            logger.debug('[S] on_command_put_unit: Unknown card_id: ' + card_id)
            return
        # 自分の手札の物であるか確認
        if card not in current_player.tefuda:
            return self.create_notification(
                'それはあなたのCardではありません', 'disallowed')
        # UnitCardであるか確認
        if card.prototype_id not in self.unit_prototype_dict:
            return self.create_notification(
                'それはUnitCardではありません', 'disallowed')
        #
        cell_to = self.board.cell_dict.get(cell_to_id)
        # cell_to_idの正当性を確認
        if cell_to is None:
            logger.debug('[S] on_command_put_unit: Unknown cell_id: ' + cell_to_id)
            return self.create_notification(
                'その場所へは置けません', 'disallowed')
        # Unitを置こうとしているCellに既にUnitがいないか確認
        if cell_to.is_not_empty():
            return self.create_notification(
                'その場所へは置けません', 'disallowed')
        # Unitを置こうとしているCellが自陣であるか確認
        if cell_to_id[0] != current_player.first_row_prefix:
            return self.create_notification(
                'その場所へは置けません', 'disallowed')
        # 有効な操作である事が確認できたのでUnitを置く



    def on_command_use_spell(self, *, params):
        print('[S] on_command_use_spell', params)

    def on_command_cell_to_cell(self, *, params):
        print('[S] on_command_cell_to_cell', params)
