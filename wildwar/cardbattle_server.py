# -*- coding: utf-8 -*-

__all__ = ('Server', 'RandomDeckCreater', )

import os.path
import random
import time
import itertools
import json

import yaml
from attrdict import AttrDict, AttrMap

import setup_logging
from slotsdict import SlotsDict
logger = setup_logging.get_logger(__name__)


class TurnEnd(Exception):
    pass


class GameEnd(Exception):
    def __init__(self, result, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.result = result


class Command(SlotsDict):
    __slotsdict__ = {
        'klass': 'Command',
        'type': None,
        'send_to': '$all',
        'params': None,
    }


class Player(SlotsDict):
    __slotsdict__ = {
        'klass': 'Player',
        'id': '$default_id',
        'index': None,
        'color': (0, 0, 0, 0,),
        'max_cost': 0,
        'cost': 0,
        'is_black': False,
        'tefuda': (),
        'deck': (),
        'honjin_prefix': '',  # 本陣(敵Unitに入られたら負けになる領域)のCellのidの接頭辞
        'first_row_prefix': '',  # 全ての自分のUnitが置ける領域のCellの接頭辞
        'second_row_prefix': '',  # 一部の特殊な自分のUnitが置ける領域のCellの接頭辞
    }

    def to_public(self):
        obj = dict(self)
        obj.update(n_tefuda=len(self.tefuda), n_cards_in_deck=len(self.deck))
        del obj['tefuda']
        del obj['deck']
        del obj['index']
        return obj

    def draw_card(self):
        if len(self.deck) == 0:
            return None
        else:
            card = self.deck.pop()
            self.tefuda.append(card)
            return card


class Cell(SlotsDict):
    __slotsdict__ = {
        'klass': 'Cell',
        'id': '$default_id',
        'index': None,
        'uniti': None,
    }

    def is_empty(self):
        return self.uniti is None

    def is_not_empty(self):
        return self.uniti is not None

    def attach(self, uniti):
        if self.is_empty():
            self.uniti = uniti
        else:
            logger.error("The cell '{}' already has a unit.".format(self.id))

    def detach(self):
        if self.is_empty():
            logger.error("The cell '{}' doesn't have unit.".format(self.id))
        else:
            previous_uniti = self.uniti
            self.uniti = None
            return previous_uniti


class Board(SlotsDict):
    __slotsdict__ = {
        'klass': 'Board',
        'size': (0, 0, ),
        'cell_list': None,
        'cell_dict': None,
        'center_row_prefix': '',
    }

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
            size=size,
            cell_list=cell_list, cell_dict=None,
            center_row_prefix=(None if rows % 2 == 0 else rows // 2 + 1))
        self.cell_dict = {cell.id: cell for cell in cell_list}

    def __str__(self):
        return '\n  '.join(
            ('Board:', *[
                '{}: {}'.format(cell.id, cell.uniti_id)
                for cell in self.cell_list]))


class UnitPrototype(SlotsDict):
    __slotsdict__ = {
        'klass': 'UnitPrototype',
        'id': '$default_id',
        'cost': 0,
        'attack': 0,
        'power': 0,
        'defense': 0,
        'skill_id_list': (),
        'tag_list': (),
    }


def _load_unitprototype_from_file(filepath):
    with open(filepath, 'rt', encoding='utf-8') as reader:
        dictionary = yaml.load(reader)
    for prototype in dictionary.values():
        stats = prototype.pop('stats')
        prototype.update(power=stats[0], attack=stats[1], defense=stats[2])
        prototype.setdefault('skill_id_list', [])
        prototype.setdefault('tag_list', [])
    return {
        key: UnitPrototype(klass='UnitPrototype', id=key, **value)
        for key, value in dictionary.items()
    }


class SpellPrototype(SlotsDict):
    __slotsdict__ = {
        'klass': 'SpellPrototype',
        'id': '$default_id',
        'cost': 0,
        'target': ''
    }


def _load_spellprototype_from_file(filepath):
    with open(filepath, 'rt', encoding='utf-8') as reader:
        dictionary = yaml.load(reader)
    return {
        key: SpellPrototype(klass='SpellPrototype', id=key, **value)
        for key, value in dictionary.items()
    }


class GameState(SlotsDict):
    __slotsdict__ = {
        'klass': 'GameState',
        'nth_turn': None,
        'current_player': None,
        'current_player_id': None,
    }


class Card(SlotsDict):
    __slotsdict__ = {
        'klass': 'Card',
        'id': '$default_id',
        'prototype_id': '$default_id',
    }


class CardFactory:

    def __init__(self):
        self.n_created = 0
        self.dict = {}

    def create(self, *, prototype_id):
        card = Card(
            klass='Card',
            id=r'{:04}'.format(self.n_created),
            prototype_id=prototype_id
        )
        self.n_created += 1
        self.dict[card.id] = card
        return card


class UnitInstance(SlotsDict):
    __slotsdict__ = {
        'klass': 'UnitInstance',
        'id': '$default_id',
        'cost': 0,
        'attack': 0,
        'power': 0,
        'defense': 0,
        'skill_id_list': (),
        'tag_list': (),
        'prototype_id': '$default_id',
        'player_id': '$default_id',
        'n_turns_until_movable': 0,
        'o_power': 0,
        'o_attack': 0,
        'o_defense': 0,
    }


class UnitInstanceFactory:

    def __init__(self, prototype_dict):
        self.prototype_dict = prototype_dict
        self.dict = {}
        self.n_created = 0

    def create(self, *, prototype_id, player_id):
        prototype = self.prototype_dict[prototype_id]
        obj = UnitInstance(
            prototype,
            klass='UnitInstance',
            id=r'{}.{:04}'.format(prototype_id, self.n_created),
            prototype_id=prototype_id,
            player_id=player_id,
            n_turns_until_movable=1,
            o_power=prototype.power,
            o_attack=prototype.attack,
            o_defense=prototype.defense)
        self.n_created += 1
        self.dict[obj.id] = obj
        return obj


class RandomDeckCreater:

    def __init__(self, *, n_cards, unit_ratio=0.8):
        self.n_cards = n_cards
        self.unit_ratio = unit_ratio

    def __call__(
            self, *, player_id, card_factory,
            unitp_dict, spellp_dict):
        unitp_id_list = list(unitp_dict.keys())
        spellp_id_list = list(spellp_dict.keys())

        unit_ratio = self.unit_ratio
        deck = []
        for __ in range(self.n_cards):
            id_list = (
                unitp_id_list if random.random() <= unit_ratio
                else spellp_id_list)
            deck.append(card_factory.create(
                prototype_id=random.choice(id_list)))

        return deck


def _func_judge_default(*, board, player_list, **kwargs):
    cols = board.size[0]
    black_info = {
        'goal': board.cell_list[:cols],  # 先手のgoalは後手の本陣
        'player_id': player_list[0].id,
        'is_reached': False, }  # goalに達したか否か
    white_info = {
        'goal': board.cell_list[-cols:],
        'player_id': player_list[1].id,
        'is_reached': False, }
    infos = (black_info, white_info, )
    for info in infos:
        for cell in info['goal']:
            if cell.is_not_empty():
                if cell.uniti.player_id == info['player_id']:
                    info['is_reached'] = True
                    break
    if black_info['is_reached']:
        if white_info['is_reached']:
            r = AttrDict(winner_id='$draw')
        else:
            r = AttrDict(winner_id=black_info['player_id'])
    else:
        if white_info['is_reached']:
            r = AttrDict(winner_id=white_info['player_id'])
        else:
            r = None
    return r


def _load_untrusted_json(json_str):
    try:
        obj = json.loads(json_str, parse_int=int, parse_constant=bool)
        if (
            obj['klass'] == 'Command' and
            isinstance(obj['type'], str) and
            (obj['params'] is None or isinstance(obj['params'], dict)) and
            isinstance(obj['nth_turn'], int)
        ):
            return AttrMap(obj)
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
        database_dir  # GameのDatabseであるunitp.yamlがあるDirectory
        board_size  # (横のマス目の数, 縦のマス目の数, )
        timeout  # Turn毎の制限時間
        how_to_decide_player_order
        n_tefuda_init  # 手札の初期枚数
        max_tefuda  # 手札の上限枚数
        func_judge  # 勝敗判定を行うcallable
        func_create_deck  # 山札を作るcallable
        '''
        self.viewer = viewer or AttrDict(
            klass='DummyViewer',
            player_id='$dummy',
            send=(lambda __: None))
        self.board_size = board_size
        self.timeout = timeout
        self.n_tefuda_init = n_tefuda_init
        self.max_tefuda = max_tefuda
        self.func_judge = (
            _func_judge_default if func_judge is None else func_judge)
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
        unitp_dict = _load_unitprototype_from_file(
            os.path.join(database_dir, 'unit_prototype.yaml')
        )
        # test用に適当にStatsを振る
        vlist = list(range(1, 4))
        for prototype in unitp_dict.values():
            prototype.update(
                cost=random.choice(vlist),
                power=random.choice(vlist),
                defense=random.choice(vlist),
                attack=random.choice(vlist),)
        #
        spellp_dict = _load_spellprototype_from_file(
            os.path.join(database_dir, 'spell_prototype.yaml')
        )
        if set(unitp_dict.keys()) & set(spellp_dict.keys()):
            logger.critical('[S] unitとspellのidに被りがあります')
            return
        prototype_dict = {**unitp_dict, **spellp_dict, }
        self.unitp_dict = unitp_dict
        self.spellp_dict = spellp_dict
        self.prototype_dict = prototype_dict

        # ----------------------------------------------------------------------
        # Factory
        # ----------------------------------------------------------------------
        self.card_factory = card_factory = CardFactory()
        self.uniti_factory = UnitInstanceFactory(unitp_dict)

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
        player_colors = ((0.4, 0, 0, 1, ), (0, 0.3, 0, 1, ), )
        player_indices = range(N_PLAYERS)
        self.player_list = player_list = [
            Player(
                id=communicator.player_id,
                index=index,
                color=color,
                tefuda=[],
                deck=func_create_deck(
                    player_id=communicator.player_id,
                    card_factory=card_factory,
                    unitp_dict=unitp_dict,
                    spellp_dict=spellp_dict))
            for communicator, color, index in zip(
                communicator_list, player_colors, player_indices)
        ]
        self.player_dict = {player.id: player for player in player_list}
        self.player_list[0].update(
            is_black=True,
            honjin_prefix='b',
            first_row_prefix=str(board_size[1] - 3),
            second_row_prefix=str(board_size[1] - 4))
        self.player_list[1].update(
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
            json_command = json.dumps(
                command, ensure_ascii=False, indent=2)
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
            yield Command(
                type='set_card_info',
                send_to=player.id,
                params={'card': card, })
            yield Command(
                type='draw',
                params={'drawer_id': player.id, 'card_id': card.id, })

    def corerun(self):
        unitp_dict = self.unitp_dict
        spellp_dict = self.spellp_dict
        board_size = self.board_size
        player_list = self.player_list
        gamestate = self.gamestate

        gamestate.nth_turn = 0

        # ----------------------------------------------------------------------
        # Game開始の合図
        # ----------------------------------------------------------------------
        yield Command(
            type='game_begin',
            params={
                'unitp_dict': unitp_dict,
                'spellp_dict': spellp_dict,
                'timeout': self.timeout,
                'board_size': board_size,
                'player_list': [player.to_public() for player in player_list], }
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

        # Main Loop
        try:
            for communicator in itertools.cycle(self.communicator_list):
                current_player = self.player_dict[communicator.player_id]
                gamestate.nth_turn += 1
                nth_turn = gamestate.nth_turn
                gamestate.current_player = current_player
                gamestate.current_player_id = current_player.id
                # Turn開始の前処理
                yield from self.reset_stats()
                yield from self.reduce_n_turns_until_movable_by(
                    n=1, target_id='$all')
                yield from self.increase_max_cost_by(
                    n=1, player=current_player)
                # Turn開始
                yield Command(
                    type='turn_begin',
                    params={
                        'nth_turn': nth_turn,
                        'player_id': current_player.id, }
                )
                yield from self.draw_card(current_player)
                time_limit = time.time() + actual_timeout
                try:
                    while True:
                        current_time = time.time()
                        if current_time < time_limit:
                            command = _load_untrusted_json(
                                communicator.recieve(timeout=time_limit - current_time))
                            if command is None:
                                continue
                            if command.nth_turn != nth_turn:
                                logger.debug(
                                    '[S] nth_turn unmatched. ({} != {})'.format(
                                        nth_turn, command.nth_turn))
                                logger.debug(str(command))
                                continue
                            command_handler = getattr(
                                self, 'on_command_' + command.type, None)
                            if command_handler is None:
                                logger.debug(
                                    r"[S] Unknown command '{}'".format(command.type))
                                continue
                            else:
                                yield from command_handler(params=command.params)
                                result = self.func_judge(
                                    board=self.board,
                                    player_list=self.player_list)
                                if result:
                                    raise GameEnd(result)
                        else:
                            raise TimeoutError()
                except TimeoutError:
                    yield self.create_notification("時間切れです", 'information')
                except TurnEnd:
                    pass
                finally:
                    yield Command(
                        type='turn_end', params={'nth_turn': nth_turn, })
        except GameEnd as e:
            yield Command(
                type='game_end',
                params={'winner_id': e.result.winner_id, })

    def reset_stats(self):
        for uniti in self.uniti_factory.dict.values():
            uniti.update(
                power=uniti.o_power,
                attack=uniti.o_attack,
                defense=uniti.o_defense)
        yield Command(type='reset_stats')

    def reduce_n_turns_until_movable_by(self, *, n, target_id):
        def internal(uniti):
            if uniti.n_turns_until_movable > n:
                uniti.n_turns_until_movable -= n
            else:
                uniti.n_turns_until_movable = 0
        if target_id == '$all':
            for uniti in self.uniti_factory.dict.values():
                internal(uniti)
        else:
            internal(self.uniti_factory.dict[target_id])
        yield Command(
            type='reduce_n_turns_until_movable_by',
            params={'n': n, 'target_id': target_id, })

    def set_max_cost(self, *, value, player):
        player.max_cost = value
        yield Command(
            type='set_max_cost',
            params={'value': value, 'player_id': player.id, })

    def increase_max_cost_by(self, *, n, player):
        yield from self.set_max_cost(
            value=player.max_cost + n,
            player=player)

    def _compute_current_cost(self):
        player_dict = self.player_dict
        cost_dict = {player_id: 0 for player_id in player_dict.keys()}
        for uniti in self.uniti_factory.dict.values():
            cost_dict[uniti.player_id] += uniti.cost
        for player_id, cost in cost_dict.items():
            player_dict[player_id].cost = cost

    def on_command_turn_end(self, *, params):
        raise TurnEnd()

    def create_notification(self, message, type, *, send_to=None):
        return Command(
            type='notification',
            send_to=(send_to or self.gamestate.current_player_id),
            params={'message': message, 'type': type, })

    def on_command_use_unitcard(self, *, params):
        r'''clientからuse_unitcardコマンドが送られて来た時に呼ばれるMethod

        paramsは外部からやってくるデータなので不正なデータが入っていないか厳重に確認
        しなければならない。
        '''
        print('[S] on_command_use_unitcard', params)

        # ----------------------------------------------------------------------
        # まずはCommandが有効なものか確認
        # ----------------------------------------------------------------------
        card_id = getattr(params, 'card_id', None)
        cell_to_id = getattr(params, 'cell_to_id', None)
        # paramsが必要な属性を持っているか確認
        if card_id is None or cell_to_id is None:
            logger.debug('[S] on_command_use_unitcard: params is broken')
            logger.debug(str(params))
            return
        #
        gamestate = self.gamestate
        current_player = gamestate.current_player
        card = self.card_factory.dict.get(card_id)
        # card_idの正当性を確認
        if card is None:
            logger.debug('[S] on_command_use_unitcard: Unknown card_id: ' + card_id)
            return
        # 自分の手札の物であるか確認
        if card not in current_player.tefuda:
            yield self.create_notification(
                'それはあなたのCardではありません', 'disallowed')
            return
        #
        prototype = self.unitp_dict.get(card.prototype_id)
        # UnitCardであるか確認
        if prototype is None:
            yield self.create_notification(
                'それはUnitCardではありません', 'disallowed')
            return
        # cost上限を越えないか確認
        if (prototype.cost + current_player.cost) > current_player.max_cost:
            yield self.create_notification(
                'costが足りません', 'disallowed')
            return
        #
        cell_to = self.board.cell_dict.get(cell_to_id)
        # cell_to_idの正当性を確認
        if cell_to is None:
            logger.debug('[S] on_command_use_unitcard: Unknown cell_id: ' + cell_to_id)
            yield self.create_notification(
                'そこへは置けません', 'disallowed')
            return
        # Unitを置こうとしているCellに既にUnitがいないか確認
        if cell_to.is_not_empty():
            yield self.create_notification(
                'そこには既にUnitが居ます', 'disallowed')
            return
        # Unitを置こうとしているCellが自陣であるか確認
        # if cell_to_id[0] != current_player.first_row_prefix:
        #     yield self.create_notification(
        #         'そこには置けません', 'disallowed')
        #     return

        # ----------------------------------------------------------------------
        # 有効なCommandである事が確認できたのでUnitを置く為の処理に入る
        # ----------------------------------------------------------------------

        # 手札の情報を持ち主以外にも送信
        yield Command(type='set_card_info', params={'card': card, })
        #
        current_player_id = gamestate.current_player_id
        uniti = self.uniti_factory.create(
            prototype_id=card.prototype_id,
            player_id=current_player_id)
        # UnitInstance設置Commandを全員に送信
        yield Command(
            type='use_unitcard',
            params={
                'uniti': uniti,
                'card_id': card_id,
                'cell_to_id': cell_to_id, })
        # 内部のDatabaseを更新
        cell_to.attach(uniti)
        current_player.tefuda.remove(card)
        self._compute_current_cost()

    def on_command_use_spellcard(self, *, params):
        print('[S] on_command_use_spellcard', params)
        yield self.create_notification(
            'Spellはまだ実装されていません', 'information')

    def on_command_cell_to_cell(self, *, params):
        r'''clientからcell_to_cellコマンドが送られて来た時に呼ばれるMethod'''
        print('[S] on_command_cell_to_cell', params)

        # ----------------------------------------------------------------------
        # Commandが有効なものか確認
        # ----------------------------------------------------------------------

        # paramsが必要な属性を持っているか確認
        cell_from_id = getattr(params, 'cell_from_id', None)
        cell_to_id = getattr(params, 'cell_to_id', None)
        if cell_from_id is None or cell_to_id is None:
            logger.debug('[S] on_command_cell_to_cell: params is broken')
            logger.debug(str(params))
            return

        # cell_from_id, cell_to_idの正当性を確認
        cell_from = self.board.cell_dict.get(cell_from_id)
        cell_to = self.board.cell_dict.get(cell_to_id)
        if cell_to is None or cell_from is None:
            logger.debug(
                '[S] on_command_cell_to_cell:\n'
                '    cell_from_id: {}\n'
                '    cell_to_id:  {}'.format(cell_from_id, cell_to_id))
            yield self.create_notification(
                '無効な操作です', 'disallowed')
            return

        # Drag元が空なら何もしない
        if cell_from.is_empty():
            return

        # Drag元にあるUnitが操作しているPlayerの物であるか確認
        gamestate = self.gamestate
        current_player = gamestate.current_player
        uniti_from = cell_from.uniti
        if uniti_from.player_id != current_player.id:
            yield self.create_notification(
                'それはあなたのUnitではありません', 'disallowed')
            return

        # Drag元のUnitが行動可能であるか確認
        if uniti_from.n_turns_until_movable > 0:
            yield self.create_notification(
                'そのUnitは行動不可能です', 'disallowed')
            return

        # Unitの移動可能範囲内か確認
        vector = _calculate_vector(
            cell_from=cell_from, cell_to=cell_to, cols=self.board_size[0])
        movement = _calculate_movement(vector)
        # print('vector:', vector, '    移動量:', movement)
        MAX_MOVEMENT = 1
        if movement > MAX_MOVEMENT:
            yield self.create_notification(
                'その場所へは動けません', 'disallowed')
            return

        # Drag先にUnitが居なければ「移動」
        if cell_to.is_empty():
            yield from self.do_command_move(cell_from=cell_from, cell_to=cell_to)
            return
        # 居る場合は「攻撃」もしくは「支援」
        else:
            uniti_to = cell_to.uniti
            # Drag先にあるUnitも操作しているPlayerの物なので「支援」
            if uniti_to.player_id == current_player.id:
                yield from self.do_command_support(cell_from=cell_from, cell_to=cell_to)
                return
            # Drag先にあるUnitが操作しているPlayerの物では無いので「攻撃」
            else:
                yield from self.do_command_attack(cell_from=cell_from, cell_to=cell_to)
                return

    def do_command_move(self, *, cell_from, cell_to):
        # 自軍の本陣へは動けない
        player = self.player_dict[cell_from.uniti.player_id]
        if player.honjin_prefix == cell_to.id[0]:
            yield self.create_notification(
                'その場所へは動けません', 'disallowed')
            return
        #
        uniti = cell_from.uniti
        yield Command(
            type='move',
            params={
                'uniti_from_id': uniti.id,
                'cell_to_id': cell_to.id, })
        uniti.n_turns_until_movable += 1
        cell_to.attach(cell_from.detach())

    def do_command_support(self, *, cell_from, cell_to):
        yield self.create_notification(
            "'支援'はまだ実装していません", 'information')

    def do_command_attack(self, *, cell_from, cell_to):
        a = cell_from.uniti
        d = cell_to.uniti
        a_id = a.id
        d_id = d.id
        uniti_dict = self.uniti_factory.dict
        a.power += a.attack
        a.attack = 0
        d.power += d.defense
        d.defense = 0
        a.power, d.power = a.power - d.power, d.power - a.power
        if a.power == d.power:
            cell_from.detach()
            cell_to.detach()
            del uniti_dict[a_id]
            del uniti_dict[d_id]
            yield Command(
                type='attack',
                params={
                    'attacker_id': a_id,
                    'defender_id': d_id,
                    'dead_id': '$both', })
        elif a.power < d.power:
            cell_from.detach()
            del uniti_dict[a_id]
            yield Command(
                type='attack',
                params={
                    'attacker_id': a_id,
                    'defender_id': d_id,
                    'dead_id': a_id, })
        else:
            cell_to.detach()
            cell_to.attach(cell_from.detach())
            del uniti_dict[d_id]
            a.n_turns_until_movable += 1
            yield Command(
                type='attack',
                params={
                    'attacker_id': a_id,
                    'defender_id': d_id,
                    'dead_id': d_id, })
        self._compute_current_cost()


def _calculate_vector(*, cell_from, cell_to, cols):
    r'''cell_fromからcell_toへの移動量を求める。

    戻り値はtuple(x軸の移動量, y軸の移動量, )で、単位はCellの個数、右がxの正方向、
    下がyの正方向になっている。'''
    index_from = cell_from.index
    index_to = cell_to.index
    pos_from = (index_from % cols, index_from // cols, )
    pos_to = (index_to % cols, index_to // cols, )
    return (pos_to[0] - pos_from[0], pos_to[1] - pos_from[1], )


def _calculate_movement(vector):
    r'''vectorから移動量の絶対値を求める'''
    return abs(vector[0]) + abs(vector[1])
