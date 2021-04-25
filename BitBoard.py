"""
!!!
!!!
NEED TO DISABLE OPPONENT'S ABILITY TO CASTLE IF WE TAKE THEIR ROOK!!! - Done
Check that en passant captured piece identification works - do we need to do index +/- 8?
!!!
!!!
DOUBLE-CHECK MOVEMENT MASK DEALY WITH OFFSET BIT FOR CURRENT POSITION!!!
NEED TO FIX PAWN PROMOTION TO NOT MAKE CHECK TEST PASS (OR FAIL?) WITH KING IN FRONT OF PAWN ON 7TH RANK
NEED TO TEST THE URDL AND ULDR MASKS TO EXCLUDE CURRENT SQUARE!!!
To do - handle pawn promotion
NEED TO MAKE SURE EN PASSANT IS HANDLED CORRECTLY - LOOK AT REAL FEN STRINGS LIKE THIS -- rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1 -- after 1 e4
Evalute function
Search function
"""

from Move import Move
from bcolors import bcolors
from math import log2, inf
import logging
import configparser
from datetime import datetime
config = configparser.ConfigParser()
config.read('config.ini')
logging.basicConfig(level=logging.CRITICAL,
                    format='%(asctime)s.%(msecs)03d - %(levelname)8s - %(filename)s - Function: %(funcName)20s - Line: %(lineno)4s // %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    handlers=[
                        # logging.FileHandler(filename='log.txt'),
                        logging.StreamHandler(),
                        # MariaDBHandler(username=config['log']['log_db_user'], password=config['log']['log_db_password'], host=config['log']['log_db_host'])
                    ])
log = logging.getLogger(__name__)

all_move_history = {}
all_move_details = {'Moves': 0, 'Captures': 0, 'En Passant': 0, 'Castles': 0, 'Promotions': 0}


class BitBoardChess:

    SIXTY_FOUR_BIT_MASK = 0b1111111111111111111111111111111111111111111111111111111111111111
    KNIGHT_SPAN = 0b0000000000000000000000000000101000010001000000000001000100001010
    KNIGHT_SQUARE = 45
    KING_SPAN = 0b1110000010100000111000000000000000000000000000000000000000000000
    KING_SQUARE = 9

    RANK_8 = 0b1111111100000000000000000000000000000000000000000000000000000000
    RANK_7 = 0b0000000011111111000000000000000000000000000000000000000000000000
    RANK_6 = 0b0000000000000000111111110000000000000000000000000000000000000000
    RANK_5 = 0b0000000000000000000000001111111100000000000000000000000000000000
    RANK_4 = 0b0000000000000000000000000000000011111111000000000000000000000000
    RANK_3 = 0b0000000000000000000000000000000000000000111111110000000000000000
    RANK_2 = 0b0000000000000000000000000000000000000000000000001111111100000000
    RANK_1 = 0b0000000000000000000000000000000000000000000000000000000011111111

    FILE_A = 0b1000000010000000100000001000000010000000100000001000000010000000
    FILE_B = 0b0100000001000000010000000100000001000000010000000100000001000000
    FILE_C = 0b0010000000100000001000000010000000100000001000000010000000100000
    FILE_D = 0b0001000000010000000100000001000000010000000100000001000000010000
    FILE_E = 0b0000100000001000000010000000100000001000000010000000100000001000
    FILE_F = 0b0000010000000100000001000000010000000100000001000000010000000100
    FILE_G = 0b0000001000000010000000100000001000000010000000100000001000000010
    FILE_H = 0b0000000100000001000000010000000100000001000000010000000100000001
    FILE_AB = 0b1100000011000000110000001100000011000000110000001100000011000000
    FILE_GH = 0b0000001100000011000000110000001100000011000000110000001100000011

    BLACK = 0
    WHITE = 1

    WHITE_KING_SIDE_CASTLE_FLAG = 8
    WHITE_QUEEN_SIDE_CASTLE_FLAG = 4
    BLACK_KING_SIDE_CASTLE_FLAG = 2
    BLACK_QUEEN_SIDE_CASTLE_FLAG = 1

    BLACK_PIECE_ATTRIBUTES = ['BLACK_PAWNS', 'BLACK_KNIGHTS', 'BLACK_BISHOPS', 'BLACK_ROOKS', 'BLACK_QUEENS', 'BLACK_KINGS']
    WHITE_PIECE_ATTRIBUTES = ['WHITE_PAWNS', 'WHITE_KNIGHTS', 'WHITE_BISHOPS', 'WHITE_ROOKS', 'WHITE_QUEENS', 'WHITE_KINGS']

    SAVE_ORDER = ['BLACK_PAWNS', 'BLACK_KNIGHTS', 'BLACK_BISHOPS', 'BLACK_ROOKS', 'BLACK_QUEENS', 'BLACK_KINGS',
                  'WHITE_PAWNS', 'WHITE_KNIGHTS', 'WHITE_BISHOPS', 'WHITE_ROOKS', 'WHITE_QUEENS', 'WHITE_KINGS',
                  'EN_PASSANT', 'CASTLING', 'FULL_MOVES', 'HALF_MOVES', 'PLAYER_TURN']

    def __init__(self) -> None:
        self.RANK_MASKS = [0] * 8
        self.FILE_MASKS = [0] * 8
        self.HV_MASKS = [0] * 64
        self.ULDR_DIAGONAL_MASKS = [0] * 64
        self.URDL_DIAGONAL_MASKS = [0] * 64
        self.CASTLING = 0b1111
        self.FULL_MOVES = 0
        self.HALF_MOVES = 0
        self.GAME_STACK = []
        self.PLAYER_TURN = BitBoardChess.WHITE
        self.EN_PASSANT = 0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00000000

        self.KNIGHT_MOVE_MASKS = [0] * 64
        self.BISHOP_MOVE_MASKS = [0] * 64
        self.ROOK_MOVE_MASKS = [0] * 64
        self.QUEEN_MOVE_MASKS = [0] * 64
        self.KING_MOVE_MASKS = [0] * 64

        self.move_history = []

        self.clear()
        self.setup_horizontal_and_vertical_masks()
        self.setup_uldr_diagonal_and_urdl_diagonal_masks()
        self.setup_piece_masks()
        self.reset()

        self.MOVE_CACHE = {}
        self.LEGAL_MOVE_CACHE = {}

    def reset(self) -> None:
        self.WHITE_PAWNS = 0b00000000_00000000_00000000_00000000_00000000_00000000_11111111_00000000
        self.WHITE_ROOKS = 0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_10000001
        self.WHITE_KNIGHTS = 0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_01000010
        self.WHITE_BISHOPS = 0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00100100
        self.WHITE_QUEENS = 0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00010000
        self.WHITE_KINGS = 0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00001000

        self.BLACK_PAWNS = 0b00000000_11111111_00000000_00000000_00000000_00000000_00000000_00000000
        self.BLACK_ROOKS = 0b10000001_00000000_00000000_00000000_00000000_00000000_00000000_00000000
        self.BLACK_KNIGHTS = 0b01000010_00000000_00000000_00000000_00000000_00000000_00000000_00000000
        self.BLACK_BISHOPS = 0b00100100_00000000_00000000_00000000_00000000_00000000_00000000_00000000
        self.BLACK_QUEENS = 0b00010000_00000000_00000000_00000000_00000000_00000000_00000000_00000000
        self.BLACK_KINGS = 0b00001000_00000000_00000000_00000000_00000000_00000000_00000000_00000000

        self.EN_PASSANT = 0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00000000

        self.CASTLING = 0b1111

        self.FULL_MOVES = 0
        self.HALF_MOVES = 0

        self.GAME_STACK.clear()
        self.move_history.clear()

        self.PLAYER_TURN = BitBoardChess.WHITE

    def clear(self) -> None:
        self.reset()
        self.WHITE_PAWNS = 0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00000000
        self.WHITE_ROOKS = 0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00000000
        self.WHITE_KNIGHTS = 0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00000000
        self.WHITE_BISHOPS = 0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00000000
        self.WHITE_QUEENS = 0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00000000
        self.WHITE_KINGS = 0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00000000

        self.BLACK_PAWNS = 0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00000000
        self.BLACK_ROOKS = 0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00000000
        self.BLACK_KNIGHTS = 0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00000000
        self.BLACK_BISHOPS = 0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00000000
        self.BLACK_QUEENS = 0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00000000
        self.BLACK_KINGS = 0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00000000

    def load_from_fen_string(self, fen_string: str) -> None:
        keys = fen_string.split(' ')
        board_string, player_turn, castling, en_passant, half_moves, full_moves = '', 'w', '-', '-', 0, 0
        board_string = keys[0]
        if len(keys) >= 2:
            player_turn = keys[1]
        if len(keys) >= 3:
            castling = keys[2]
        if len(keys) >= 4:
            en_passant = keys[3]
        if len(keys) >= 5:
            half_moves = int(keys[4])
        if len(keys) >= 6:
            full_moves = int(keys[5])
        log.info(f'Processing: {board_string}, {player_turn}, {castling}, {en_passant}, {half_moves}, {full_moves}')

        def process_board_layout(board_string):
            log.debug(f'Loading FEN string {board_string}...')
            position = BitBoardChess.convert_position_to_mask(0)
            self.clear()
            for char in board_string:
                log.debug(f'Processing {char}...')
                if char.isdigit():
                    position = position >> int(char)
                    log.debug(f'Skipping {int(char)} spaces...')
                elif char.isalpha():
                    if char == 'K':
                        log.debug(f'Adding a WHITE KING to {int(log2(position))}...')
                        self.WHITE_KINGS |= position
                    elif char == 'k':
                        log.debug(f'Adding a BLACK KING to {int(log2(position))}...')
                        self.BLACK_KINGS |= position
                    if char == 'Q':
                        log.debug(f'Adding a WHITE QUEEN to {int(log2(position))}...')
                        self.WHITE_QUEENS |= position
                    elif char == 'q':
                        log.debug(f'Adding a BLACK QUEEN to {int(log2(position))}...')
                        self.BLACK_QUEENS |= position
                    if char == 'R':
                        log.debug(f'Adding a WHITE ROOK to {int(log2(position))}...')
                        self.WHITE_ROOKS |= position
                    elif char == 'r':
                        log.debug(f'Adding a BLACK ROOK to {int(log2(position))}...')
                        self.BLACK_ROOKS |= position
                    if char == 'B':
                        log.debug(f'Adding a WHITE BISHOP to {int(log2(position))}...')
                        self.WHITE_BISHOPS |= position
                    elif char == 'b':
                        log.debug(f'Adding a BLACK BISHOP to {int(log2(position))}...')
                        self.BLACK_BISHOPS |= position
                    if char == 'N':
                        log.debug(f'Adding a WHITE KNIGHT to {int(log2(position))}...')
                        self.WHITE_KNIGHTS |= position
                    elif char == 'n':
                        log.debug(f'Adding a BLACK KNIGHT to {int(log2(position))}...')
                        self.BLACK_KNIGHTS |= position
                    if char == 'P':
                        log.debug(f'Adding a WHITE PAWN to {int(log2(position))}...')
                        self.WHITE_PAWNS |= position
                    elif char == 'p':
                        log.debug(f'Adding a BLACK PAWN to {int(log2(position))}...')
                        self.BLACK_PAWNS |= position
                    elif char == '/':
                        continue

                    if char != '/':
                        position = position >> 1

        def process_castling(castling: str) -> None:
            self.CASTLING = 0
            if 'K' in castling:
                self.CASTLING = self.CASTLING | BitBoardChess.WHITE_KING_SIDE_CASTLE_FLAG
            if 'Q' in castling:
                self.CASTLING = self.CASTLING | BitBoardChess.WHITE_QUEEN_SIDE_CASTLE_FLAG
            if 'k' in castling:
                self.CASTLING = self.CASTLING | BitBoardChess.BLACK_KING_SIDE_CASTLE_FLAG
            if 'q' in castling:
                self.CASTLING = self.CASTLING | BitBoardChess.BLACK_QUEEN_SIDE_CASTLE_FLAG

            log.info(f'Setting castling of {castling} to: {self.CASTLING:4b}')

        def process_en_passant(en_passant: str) -> None:
            self.EN_PASSANT = 0
            if len(en_passant) == 2:
                en_passant_board_position = BitBoardChess.convert_algebraic_notation_to_position(en_passant)
                self.EN_PASSANT = BitBoardChess.convert_position_to_mask(en_passant_board_position)
                log.info(f'En Passant loaded: {en_passant_board_position}.')

        self.clear()
        process_board_layout(board_string=board_string)
        process_castling(castling=castling)
        process_en_passant(en_passant=en_passant)
        if player_turn.lower() not in ['w', 'b']:
            raise Exception('Invalid player turn in fen string.')
        self.PLAYER_TURN = BitBoardChess.WHITE if player_turn.lower() == 'w' else BitBoardChess.BLACK
        self.HALF_MOVES = half_moves
        self.FULL_MOVES = full_moves

        log.info(f'BLACK PIECES: {self.BLACK_PIECES:064b}')
        log.info(f'WHITE PIECES: {self.WHITE_PIECES:064b}')

    def print_board(self) -> None:
        print('-' * 41)
        for board_position in range(64):
            print('| ' + self.get_piece_label(board_position) + ' ', end='')
            if (board_position + 1) % 8 == 0:
                print(f'| {8 - ((board_position // 8))}')
                print('-' * 41)
        print('- A -- B -- C -- D -- E -- F -- G -- H -')
        print()
        # print(self.fen_key)
        print()

    def get_piece_label(self, position: int) -> str:
        """
        """
        position_mask = BitBoardChess.convert_position_to_mask(position)
        # Determine color
        if self.BLACK_PIECES & position_mask:
            piece_label = bcolors.CBEIGE2 + 'B'
        elif self.WHITE_PIECES & position_mask:
            piece_label = 'W'
        else:
            return '  '

        if (self.BLACK_PAWNS | self.WHITE_PAWNS) & position_mask:
            piece_label += 'P'
        elif (self.BLACK_KNIGHTS | self.WHITE_KNIGHTS) & position_mask:
            piece_label += 'N'
        elif (self.BLACK_BISHOPS | self.WHITE_BISHOPS) & position_mask:
            piece_label += 'B'
        elif (self.BLACK_ROOKS | self.WHITE_ROOKS) & position_mask:
            piece_label += 'R'
        elif (self.BLACK_QUEENS | self.WHITE_QUEENS) & position_mask:
            piece_label += 'Q'
        elif (self.BLACK_KINGS | self.WHITE_KINGS) & position_mask:
            piece_label += 'K'

        if self.BLACK_PIECES & position_mask:
            piece_label += bcolors.ENDC
        return piece_label

    def setup_horizontal_and_vertical_masks(self) -> None:
        log.debug('Generating horizontal and vertical masks...')
        rank_base_mask = 0b11111111
        for rank in range(8):
            self.RANK_MASKS[rank] = (0 | (rank_base_mask << (rank * 8))) & BitBoardChess.SIXTY_FOUR_BIT_MASK

        file_base_mask = 0b1000000010000000100000001000000010000000100000001000000010000000
        for file in range(8):
            self.FILE_MASKS[file] = (file_base_mask >> file) & BitBoardChess.SIXTY_FOUR_BIT_MASK

        for square in range(64):
            rank = 7 - (square // 8)
            file = square % 8
            mask_value = (self.RANK_MASKS[rank] | self.FILE_MASKS[file]) & ~(1 << (63 - square))
            self.HV_MASKS[square] = mask_value
        log.debug('Generating horizontal and vertical masks... Done.')

    def setup_uldr_diagonal_and_urdl_diagonal_masks(self) -> None:
        log.debug('Generating diagonal masks...')
        urdl_base_mask = 0b00000001_00000010_00000100_00001000_00010000_00100000_01000000_10000000
        uldr_base_mask = 0b10000000_01000000_00100000_00010000_00001000_00000100_00000010_00000001
        for square in range(64):
            shift = (square % 8) - (square // 8)
            if shift >= 0:
                uldr_diagonal_mask = (uldr_base_mask << (abs(shift) * 8)) & BitBoardChess.SIXTY_FOUR_BIT_MASK
            else:
                uldr_diagonal_mask = (uldr_base_mask >> (abs(shift) * 8)) & BitBoardChess.SIXTY_FOUR_BIT_MASK
            self.ULDR_DIAGONAL_MASKS[square] = uldr_diagonal_mask & ~(1 << (63 - square))
            # print(square)
            # BitBoardChess.print_bitboard(self.ULDR_DIAGONAL_MASKS[square])

            shift = (square % 8) - (square // 8)
            if shift >= 0:
                urdl_diagonal_mask = (urdl_base_mask << (abs(shift) * 8)) & BitBoardChess.SIXTY_FOUR_BIT_MASK
            else:
                urdl_diagonal_mask = (urdl_base_mask >> (abs(shift) * 8)) & BitBoardChess.SIXTY_FOUR_BIT_MASK
            new_index = (((square // 8) + 1) * 8 - square % 8) - 1
            self.URDL_DIAGONAL_MASKS[new_index] = urdl_diagonal_mask & ~(1 << (63 - square))
        log.debug('Generating diagonal masks... Done.')

    @property
    def WHITE_PIECES(self) -> int:
        return self.WHITE_PAWNS | self.WHITE_KNIGHTS | self.WHITE_BISHOPS | self.WHITE_ROOKS | self.WHITE_QUEENS | self.WHITE_KINGS

    @property
    def BLACK_PIECES(self) -> int:
        return self.BLACK_PAWNS | self.BLACK_KNIGHTS | self.BLACK_BISHOPS | self.BLACK_ROOKS | self.BLACK_QUEENS | self.BLACK_KINGS

    @property
    def ALL_PIECES(self) -> int:
        return self.WHITE_PIECES | self.BLACK_PIECES

    @property
    def EMPTY_SQUARES(self) -> int:
        return ~self.ALL_PIECES

    def player_is_in_check(self, player_color: int) -> bool:
        """
        Determines if any OPPONENT piece is threatening the THIS PLAYER'S King.
        """
        log.debug('Check test START.')
        if player_color == BitBoardChess.WHITE:
            next_player_color = BitBoardChess.BLACK
        elif player_color == BitBoardChess.BLACK:
            next_player_color = BitBoardChess.WHITE
        else:
            raise Exception('Nope')
        check_board = 0

        if player_color == BitBoardChess.WHITE:
            KING_SQUARE = next(BitBoardChess.generate_positions_from_mask(self.WHITE_KINGS))
            # ******************** Pawns ********************
            check_board |= (self.BLACK_PAWNS >> 7) & ~BitBoardChess.FILE_H
            check_board |= (self.BLACK_PAWNS >> 9) & ~BitBoardChess.FILE_A
            # ******************** Knights ********************
            for knight_square in BitBoardChess.generate_positions_from_mask(self.BLACK_KNIGHTS & self.KNIGHT_MOVE_MASKS[KING_SQUARE]):
                check_board |= self.KNIGHT_MOVE_MASKS[knight_square]
            # ******************** Bishops ********************
            for bishop_square in BitBoardChess.generate_positions_from_mask(self.BLACK_BISHOPS & self.BISHOP_MOVE_MASKS[KING_SQUARE]):
                check_board |= self.BISHOP_MOVE_MASKS[bishop_square]
            # ******************** Rooks ********************
            for rook_square in BitBoardChess.generate_positions_from_mask(self.BLACK_ROOKS & self.ROOK_MOVE_MASKS[KING_SQUARE]):
                check_board |= self.ROOK_MOVE_MASKS[rook_square]
            # ******************** Queens ********************
            for queen_square in BitBoardChess.generate_positions_from_mask(self.BLACK_QUEENS & self.QUEEN_MOVE_MASKS[KING_SQUARE]):
                check_board |= self.QUEEN_MOVE_MASKS[queen_square]
            # ******************** Kings ********************
            # for king_square in BitBoardChess.generate_positions_from_mask(self.BLACK_KINGS):
            #     check_board |= self.KING_MOVE_MASKS[king_square]
            log.debug('Check test END.')
            if self.WHITE_KINGS & check_board:
                pass
            else:
                return False
        elif player_color == BitBoardChess.BLACK:
            KING_SQUARE = next(BitBoardChess.generate_positions_from_mask(self.BLACK_KINGS))
            # ******************** Pawns ********************
            check_board |= (self.WHITE_PAWNS << 7) & ~BitBoardChess.FILE_A
            check_board |= (self.WHITE_PAWNS << 9) & ~BitBoardChess.FILE_H
            # ******************** Knights ********************
            for knight_square in BitBoardChess.generate_positions_from_mask(self.WHITE_KNIGHTS & self.KNIGHT_MOVE_MASKS[KING_SQUARE]):
                check_board |= self.KNIGHT_MOVE_MASKS[knight_square]
            # ******************** Bishops ********************
            for bishop_square in BitBoardChess.generate_positions_from_mask(self.WHITE_BISHOPS & self.BISHOP_MOVE_MASKS[KING_SQUARE]):
                check_board |= self.BISHOP_MOVE_MASKS[bishop_square]
            # ******************** Rooks ********************
            for rook_square in BitBoardChess.generate_positions_from_mask(self.WHITE_ROOKS & self.ROOK_MOVE_MASKS[KING_SQUARE]):
                check_board |= self.ROOK_MOVE_MASKS[rook_square]
            # ******************** Queens ********************
            for queen_square in BitBoardChess.generate_positions_from_mask(self.WHITE_QUEENS & self.QUEEN_MOVE_MASKS[KING_SQUARE]):
                check_board |= self.QUEEN_MOVE_MASKS[queen_square]
            # ******************** Kings ********************
            # for king_square in BitBoardChess.generate_positions_from_mask(self.WHITE_KINGS):
            #     check_board |= self.KING_MOVE_MASKS[king_square]
            log.debug('Check test END.')
            if self.BLACK_KINGS & check_board:
                pass
            else:
                return False

        _, check_board = self.generate_all_possible_moves(piece_color=next_player_color)
        log.debug('Check test END.')

        # BitBoardChess.print_bitboard(check_board)
        if player_color == BitBoardChess.WHITE and self.WHITE_KINGS & check_board:
            return True
        elif player_color == BitBoardChess.BLACK and self.BLACK_KINGS & check_board:
            return True
        return False

    def setup_piece_masks(self) -> None:
        log.debug('Generating piece masks...')
        for square in range(64):
            self.KNIGHT_MOVE_MASKS[square] = self.process_knight_move(board_position=square, piece_color=None)
            self.BISHOP_MOVE_MASKS[square] = (self.URDL_DIAGONAL_MASKS[square] | self.ULDR_DIAGONAL_MASKS[square]) & ~(1 << (63 - square))
            self.ROOK_MOVE_MASKS[square] = self.HV_MASKS[square]
            self.QUEEN_MOVE_MASKS[square] = (self.URDL_DIAGONAL_MASKS[square] | self.ULDR_DIAGONAL_MASKS[square] | self.HV_MASKS[square]) & ~(1 << (63 - square))
            self.KING_MOVE_MASKS[square] = self.process_king_move(board_position=square, piece_color=None)
            # print(square)
            # BitBoardChess.print_bitboard(self.KING_MOVE_MASKS[square])
        log.debug('Generating piece masks... Done.')

    @staticmethod
    def reverse_bits(bitboard: int) -> int:
        bits_string = f"{bitboard:064b}"
        reversed_bits_string = ''.join(bits_string[::-1])
        # log.debug(f'{bits_string} -> {reversed_bits_string}')
        reversed_number = int(reversed_bits_string, base=2)
        return reversed_number

    @staticmethod
    def print_bitboard(bitboard: int) -> None:
        board_string = f"{bitboard:064b}"
        for idx, char in enumerate(board_string):
            if idx % 8 == 0:
                print()
            print(" ", end="")
            if char == '1':
                print(bcolors.OKGREEN + char + bcolors.CEND, end='')
            else:
                print(char, end='')
        print()
        print()

    @staticmethod
    def convert_position_to_rank(board_position: int) -> int:
        return 7 - (board_position // 8)

    @staticmethod
    def convert_position_to_file(board_position: int) -> int:
        return board_position % 8

    @staticmethod
    def convert_position_to_algebraic_notation(board_position: int) -> str:
        rank = 8 - (board_position // 8)
        file = board_position % 8 + 1
        file_str = chr(97 + file - 1)
        rank_str = str(rank)
        return file_str + rank_str

    @staticmethod
    def convert_algebraic_notation_to_position(algebraic_notation: str) -> int:
        """
        Converts a two-character algebraic notation (b2, c4, etc) to the board position index.
        """
        algebraic_notation = algebraic_notation.lower()
        file = ord(algebraic_notation[0]) - 97
        rank = int(algebraic_notation[1])
        rank = 8 - rank
        board_position = (rank * 8) + file
        return board_position

    @staticmethod
    def convert_algebraic_notation_to_mask(algebraic_notation: str) -> int:
        """
        Converts a two-character algebraic notation (b2, c4, etc) to a bit representation of
        the board.
        """
        algebraic_notation = algebraic_notation.lower()
        file = ord(algebraic_notation[0]) - 97
        rank = int(algebraic_notation[1])
        rank = 8 - rank
        rank *= 8
        return BitBoardChess.convert_position_to_mask(board_position=rank + file)

    @staticmethod
    def convert_position_to_mask(board_position: int) -> int:
        return 1 << (63 - board_position)

    @staticmethod
    def generate_positions_from_mask(board: int) -> int:
        bit_value = board & ~(board - 1)
        while bit_value:
            yield 63 - int(log2(bit_value))
            board = board & ~bit_value
            bit_value = board & ~(board - 1)
        return

    @staticmethod
    def generate_masks_from_mask(board: int) -> int:
        bit_value = board & ~(board - 1)
        while bit_value:
            yield bit_value
            board = board & ~bit_value
            bit_value = board & ~(board - 1)
        return

    def generate_horizontal_moves(self, board_position: int, piece_color: int) -> int:
        """
        Used to generate all available destination squares for pieces which can slide horizontally:
            --> Rook, Queen
        """
        # position_mask = 1 << (63 - board_position)
        # occupied = self.ALL_PIECES
        # left_mask = occupied ^ (occupied - (2 * position_mask))
        # left_mask = left_mask & self.RANK_MASKS[BitBoardChess.convert_position_to_rank(board_position=board_position)]
        # right_mask = occupied ^ BitBoardChess.reverse_bits(abs((BitBoardChess.reverse_bits(occupied) - (2 * BitBoardChess.reverse_bits(position_mask)))))
        # right_mask = right_mask & self.RANK_MASKS[BitBoardChess.convert_position_to_rank(board_position=board_position)]
        # horizontal_move_mask = left_mask ^ right_mask
        # if piece_color == BitBoardChess.WHITE:
        #     horizontal_move_mask = horizontal_move_mask & (~self.WHITE_PIECES)
        # else:
        #     horizontal_move_mask = horizontal_move_mask & (~self.BLACK_PIECES)
        # return horizontal_move_mask
        return self.generate_movement_mask(board_position=board_position, piece_color=piece_color, movement_mask=self.RANK_MASKS[BitBoardChess.convert_position_to_rank(board_position=board_position)])

    def generate_movement_mask(self, board_position: int, piece_color: int, movement_mask: int) -> int:
        position_mask = 1 << (63 - board_position)
        occupied = self.ALL_PIECES & movement_mask
        up_mask = occupied ^ (occupied - (2 * position_mask))
        up_mask = up_mask & movement_mask

        # Reverse the board, and do the same up logic
        occupied_reversed = BitBoardChess.reverse_bits(occupied)
        position_mask_reversed = BitBoardChess.reverse_bits(position_mask)
        movement_mask_reversed = BitBoardChess.reverse_bits(movement_mask)
        # board_position_reversed = 63 - board_position

        down_mask = occupied_reversed ^ (occupied_reversed - (2 * position_mask_reversed))
        down_mask = down_mask & movement_mask_reversed
        down_mask = BitBoardChess.reverse_bits(bitboard=down_mask)
        # BitBoardChess.print_bitboard(down_mask)

        combined_mask = up_mask ^ down_mask
        if piece_color == BitBoardChess.WHITE:
            combined_mask = combined_mask & (~self.WHITE_PIECES)
        else:
            combined_mask = combined_mask & (~self.BLACK_PIECES)
        return combined_mask

    def generate_vertical_moves(self, board_position: int, piece_color: int) -> int:
        """
        Used to generate all available destination squares for pieces which can slide vertically:
            --> Rook, Queen
        """
        # position_mask = 1 << (63 - board_position)
        # occupied = self.ALL_PIECES & self.FILE_MASKS[BitBoardChess.convert_position_to_file(board_position=board_position)]
        # up_mask = occupied ^ (occupied - (2 * position_mask))
        # up_mask = up_mask & self.FILE_MASKS[BitBoardChess.convert_position_to_file(board_position=board_position)]

        # # Reverse the board, and do the same up logic
        # occupied_reversed = BitBoardChess.reverse_bits(occupied)
        # position_mask_reversed = BitBoardChess.reverse_bits(position_mask)
        # board_position_reversed = 63 - board_position

        # down_mask = occupied_reversed ^ (occupied_reversed - (2 * position_mask_reversed))
        # down_mask = down_mask & self.FILE_MASKS[BitBoardChess.convert_position_to_file(board_position=board_position_reversed)]
        # down_mask = BitBoardChess.reverse_bits(bitboard=down_mask)
        # # BitBoardChess.print_bitboard(down_mask)

        # vertical_move_mask = up_mask ^ down_mask
        # if piece_color == BitBoardChess.WHITE:
        #     vertical_move_mask = vertical_move_mask & (~self.WHITE_PIECES)
        # else:
        #     vertical_move_mask = vertical_move_mask & (~self.BLACK_PIECES)
        # return vertical_move_mask
        return self.generate_movement_mask(board_position=board_position, piece_color=piece_color, movement_mask=self.FILE_MASKS[BitBoardChess.convert_position_to_file(board_position=board_position)])

    def generate_diagonal_uldr_moves(self, board_position: int, piece_color: int) -> int:
        """
        Used to generate all available destination squares for pieces which can slide diagonally:
            --> Bishop, Queen
        """
        # position_mask = 1 << (63 - board_position)
        # occupied = self.ALL_PIECES & self.ULDR_DIAGONAL_MASKS[board_position]
        # up_mask = occupied ^ (occupied - (2 * position_mask))
        # up_mask = up_mask & self.ULDR_DIAGONAL_MASKS[board_position]
        # down_mask = occupied ^ BitBoardChess.reverse_bits(abs((BitBoardChess.reverse_bits(occupied) - (2 * BitBoardChess.reverse_bits(position_mask)))))
        # down_mask = down_mask & self.ULDR_DIAGONAL_MASKS[board_position]
        # ul_dr_move_mask = up_mask ^ down_mask
        # if piece_color == BitBoardChess.WHITE:
        #     ul_dr_move_mask = ul_dr_move_mask & (~self.WHITE_PIECES)
        # else:
        #     ul_dr_move_mask = ul_dr_move_mask & (~self.BLACK_PIECES)

        # return ul_dr_move_mask
        return self.generate_movement_mask(board_position=board_position, piece_color=piece_color, movement_mask=self.ULDR_DIAGONAL_MASKS[board_position])

    def generate_diagonal_urdl_moves(self, board_position: int, piece_color: int) -> int:
        """
        Used to generate all available destination squares for pieces which can slide diagonally:
            --> Bishop, Queen
        """
        # position_mask = 1 << (63 - board_position)
        # occupied = self.ALL_PIECES & self.URDL_DIAGONAL_MASKS[board_position]
        # up_mask = occupied ^ (occupied - (2 * position_mask))
        # up_mask = up_mask & self.URDL_DIAGONAL_MASKS[board_position]
        # down_mask = occupied ^ BitBoardChess.reverse_bits(abs((BitBoardChess.reverse_bits(occupied) - (2 * BitBoardChess.reverse_bits(position_mask)))))
        # down_mask = down_mask & self.URDL_DIAGONAL_MASKS[board_position]
        # ur_dl_move_mask = up_mask ^ down_mask
        # if piece_color == BitBoardChess.WHITE:
        #     ur_dl_move_mask = ur_dl_move_mask & (~self.WHITE_PIECES)
        # else:
        #     ur_dl_move_mask = ur_dl_move_mask & (~self.BLACK_PIECES)

        # return ur_dl_move_mask
        return self.generate_movement_mask(board_position=board_position, piece_color=piece_color, movement_mask=self.URDL_DIAGONAL_MASKS[board_position])

    def process_bishop_move(self, board_position: int, piece_color: int) -> int:
        """
        Handles calculating all possible destination squares for the Bishop piece.
        Utilizes ULDR_DIAGONAL_MASKS and URDL_DIAGONAL_MASKS to determine which squares are in reach.
        Results are modified for captures of the opponent's piece.
        """
        # print(' ' + '*' * 6 + ' ' + BitBoardChess.convert_position_to_algebraic_notation(board_position) + ' ' + '*' * 6)
        move_mask = (self.generate_diagonal_uldr_moves(board_position=board_position, piece_color=piece_color) | self.generate_diagonal_urdl_moves(board_position=board_position, piece_color=piece_color))
        # BitBoardChess.print_bitboard(move_mask)
        return move_mask

    def process_rook_move(self, board_position: int, piece_color: int) -> int:
        """
        Handles calculating all possible destination squares for the Rook piece.
        Combines the horizontal and vertical move masks.
        Results are modified for captures of the opponent's piece.
        """
        # print(' ' + '*' * 6 + ' ' + BitBoardChess.convert_position_to_algebraic_notation(board_position) + ' ' + '*' * 6)
        move_mask = self.generate_horizontal_moves(board_position=board_position, piece_color=piece_color) | self.generate_vertical_moves(board_position=board_position, piece_color=piece_color)
        # BitBoardChess.print_bitboard(move_mask)
        return move_mask

    def process_queen_move(self, board_position: int, piece_color: int) -> int:
        """
        Handles calculating all possible destination squares for the Queen piece.
        Combines the horizontal, vertical, and diagonal move masks.
        Results are modified for captures of the opponent's piece.
        """
        # print(' ' + '*' * 6 + ' ' + BitBoardChess.convert_position_to_algebraic_notation(board_position) + ' ' + '*' * 6)
        move_mask = self.generate_horizontal_moves(board_position=board_position, piece_color=piece_color) | self.generate_vertical_moves(board_position=board_position, piece_color=piece_color)
        move_mask |= self.generate_diagonal_uldr_moves(board_position=board_position, piece_color=piece_color) | self.generate_diagonal_urdl_moves(board_position=board_position, piece_color=piece_color)
        # BitBoardChess.print_bitboard(move_mask)
        return move_mask

    def process_king_move(self, board_position: int, piece_color: int) -> int:
        """
        Handles calculating all possible destination squares for the king piece.
        Utilizes KING_SPAN to determine which squares are in reach, and the
        span is bit-shifted across the board to the king's location
        """
        # print(' ' + '*' * 6 + ' ' + BitBoardChess.convert_position_to_algebraic_notation(board_position) + ' ' + '*' * 6)
        move_mask = 0 | 1 << (63 - board_position)

        if BitBoardChess.KING_SQUARE - board_position > 0:
            move_mask = (BitBoardChess.KING_SPAN << (BitBoardChess.KING_SQUARE - board_position)) & BitBoardChess.SIXTY_FOUR_BIT_MASK
        else:
            move_mask = (BitBoardChess.KING_SPAN >> (board_position - BitBoardChess.KING_SQUARE)) & BitBoardChess.SIXTY_FOUR_BIT_MASK

        # Bit-shift cleanup - King can't move from A file to H file by shifting left, etc...
        if board_position % 8 == 0:
            move_mask = move_mask & ~BitBoardChess.FILE_H
        elif board_position % 8 == 7:
            move_mask = move_mask & ~BitBoardChess.FILE_A

        # King can go to where an opponent's piece is located, but not one of its own pieces
        if piece_color == BitBoardChess.WHITE:
            move_mask = move_mask & (~self.WHITE_PIECES)
        elif piece_color == BitBoardChess.BLACK:
            move_mask = move_mask & (~self.BLACK_PIECES)

        # BitBoardChess.print_bitboard(move_mask)
        return move_mask

    def process_pawn_move(self, board_position: int, piece_color: int) -> int:
        """
        Handles calculating all possible destination squares for the pawn piece.
        Assumes a one-square vertical move by default, unless that square is occupied by any piece.
        If a one-square move is possible, and the pawn is still on its starting rank,
        an initial move of 2 squares is available if this destination square is also unoccupied.

        CAN WE DO THESE ALL AT ONCE?

        """
        # print(' ' + '*' * 6 + ' ' + BitBoardChess.convert_position_to_algebraic_notation(board_position) + ' ' + '*' * 6)
        initial_position = 0 | 1 << (63 - board_position)
        if piece_color == BitBoardChess.WHITE:
            # Moving up the board, but not to the last rank -- promotion is handled separately
            move_mask = (initial_position << 8) & BitBoardChess.SIXTY_FOUR_BIT_MASK & self.EMPTY_SQUARES & ~BitBoardChess.RANK_8
            if move_mask > 0 and initial_position & BitBoardChess.RANK_2:
                # We started on the initial rank, and we were able to move 1 square -- let's try for two.
                move_mask |= (initial_position << 16) & BitBoardChess.SIXTY_FOUR_BIT_MASK & self.EMPTY_SQUARES & ~BitBoardChess.RANK_8
        elif piece_color == BitBoardChess.BLACK:
            # Moving down the board, but not to the last rank -- promotion is handled separately
            move_mask = (initial_position >> 8) & BitBoardChess.SIXTY_FOUR_BIT_MASK & self.EMPTY_SQUARES & ~BitBoardChess.RANK_1
            if move_mask > 0 and initial_position & BitBoardChess.RANK_7:
                # We started on the initial rank, and we were able to move 1 square -- let's try for two.
                move_mask |= (initial_position >> 16) & BitBoardChess.SIXTY_FOUR_BIT_MASK & self.EMPTY_SQUARES & ~BitBoardChess.RANK_1
        # BitBoardChess.print_bitboard(move_mask)
        return move_mask

    def process_pawn_capture_left(self, board_position: int, piece_color: int) -> int:
        """
        Handles calculating all possible destination squares for the pawn piece.
        Capturing to the left.
        F-file is excluded because pieces can not end up there after capturing left.

        CAN WE DO THESE ALL AT ONCE?

        Do we do (self.BLACK_PIECES | self.EN_PASSANT) and (self.WHITE_PIECES | self.EN_PASSANT) ???

        """
        # print(' ' + '*' * 6 + ' ' + BitBoardChess.convert_position_to_algebraic_notation(board_position) + ' ' + '*' * 6)
        initial_position = 0 | 1 << (63 - board_position)
        if piece_color == BitBoardChess.WHITE:
            # Moving up the board, but not to the last rank -- promotion is handled separately
            # Can not end up in H file as WHITE after capturing to the LEFT
            move_mask = (initial_position << 9) & BitBoardChess.SIXTY_FOUR_BIT_MASK & self.BLACK_PIECES & ~BitBoardChess.RANK_8 & ~BitBoardChess.FILE_H
        elif piece_color == BitBoardChess.BLACK:
            # Moving down the board, but not to the last rank -- promotion is handled separately
            move_mask = (initial_position >> 7) & BitBoardChess.SIXTY_FOUR_BIT_MASK & self.WHITE_PIECES & ~BitBoardChess.RANK_1 & ~BitBoardChess.FILE_H
        # BitBoardChess.print_bitboard(move_mask)
        return move_mask

    def process_pawn_capture_right(self, board_position: int, piece_color: int) -> int:
        """
        Handles calculating all possible destination squares for the pawn piece.
        Capturing to the left.
        A-file is excluded because pieces can not end up there after capturing right.

        CAN WE DO THESE ALL AT ONCE?

        """
        # print(' ' + '*' * 6 + ' ' + BitBoardChess.convert_position_to_algebraic_notation(board_position) + ' ' + '*' * 6)
        initial_position = 0 | 1 << (63 - board_position)
        if piece_color == BitBoardChess.WHITE:
            # Moving up the board, but not to the last rank -- promotion is handled separately
            # Can not end up in H file as WHITE after capturing to the LEFT
            move_mask = (initial_position << 7) & BitBoardChess.SIXTY_FOUR_BIT_MASK & self.BLACK_PIECES & ~BitBoardChess.RANK_8 & ~BitBoardChess.FILE_A
        elif piece_color == BitBoardChess.BLACK:
            # Moving down the board, but not to the last rank -- promotion is handled separately
            move_mask = (initial_position >> 9) & BitBoardChess.SIXTY_FOUR_BIT_MASK & self.WHITE_PIECES & ~BitBoardChess.RANK_1 & ~BitBoardChess.FILE_A
        # BitBoardChess.print_bitboard(move_mask)
        return move_mask

    def process_pawn_capture_en_passant(self, board_position: int, piece_color: int) -> int:
        if not self.EN_PASSANT:
            return 0

        # print(' ' + '*' * 6 + ' ' + BitBoardChess.convert_position_to_algebraic_notation(board_position) + ' ' + '*' * 6)
        initial_position = 0 | 1 << (63 - board_position)
        move_mask = 0
        # Left
        if piece_color == BitBoardChess.WHITE and initial_position & BitBoardChess.RANK_5:
            # Moving up the board, but not to the last rank -- promotion is handled separately
            # Can not end up in H file as WHITE after capturing to the LEFT
            move_mask |= (initial_position << 9) & BitBoardChess.SIXTY_FOUR_BIT_MASK & self.EN_PASSANT & BitBoardChess.RANK_6 & ~BitBoardChess.FILE_H
        elif piece_color == BitBoardChess.BLACK and initial_position & BitBoardChess.RANK_4:
            # Moving down the board, but not to the last rank -- promotion is handled separately
            move_mask |= (initial_position >> 7) & BitBoardChess.SIXTY_FOUR_BIT_MASK & self.EN_PASSANT & BitBoardChess.RANK_3 & ~BitBoardChess.FILE_H

        # Right
        if piece_color == BitBoardChess.WHITE and initial_position & BitBoardChess.RANK_5:
            # Moving up the board, but not to the last rank -- promotion is handled separately
            # Can not end up in H file as WHITE after capturing to the LEFT
            move_mask |= (initial_position << 7) & BitBoardChess.SIXTY_FOUR_BIT_MASK & self.EN_PASSANT & BitBoardChess.RANK_6 & ~BitBoardChess.FILE_A
        elif piece_color == BitBoardChess.BLACK and initial_position & BitBoardChess.RANK_4:
            # Moving down the board, but not to the last rank -- promotion is handled separately
            move_mask |= (initial_position >> 9) & BitBoardChess.SIXTY_FOUR_BIT_MASK & self.EN_PASSANT & BitBoardChess.RANK_3 & ~BitBoardChess.FILE_A
        # BitBoardChess.print_bitboard(move_mask)
        return move_mask

    def process_pawn_promotion_move(self, board_position: int, piece_color: int) -> int:
        """
        Handles calculating all possible destination squares for the pawn piece.
        Assumes a one-square vertical move by default, unless that square is occupied by any piece.
        Pawns can promote to a Queen, Rook, Bishop, or Knight.
        """
        # print(' ' + '*' * 6 + ' ' + BitBoardChess.convert_position_to_algebraic_notation(board_position) + ' ' + '*' * 6)
        initial_position = 0 | 1 << (63 - board_position)
        if (piece_color == BitBoardChess.WHITE and board_position > 15) or (piece_color == BitBoardChess.BLACK and board_position < 48):
            return 0

        # Move
        if piece_color == BitBoardChess.WHITE:
            # Moving up the board, but not to the last rank -- promotion is handled separately
            move_mask = (initial_position << 8) & BitBoardChess.SIXTY_FOUR_BIT_MASK & self.EMPTY_SQUARES & BitBoardChess.RANK_8
        elif piece_color == BitBoardChess.BLACK:
            # Moving down the board, but not to the last rank -- promotion is handled separately
            move_mask = (initial_position >> 8) & BitBoardChess.SIXTY_FOUR_BIT_MASK & self.EMPTY_SQUARES & BitBoardChess.RANK_1

        # BitBoardChess.print_bitboard(move_mask)
        return move_mask

    def process_pawn_promotion_capture(self, board_position: int, piece_color: int) -> int:
        """
        Handles calculating all possible destination squares for the pawn piece.
        Assumes a one-square vertical move by default, unless that square is occupied by any piece.
        Pawns can promote to a Queen, Rook, Bishop, or Knight.
        """
        # print(' ' + '*' * 6 + ' ' + BitBoardChess.convert_position_to_algebraic_notation(board_position) + ' ' + '*' * 6)
        initial_position = 0 | 1 << (63 - board_position)
        if (piece_color == BitBoardChess.WHITE and board_position > 15) or (piece_color == BitBoardChess.BLACK and board_position < 48):
            return 0

        move_mask = 0
        # Capture LEFT and promote
        if piece_color == BitBoardChess.WHITE:
            # Moving up the board, but not to the last rank -- promotion is handled separately
            # Can not end up in H file as WHITE after capturing to the LEFT
            move_mask |= ((initial_position << 9) & BitBoardChess.SIXTY_FOUR_BIT_MASK & self.BLACK_PIECES & BitBoardChess.RANK_8 & ~BitBoardChess.FILE_H)
        elif piece_color == BitBoardChess.BLACK:
            # Moving down the board, but not to the last rank -- promotion is handled separately
            move_mask |= ((initial_position >> 7) & BitBoardChess.SIXTY_FOUR_BIT_MASK & self.EMPTY_SQUARES & BitBoardChess.RANK_1 & ~BitBoardChess.FILE_H)

        # Capture RIGHT and promote
        if piece_color == BitBoardChess.WHITE:
            # Moving up the board, but not to the last rank -- promotion is handled separately
            # Can not end up in H file as WHITE after capturing to the LEFT
            move_mask |= ((initial_position << 7) & BitBoardChess.SIXTY_FOUR_BIT_MASK & self.BLACK_PIECES & BitBoardChess.RANK_8 & ~BitBoardChess.FILE_A)
        elif piece_color == BitBoardChess.BLACK:
            # Moving down the board, but not to the last rank -- promotion is handled separately
            move_mask |= ((initial_position >> 9) & BitBoardChess.SIXTY_FOUR_BIT_MASK & self.EMPTY_SQUARES & BitBoardChess.RANK_1 & ~BitBoardChess.FILE_A)

        # BitBoardChess.print_bitboard(move_mask)
        return move_mask

    def process_knight_move(self, board_position: int, piece_color: int) -> int:
        """
        Handles calculating all possible destination squares for the knight piece.
        Utilizes KNIGHT_SPAN to determine which squares are in reach, and the
        span is bit-shifted across the board to the knights's location
        """
        # print(' ' + '*' * 6 + ' ' + BitBoardChess.convert_position_to_algebraic_notation(board_position) + ' ' + '*' * 6)
        move_mask = 0 | 1 << (63 - board_position)

        if BitBoardChess.KNIGHT_SQUARE - board_position > 0:
            move_mask = (BitBoardChess.KNIGHT_SPAN << (BitBoardChess.KNIGHT_SQUARE - board_position)) & BitBoardChess.SIXTY_FOUR_BIT_MASK
        else:
            move_mask = (BitBoardChess.KNIGHT_SPAN >> (board_position - BitBoardChess.KNIGHT_SQUARE)) & BitBoardChess.SIXTY_FOUR_BIT_MASK

        if board_position % 8 < 2:
            move_mask = move_mask & ~BitBoardChess.FILE_GH
        elif board_position % 8 > 5:
            move_mask = move_mask & ~BitBoardChess.FILE_AB

        # Knight can go to where an opponent's piece is located, but not one of its own pieces
        if piece_color == BitBoardChess.WHITE:
            move_mask = move_mask & (~self.WHITE_PIECES)
        elif piece_color == BitBoardChess.BLACK:
            move_mask = move_mask & (~self.BLACK_PIECES)

        return move_mask

    def process_castling_moves(self, piece_color: int) -> list:
        castling_options = []
        if piece_color == BitBoardChess.WHITE:
            if self.CASTLING & self.WHITE_KING_SIDE_CASTLE_FLAG:
                # Check that KING side is clear...
                if not self.ALL_PIECES & 6:
                    # and player would not be in check along the way
                    self.save_state()
                    self.apply_move(Move(starting_square=60, ending_square=61))
                    check = self.player_is_in_check(BitBoardChess.WHITE)
                    self.load_state()
                    if not check:
                        self.save_state()
                        self.apply_move(Move(starting_square=60, ending_square=62))
                        check = self.player_is_in_check(BitBoardChess.WHITE)
                        self.load_state()
                    if not check:
                        castling_options.append((62, Move.KING))
            if self.CASTLING & BitBoardChess.WHITE_QUEEN_SIDE_CASTLE_FLAG:
                # Check that QUEEN side is clear...
                if not self.ALL_PIECES & 48:
                    #  and player would not be in check along the way
                    self.save_state()
                    self.apply_move(Move(starting_square=60, ending_square=59))
                    check = self.player_is_in_check(BitBoardChess.WHITE)
                    self.load_state()
                    if not check:
                        self.save_state()
                        self.apply_move(Move(starting_square=60, ending_square=58))
                        check = self.player_is_in_check(BitBoardChess.WHITE)
                        self.load_state()
                    if not check:
                        castling_options.append((58, Move.QUEEN))
        elif piece_color == BitBoardChess.BLACK:
            if self.CASTLING & BitBoardChess.BLACK_KING_SIDE_CASTLE_FLAG:
                # Check that KING side is clear...
                if not self.ALL_PIECES & 432345564227567616:
                    # and player would not be in check along the way
                    self.save_state()
                    self.apply_move(Move(starting_square=4, ending_square=5))
                    check = self.player_is_in_check(BitBoardChess.BLACK)
                    self.load_state()
                    if not check:
                        self.save_state()
                        self.apply_move(Move(starting_square=4, ending_square=6))
                        check = self.player_is_in_check(BitBoardChess.BLACK)
                        self.load_state()
                    if not check:
                        castling_options.append((6, Move.KING))
            if self.CASTLING & BitBoardChess.BLACK_QUEEN_SIDE_CASTLE_FLAG:
                # Check that QUEEN side is clear...
                if not self.ALL_PIECES & 3458764513820540928:
                    #  and player would not be in check along the way
                    self.save_state()
                    self.apply_move(Move(starting_square=4, ending_square=3))
                    check = self.player_is_in_check(BitBoardChess.BLACK)
                    self.load_state()
                    if not check:
                        self.save_state()
                        self.apply_move(Move(starting_square=4, ending_square=2))
                        check = self.player_is_in_check(BitBoardChess.BLACK)
                        self.load_state()
                    if not check:
                        castling_options.append((2, Move.QUEEN))
        return castling_options

    def determine_if_move_is_capture(self, destination: int, piece_color: int) -> bool:
        return self.BLACK_PIECES & BitBoardChess.convert_position_to_mask(destination) if piece_color == BitBoardChess.WHITE else self.WHITE_PIECES & BitBoardChess.convert_position_to_mask(destination)

    def determine_captured_piece(self, board_position: int, piece_color: int) -> int:
        destination_mask = BitBoardChess.convert_position_to_mask(board_position)
        if piece_color == BitBoardChess.WHITE:
            if destination_mask & self.BLACK_PAWNS:
                return Move.PAWN
            elif destination_mask & self.BLACK_KNIGHTS:
                return Move.KNIGHT
            elif destination_mask & self.BLACK_BISHOPS:
                return Move.BISHOP
            elif destination_mask & self.BLACK_ROOKS:
                return Move.ROOK
            elif destination_mask & self.BLACK_QUEENS:
                return Move.QUEEN
            elif destination_mask & self.BLACK_KINGS:
                return Move.KING
            else:
                return Move.NONE

        elif piece_color == BitBoardChess.BLACK:
            if destination_mask & self.WHITE_PAWNS:
                return Move.PAWN
            elif destination_mask & self.WHITE_KNIGHTS:
                return Move.KNIGHT
            elif destination_mask & self.WHITE_BISHOPS:
                return Move.BISHOP
            elif destination_mask & self.WHITE_ROOKS:
                return Move.ROOK
            elif destination_mask & self.WHITE_QUEENS:
                return Move.QUEEN
            elif destination_mask & self.WHITE_KINGS:
                return Move.KING
            else:
                return Move.NONE

        return Move.NONE

    def generate_all_possible_moves(self, piece_color: int) -> tuple:
        """
        """
        if (piece_color, self.WHITE_PAWNS, self.WHITE_KNIGHTS, self.WHITE_BISHOPS, self.WHITE_ROOKS, self.WHITE_QUEENS, self.WHITE_KINGS, self.BLACK_PAWNS, self.BLACK_KNIGHTS, self.BLACK_BISHOPS, self.BLACK_ROOKS, self.BLACK_QUEENS, self.BLACK_KINGS, self.CASTLING, self.EN_PASSANT) in self.MOVE_CACHE:
            return self.MOVE_CACHE[(piece_color, self.WHITE_PAWNS, self.WHITE_KNIGHTS, self.WHITE_BISHOPS, self.WHITE_ROOKS, self.WHITE_QUEENS, self.WHITE_KINGS, self.BLACK_PAWNS, self.BLACK_KNIGHTS, self.BLACK_BISHOPS, self.BLACK_ROOKS, self.BLACK_QUEENS, self.BLACK_KINGS, self.CASTLING, self.EN_PASSANT)]

        all_possible_moves = []
        threat_mask = 0
        # ******************** Pawns ********************
        # Pawn movement
        for pawn_square in BitBoardChess.generate_positions_from_mask(self.WHITE_PAWNS if piece_color == BitBoardChess.WHITE else self.BLACK_PAWNS):
            destinations = self.process_pawn_move(pawn_square, piece_color=piece_color)
            if destinations:
                for destination in BitBoardChess.generate_positions_from_mask(destinations):
                    all_possible_moves.append(Move(starting_square=pawn_square, ending_square=destination))

        # Pawn captures - LEFT
        # for pawn_square in BitBoardChess.generate_positions_from_mask(self.WHITE_PAWNS if piece_color == BitBoardChess.WHITE else self.BLACK_PAWNS):
            destinations = self.process_pawn_capture_left(pawn_square, piece_color=piece_color)
            threat_mask |= destinations
            for destination in BitBoardChess.generate_positions_from_mask(destinations):
                all_possible_moves.append(Move(starting_square=pawn_square, ending_square=destination, is_capture=True, extra_piece_info=self.determine_captured_piece(board_position=destination, piece_color=piece_color)))

        # Pawn captures - RIGHT
        # for pawn_square in BitBoardChess.generate_positions_from_mask(self.WHITE_PAWNS if piece_color == BitBoardChess.WHITE else self.BLACK_PAWNS):
            destinations = self.process_pawn_capture_right(pawn_square, piece_color=piece_color)
            threat_mask |= destinations
            for destination in BitBoardChess.generate_positions_from_mask(destinations):
                all_possible_moves.append(Move(starting_square=pawn_square, ending_square=destination, is_capture=True, extra_piece_info=self.determine_captured_piece(board_position=destination, piece_color=piece_color)))

        # Promotion
        # for pawn_square in BitBoardChess.generate_positions_from_mask(self.WHITE_PAWNS if piece_color == BitBoardChess.WHITE else self.BLACK_PAWNS):
            destinations = self.process_pawn_promotion_move(pawn_square, piece_color=piece_color)
            for destination in BitBoardChess.generate_positions_from_mask(destinations):
                all_possible_moves.append(Move(starting_square=pawn_square, ending_square=destination, is_promotion=True, extra_piece_info=Move.KNIGHT))
                all_possible_moves.append(Move(starting_square=pawn_square, ending_square=destination, is_promotion=True, extra_piece_info=Move.BISHOP))
                all_possible_moves.append(Move(starting_square=pawn_square, ending_square=destination, is_promotion=True, extra_piece_info=Move.ROOK))
                all_possible_moves.append(Move(starting_square=pawn_square, ending_square=destination, is_promotion=True, extra_piece_info=Move.QUEEN))

            destinations = self.process_pawn_promotion_capture(pawn_square, piece_color=piece_color)
            threat_mask |= destinations
            for destination in BitBoardChess.generate_positions_from_mask(destinations):
                all_possible_moves.append(Move(starting_square=pawn_square, ending_square=destination, is_capture=True, is_promotion=True, extra_piece_info=Move.KNIGHT))
                all_possible_moves.append(Move(starting_square=pawn_square, ending_square=destination, is_capture=True, is_promotion=True, extra_piece_info=Move.BISHOP))
                all_possible_moves.append(Move(starting_square=pawn_square, ending_square=destination, is_capture=True, is_promotion=True, extra_piece_info=Move.ROOK))
                all_possible_moves.append(Move(starting_square=pawn_square, ending_square=destination, is_capture=True, is_promotion=True, extra_piece_info=Move.QUEEN))

        # Pawn captures - En Passant
        if self.EN_PASSANT:
            for pawn_square in BitBoardChess.generate_positions_from_mask(self.WHITE_PAWNS if piece_color == BitBoardChess.WHITE else self.BLACK_PAWNS):
                destinations = self.process_pawn_capture_en_passant(pawn_square, piece_color=piece_color)
                for destination in BitBoardChess.generate_positions_from_mask(destinations):
                    all_possible_moves.append(Move(starting_square=pawn_square, ending_square=destination, is_capture=True, is_en_passant=True, extra_piece_info=self.determine_captured_piece(board_position=destination + 8 if piece_color == BitBoardChess.WHITE else -8, piece_color=piece_color)))

        # ******************** Knights ********************
        for knight_square in BitBoardChess.generate_positions_from_mask(self.WHITE_KNIGHTS if piece_color == BitBoardChess.WHITE else self.BLACK_KNIGHTS):
            destinations = self.process_knight_move(knight_square, piece_color=piece_color)
            threat_mask |= destinations
            for destination in BitBoardChess.generate_positions_from_mask(destinations):
                all_possible_moves.append(Move(starting_square=knight_square, ending_square=destination, is_capture=self.determine_if_move_is_capture(destination, piece_color), extra_piece_info=self.determine_captured_piece(board_position=destination, piece_color=piece_color)))

        # ******************** Bishops ********************
        for bishop_square in BitBoardChess.generate_positions_from_mask(self.WHITE_BISHOPS if piece_color == BitBoardChess.WHITE else self.BLACK_BISHOPS):
            destinations = self.process_bishop_move(bishop_square, piece_color=piece_color)
            threat_mask |= destinations
            for destination in BitBoardChess.generate_positions_from_mask(destinations):
                all_possible_moves.append(Move(starting_square=bishop_square, ending_square=destination, is_capture=self.determine_if_move_is_capture(destination, piece_color), extra_piece_info=self.determine_captured_piece(board_position=destination, piece_color=piece_color)))

        # ******************** Rooks ********************
        for rook_square in BitBoardChess.generate_positions_from_mask(self.WHITE_ROOKS if piece_color == BitBoardChess.WHITE else self.BLACK_ROOKS):
            destinations = self.process_rook_move(rook_square, piece_color=piece_color)
            threat_mask |= destinations
            for destination in BitBoardChess.generate_positions_from_mask(destinations):
                all_possible_moves.append(Move(starting_square=rook_square, ending_square=destination, is_capture=self.determine_if_move_is_capture(destination, piece_color), extra_piece_info=self.determine_captured_piece(board_position=destination, piece_color=piece_color)))

        # ******************** Queens ********************
        for queen_square in BitBoardChess.generate_positions_from_mask(self.WHITE_QUEENS if piece_color == BitBoardChess.WHITE else self.BLACK_QUEENS):
            destinations = self.process_queen_move(queen_square, piece_color=piece_color)
            threat_mask |= destinations
            for destination in BitBoardChess.generate_positions_from_mask(destinations):
                all_possible_moves.append(Move(starting_square=queen_square, ending_square=destination, is_capture=self.determine_if_move_is_capture(destination, piece_color), extra_piece_info=self.determine_captured_piece(board_position=destination, piece_color=piece_color)))

        # ******************** King ********************
        for king_square in BitBoardChess.generate_positions_from_mask(self.WHITE_KINGS if piece_color == BitBoardChess.WHITE else self.BLACK_KINGS):
            destinations = self.process_king_move(king_square, piece_color=piece_color)
            threat_mask |= destinations
            for destination in BitBoardChess.generate_positions_from_mask(destinations):
                all_possible_moves.append(Move(starting_square=king_square, ending_square=destination, is_capture=self.determine_if_move_is_capture(destination, piece_color), extra_piece_info=self.determine_captured_piece(board_position=destination, piece_color=piece_color)))
            # ******************** Castling ********************
            castling_options = self.process_castling_moves(piece_color=piece_color)
            for (castling_option, extra_piece_info) in castling_options:
                all_possible_moves.append(Move(starting_square=king_square, ending_square=castling_option, is_castle=True, extra_piece_info=extra_piece_info))

        # log.info(f"""{len(all_possible_moves)} moves generated for {"WHITE" if piece_color == BitBoardChess.WHITE else "BLACK"}: {all_possible_moves}""")
        self.MOVE_CACHE[(piece_color, self.WHITE_PAWNS, self.WHITE_KNIGHTS, self.WHITE_BISHOPS, self.WHITE_ROOKS, self.WHITE_QUEENS, self.WHITE_KINGS, self.BLACK_PAWNS, self.BLACK_KNIGHTS, self.BLACK_BISHOPS, self.BLACK_ROOKS, self.BLACK_QUEENS, self.BLACK_KINGS, self.CASTLING, self.EN_PASSANT)] = (all_possible_moves, threat_mask)
        return all_possible_moves, threat_mask

    def generate_all_legal_moves(self, piece_color: int) -> tuple:
        if (piece_color, self.WHITE_PAWNS, self.WHITE_KNIGHTS, self.WHITE_BISHOPS, self.WHITE_ROOKS, self.WHITE_QUEENS, self.WHITE_KINGS, self.BLACK_PAWNS, self.BLACK_KNIGHTS, self.BLACK_BISHOPS, self.BLACK_ROOKS, self.BLACK_QUEENS, self.BLACK_KINGS, self.CASTLING, self.EN_PASSANT) in self.LEGAL_MOVE_CACHE:
            return self.LEGAL_MOVE_CACHE[(piece_color, self.WHITE_PAWNS, self.WHITE_KNIGHTS, self.WHITE_BISHOPS, self.WHITE_ROOKS, self.WHITE_QUEENS, self.WHITE_KINGS, self.BLACK_PAWNS, self.BLACK_KNIGHTS, self.BLACK_BISHOPS, self.BLACK_ROOKS, self.BLACK_QUEENS, self.BLACK_KINGS, self.CASTLING, self.EN_PASSANT)]
        all_legal_moves = []
        # all_legal_moves_mask = 0

        all_possible_moves, _ = self.generate_all_possible_moves(piece_color=piece_color)
        move_list_contains_castling = sum([1 for move in all_possible_moves if move.is_castle])
        if move_list_contains_castling > 0:
            # Determine if player is currently in check
            player_is_in_check = self.player_is_in_check(player_color=piece_color)
        else:
            # Check is not necessary to determine yet
            player_is_in_check = False

        for move in all_possible_moves:
            if not (player_is_in_check and move.is_castle):
                self.save_state()
                self.apply_move(move=move)
                if not self.player_is_in_check(player_color=piece_color):
                    # Move is valid
                    all_legal_moves.append(move)
                self.load_state()
        self.LEGAL_MOVE_CACHE[(piece_color, self.WHITE_PAWNS, self.WHITE_KNIGHTS, self.WHITE_BISHOPS, self.WHITE_ROOKS, self.WHITE_QUEENS, self.WHITE_KINGS, self.BLACK_PAWNS, self.BLACK_KNIGHTS, self.BLACK_BISHOPS, self.BLACK_ROOKS, self.BLACK_QUEENS, self.BLACK_KINGS, self.CASTLING, self.EN_PASSANT)] = all_legal_moves
        return all_legal_moves

    def apply_move(self, move: Move) -> None:
        """
        Do I need the capture checks? Can I just & ~ the whole thing?
        """
        # start_square = move.starting_square
        # end_square = move.ending_square
        start_mask = move.starting_mask
        end_mask = move.ending_mask

        EN_PASSANT_FLAG = False

        if self.WHITE_PIECES & start_mask:
            # Check if we need to disable ability to castle
            if self.CASTLING & (BitBoardChess.WHITE_KING_SIDE_CASTLE_FLAG | BitBoardChess.WHITE_QUEEN_SIDE_CASTLE_FLAG):
                if self.WHITE_KINGS & start_mask:
                    self.CASTLING &= ~BitBoardChess.WHITE_KING_SIDE_CASTLE_FLAG
                    self.CASTLING &= ~BitBoardChess.WHITE_QUEEN_SIDE_CASTLE_FLAG
                    log.info('Disabling WHITE castling due to KING move.')
                elif self.WHITE_ROOKS & start_mask:
                    if start_mask == 1:
                        self.CASTLING &= ~BitBoardChess.WHITE_KING_SIDE_CASTLE_FLAG
                        log.info('Disabling WHITE KING SIDE castling due to ROOK move.')
                    elif start_mask == 128:
                        self.CASTLING &= ~BitBoardChess.WHITE_QUEEN_SIDE_CASTLE_FLAG
                        log.info('Disabling WHITE QUEEN SIDE castling due to ROOK move.')

            if not move.is_promotion:
                for PIECE_BOARD in BitBoardChess.WHITE_PIECE_ATTRIBUTES:
                    if self.__getattribute__(PIECE_BOARD) & start_mask:
                        log.debug(f'Found WHITE piece in {PIECE_BOARD}.')
                        self.__setattr__(PIECE_BOARD, self.__getattribute__(PIECE_BOARD) & ~start_mask)
                        self.__setattr__(PIECE_BOARD, self.__getattribute__(PIECE_BOARD) | end_mask)
                        break
            else:
                # Remove the pawn from the board
                self.WHITE_PAWNS &= ~start_mask
                # Replace it with the promoted piece
                if move.extra_piece_info == Move.KNIGHT:
                    self.WHITE_KNIGHTS |= end_mask
                elif move.extra_piece_info == Move.BISHOP:
                    self.WHITE_BISHOPS |= end_mask
                elif move.extra_piece_info == Move.ROOK:
                    self.WHITE_ROOKS |= end_mask
                elif move.extra_piece_info == Move.QUEEN:
                    self.WHITE_QUEENS |= end_mask

            # Pawn related moves
            # Pawn moved 2 space -> En Passant move
            if self.WHITE_PAWNS & end_mask and ((end_mask >> 16) & start_mask):
                self.EN_PASSANT = (end_mask >> 8)
                # log.debug(f'En Passant move detected: {move}.')
                EN_PASSANT_FLAG = True
            # Shift end_mask to the pawn location if this was an En Passant capture
            elif self.BLACK_PAWNS & (self.EN_PASSANT >> 8) and self.WHITE_PAWNS & self.EN_PASSANT:
                end_mask = end_mask >> 8
                # log.debug(f'En passant capture: {move}.')

            # Castling related moves
            if move.is_castle:
                if self.WHITE_KINGS & end_mask and start_mask == 8 and end_mask == 2:
                    # Move the KING SIDE Rook to f1
                    log.debug('WHITE castling KING SIDE')
                    self.apply_move(Move(starting_square=63, ending_square=61))
                elif self.WHITE_KINGS & end_mask and start_mask == 8 and end_mask == 32:
                    # Move the QUEEN SIDE Rook to d1
                    log.debug('WHITE castling QUEEN SIDE')
                    self.apply_move(Move(starting_square=56, ending_square=59))
                else:
                    raise Exception(f'Invalid castling move {move}.')

                self.CASTLING &= ~BitBoardChess.WHITE_KING_SIDE_CASTLE_FLAG
                self.CASTLING &= ~BitBoardChess.WHITE_QUEEN_SIDE_CASTLE_FLAG

            # Check for captures
            if self.BLACK_PIECES & end_mask:
                # Check if we captured BLACK's ROOK, and disable castling appropriately
                if self.BLACK_ROOKS & end_mask:
                    if end_mask == (1 << (63 - 0)):
                        self.CASTLING &= ~BitBoardChess.BLACK_QUEEN_SIDE_CASTLE_FLAG
                    if end_mask == (1 << (63 - 7)):
                        self.CASTLING &= ~BitBoardChess.BLACK_KING_SIDE_CASTLE_FLAG

                for CAPTURE_BOARD in BitBoardChess.BLACK_PIECE_ATTRIBUTES:
                    if self.__getattribute__(CAPTURE_BOARD) & end_mask:
                        self.__setattr__(CAPTURE_BOARD, self.__getattribute__(CAPTURE_BOARD) & ~end_mask)
                        log.debug(f'Found BLACK piece being captured in {CAPTURE_BOARD}.')
                        break

        elif self.BLACK_PIECES & start_mask:
            # Check if we need to disable ability to castle
            if self.CASTLING & (BitBoardChess.BLACK_KING_SIDE_CASTLE_FLAG | BitBoardChess.BLACK_QUEEN_SIDE_CASTLE_FLAG):
                if self.BLACK_KINGS & start_mask:
                    self.CASTLING &= ~BitBoardChess.BLACK_KING_SIDE_CASTLE_FLAG
                    self.CASTLING &= ~BitBoardChess.BLACK_QUEEN_SIDE_CASTLE_FLAG
                    log.info('Disabling BLACK castling due to KING move.')
                elif self.BLACK_ROOKS & start_mask:
                    if start_mask == (1 << (63 - 7)):
                        self.CASTLING &= ~BitBoardChess.BLACK_KING_SIDE_CASTLE_FLAG
                        log.info('Disabling BLACK KING SIDE castling due to ROOK move.')
                    elif start_mask == (1 << (63 - 0)):
                        self.CASTLING &= ~BitBoardChess.BLACK_QUEEN_SIDE_CASTLE_FLAG
                        log.info('Disabling BLACK QUEEN SIDE castling due to ROOK move.')

            if not move.is_promotion:
                for PIECE_BOARD in BitBoardChess.BLACK_PIECE_ATTRIBUTES:
                    if self.__getattribute__(PIECE_BOARD) & start_mask:
                        log.debug(f'Found BLACK piece in {PIECE_BOARD}.')
                        self.__setattr__(PIECE_BOARD, self.__getattribute__(PIECE_BOARD) & ~start_mask)
                        self.__setattr__(PIECE_BOARD, self.__getattribute__(PIECE_BOARD) | end_mask)
                        break
            else:
                # Remove the pawn from the board
                self.BLACK_PAWNS &= ~start_mask
                # Replace it with the promoted piece
                if move.extra_piece_info == Move.KNIGHT:
                    self.BLACK_KNIGHTS |= end_mask
                elif move.extra_piece_info == Move.BISHOP:
                    self.BLACK_BISHOPS |= end_mask
                elif move.extra_piece_info == Move.ROOK:
                    self.BLACK_ROOKS |= end_mask
                elif move.extra_piece_info == Move.QUEEN:
                    self.BLACK_QUEENS |= end_mask

            # Pawn related moves
            # # Pawn moved 2 space -> En Passant move
            if self.BLACK_PAWNS & end_mask and ((end_mask << 16) & start_mask):
                self.EN_PASSANT = (end_mask << 8)
                # log.debug(f'En Passant move detected: {move}.')
                EN_PASSANT_FLAG = True
            # Shift end_mask to the pawn location if this was an En Passant capture
            elif self.WHITE_PAWNS & (self.EN_PASSANT << 8) and self.BLACK_PAWNS & self.EN_PASSANT:
                end_mask = end_mask << 8
                # log.debug(f'En passant capture: {move}.')

            # Castling related moves
            if move.is_castle:
                if self.BLACK_KINGS & end_mask and start_mask == 576460752303423488 and end_mask == 144115188075855872:
                    # Move the KING SIDE Rook to f8
                    log.debug('BLACK castling KING SIDE')
                    self.apply_move(Move(starting_square=7, ending_square=5))
                elif self.BLACK_KINGS & end_mask and start_mask == 576460752303423488 and end_mask == 2305843009213693952:
                    # Move the QUEEN SIDE Rook to d8
                    log.debug('BLACK castling QUEEN SIDE')
                    self.apply_move(Move(starting_square=0, ending_square=3))
                else:
                    raise Exception(f'Invalid castling move {move}.')

                self.CASTLING &= ~BitBoardChess.BLACK_KING_SIDE_CASTLE_FLAG
                self.CASTLING &= ~BitBoardChess.BLACK_QUEEN_SIDE_CASTLE_FLAG

            # Check for captures
            if self.WHITE_PIECES & end_mask:
                # Check if we captured BLACK's ROOK, and disable castling appropriately
                if self.WHITE_ROOKS & end_mask:
                    if end_mask == (1 << (63 - 56)):
                        self.CASTLING &= ~BitBoardChess.WHITE_QUEEN_SIDE_CASTLE_FLAG
                    if end_mask == (1 << (63 - 63)):
                        self.CASTLING &= ~BitBoardChess.WHITE_KING_SIDE_CASTLE_FLAG

                for CAPTURE_BOARD in BitBoardChess.WHITE_PIECE_ATTRIBUTES:
                    if self.__getattribute__(CAPTURE_BOARD) & end_mask:
                        self.__setattr__(CAPTURE_BOARD, self.__getattribute__(CAPTURE_BOARD) & ~end_mask)
                        log.debug(f'Found WHITE piece being captured in {CAPTURE_BOARD}.')
                        break

        else:
            raise Exception('Move not found on board.')

        if EN_PASSANT_FLAG is False:
            self.EN_PASSANT = 0

        return

    def save_state(self) -> None:
        board_state = {attribute: self.__getattribute__(attribute) for attribute in BitBoardChess.SAVE_ORDER}
        self.GAME_STACK.append(board_state)
        # print(f'SAVING {board_state}')

    def load_state(self) -> None:
        board_state = self.GAME_STACK.pop()
        for attribute, value in board_state.items():
            self.__setattr__(attribute, value)

    def evaluate(self) -> int:
        """
        """
        PAWN_WEIGHT = 100
        KNIGHT_WEIGHT = 300
        BISHOP_WEIGHT = 300
        ROOK_WEIGHT = 500
        QUEEN_WEIGHT = 800

        pawn_score = sum([1 * PAWN_WEIGHT for _ in BitBoardChess.generate_positions_from_mask(self.WHITE_PAWNS)]) - sum([1 * PAWN_WEIGHT for _ in BitBoardChess.generate_positions_from_mask(self.BLACK_PAWNS)])
        knight_score = sum([1 * KNIGHT_WEIGHT for _ in BitBoardChess.generate_positions_from_mask(self.WHITE_KNIGHTS)]) - sum([1 * KNIGHT_WEIGHT for _ in BitBoardChess.generate_positions_from_mask(self.BLACK_KNIGHTS)])
        bishop_score = sum([1 * BISHOP_WEIGHT for _ in BitBoardChess.generate_positions_from_mask(self.WHITE_BISHOPS)]) - sum([1 * BISHOP_WEIGHT for _ in BitBoardChess.generate_positions_from_mask(self.BLACK_BISHOPS)])
        rook_score = sum([1 * ROOK_WEIGHT for _ in BitBoardChess.generate_positions_from_mask(self.WHITE_ROOKS)]) - sum([1 * ROOK_WEIGHT for _ in BitBoardChess.generate_positions_from_mask(self.BLACK_ROOKS)])
        queen_score = sum([1 * QUEEN_WEIGHT for _ in BitBoardChess.generate_positions_from_mask(self.WHITE_QUEENS)]) - sum([1 * QUEEN_WEIGHT for _ in BitBoardChess.generate_positions_from_mask(self.BLACK_QUEENS)])

        log.debug(f'{pawn_score} {knight_score} {bishop_score} {rook_score} {queen_score}')
        return pawn_score + knight_score + bishop_score + rook_score + queen_score

    def depth_search(self, depth: int) -> int:
        """
        """
        if depth == 0:
            return self.evaluate()

        best_score = -inf

        for move in self.generate_all_possible_moves(piece_color=self.PLAYER_TURN)[0]:
            self.save_state()
            self.apply_move(move=move)
            self.PLAYER_TURN = BitBoardChess.WHITE if self.PLAYER_TURN == BitBoardChess.BLACK else BitBoardChess.BLACK
            evaluation = self.depth_search(depth=depth - 1)
            self.load_state()
            best_score = max(evaluation, best_score)

        return best_score

    def shannon_number(self, depth_limit: int, player_turn: int, current_depth: int = 0, fen_string_to_test: str = '', is_capture: bool = False, is_en_passant: bool = False, is_castle: bool = False, is_promotion: bool = False) -> int:
        """
        """

        if depth_limit == current_depth:
            all_move_details['Moves'] += 1
            all_move_details['Captures'] += 1 if is_capture else 0
            all_move_details['En Passant'] += 1 if is_en_passant else 0
            all_move_details['Castles'] += 1 if is_castle else 0
            all_move_details['Promotions'] += 1 if is_promotion else 0
            return 1

        shannon = 0
        all_possible_moves = self.generate_all_legal_moves(piece_color=player_turn)

        if current_depth == 0:
            progress_number_of_moves = len(all_possible_moves)
            correct_results = get_stockfish_data(fen_string=fen_string_to_test, shannon_depth=depth_limit)
            start_time = datetime.now()
            print(f'Starting Shannon number with a depth of {depth_limit}...')

        next_player = BitBoardChess.WHITE if player_turn == BitBoardChess.BLACK else BitBoardChess.BLACK
        for idx, move in enumerate(all_possible_moves):
            if current_depth == 0:
                print(f'{datetime.now()} - Analyzing {move} #{idx + 1} out of {progress_number_of_moves}... ', end='', flush=True)

            self.save_state()
            self.apply_move(move)
            next_depth_shannon_number = self.shannon_number(depth_limit=depth_limit, player_turn=next_player, current_depth=current_depth + 1, is_capture=move.is_capture, is_en_passant=move.is_en_passant, is_castle=move.is_castle, is_promotion=move.is_promotion)
            shannon += next_depth_shannon_number

            if current_depth == 0:
                all_move_history[move] = next_depth_shannon_number

            self.load_state()
            if current_depth == 0:
                print(f'{next_depth_shannon_number:0,} vs Stockfish {correct_results.get(move, -1):0,}  //   ETA {start_time + ((datetime.now() - start_time) / ((idx + 1)/progress_number_of_moves))}')
                if correct_results.get(move, -1) != next_depth_shannon_number:
                    print('******** ' + bcolors.CREDBG + '!!! NOPE !!!' + bcolors.ENDC + ' *************')
                    break

        if current_depth == 0:
            match = True
            # If we get this far, make sure the dictionaries match
            for k, v in correct_results.items():
                if all_move_history.get(k, -1) != v:
                    print(f'MY RESULTS FOR {k} {all_move_history.get(k, -1):0,}   STOCKFISH RESULTS FOR {k} {v:0,}')
                    match = False
            for k, v in all_move_history.items():
                if correct_results.get(k, -1) != v:
                    print(f'MY RESULTS FOR {k} {v:0,}   STOCKFISH RESULTS FOR {k} {correct_results.get(k, -1):0,}')
                    match = False
            if match:
                print('******** ' + bcolors.CGREEN + ' LOOKS GOOD ' + bcolors.ENDC + '*************')
            else:
                print('******** ' + bcolors.CREDBG + '!!! NOPE !!!' + bcolors.ENDC + ' *************')

            print()
            print('************** MY MOVES ********************')
            print()
            print(all_move_details)
        return shannon


def shannon_test_starting_position():
    chess_board = BitBoardChess()
    fen_string = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    chess_board.load_from_fen_string(fen_string=fen_string)
    chess_board.print_board()
    shannon_depth = 4
    # all_move_history.clear()
    start_time = datetime.now()
    print(f'{chess_board.shannon_number(depth_limit=shannon_depth, player_turn=BitBoardChess.WHITE, fen_string_to_test=fen_string):0,} took {datetime.now() - start_time}.')
    print()


def shannon_test_castling():
    chess_board = BitBoardChess()
    fen_string = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
    # fen_string = "r3k2r/8/8/8/8/8/8/R3K1R1 b Qkq - 1 1"
    # fen_string = "r3k3/8/8/8/8/8/8/R3K1Rr w Qq - 2 2"
    # fen_string = "r3k3/8/8/8/8/8/8/R3KR1r b Qq - 3 2"
    chess_board.load_from_fen_string(fen_string=fen_string)
    chess_board.print_board()
    shannon_depth = 5
    # all_move_history.clear()
    start_time = datetime.now()
    print(f'{chess_board.shannon_number(depth_limit=shannon_depth, player_turn=BitBoardChess.WHITE, fen_string_to_test=fen_string):0,} took {datetime.now() - start_time}.')


def shannon_test_promotions():
    chess_board = BitBoardChess()
    fen_string = "2n1k3/1P6/6P/8/8/8/1p4p1/4K3 w - - 0 1"
    # fen_string = "r3k2r/8/8/8/8/8/8/R3K1R1 b Qkq - 1 1"
    # fen_string = "r3k3/8/8/8/8/8/8/R3K1Rr w Qq - 2 2"
    # fen_string = "r3k3/8/8/8/8/8/8/R3KR1r b Qq - 3 2"
    chess_board.load_from_fen_string(fen_string=fen_string)
    chess_board.print_board()
    shannon_depth = 1
    # all_move_history.clear()
    start_time = datetime.now()
    print(f'{chess_board.shannon_number(depth_limit=shannon_depth, player_turn=BitBoardChess.WHITE, fen_string_to_test=fen_string):0,} took {datetime.now() - start_time}.')


def get_stockfish_data(fen_string: str, shannon_depth: int) -> dict:
    print('Getting Stockfish data...')
    import subprocess
    import time
    engine = subprocess.Popen('stockfish_13_win_x64.exe', universal_newlines=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    time.sleep(1)
    engine.stdin.write("isready\n")
    engine.stdin.flush()
    # print("\nengine:")

    while True:
        text = engine.stdout.readline().strip()
        # print(text)
        if text == "readyok":
            break

    engine.stdin.write(f"position fen {fen_string}\n")
    engine.stdin.flush()
    time.sleep(0.25)
    engine.stdin.write(f"go perft {shannon_depth}\n")
    engine.stdin.flush()
    time.sleep(0.5)

    # print("\nengine:")
    results = []
    while True:
        text = engine.stdout.readline().strip()
        # print(text)
        if "Nodes searched: " in text:
            break
        if text != "":
            results.append(text)
    # print(results)
    stockfish_results = {}
    for result in results:
        k, v = result.split(': ')
        stockfish_results[k] = int(v)
    # for key, value in sorted(stockfish_results.items(), key=lambda x: x[0]):
    #     print("{} : {}".format(key, value))
    engine.terminate()

    return stockfish_results


if __name__ == '__main__':
    # shannon_test_starting_position()
    # shannon_test_castling()
    shannon_test_promotions()

    # import csv
    # with open('bitboard_version.csv', 'w', newline='') as f:
    #     writer = csv.writer(f)
    #     writer.writerows(total_moves)
    # 1 	20
    # 2 	400
    # 3 	8,902
    # 4 	197,281
    # 5 	4,865,609
    # 6 	119,060,324
    # 7 	3,195,901,860
    # 8 	84,998,978,956
    # 9 	2,439,530,234,167
    # 10 	69,352,859,712,417
