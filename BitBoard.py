"""
To do - handle pawn promotion
NEED TO MAKE SURE EN PASSANT IS HANDLED CORRECTLY - LOOK AT REAL FEN STRINGS LIKE THIS -- rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1 -- after 1 e4
Evalute function
Search function
"""

from bcolors import bcolors
from math import log2
import logging
log = logging.getLogger(__name__)


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

    BLACK_PIECE_ATTRIBUTES = ['BLACK_PAWNS', 'BLACK_KNIGHTS', 'BLACK_BISHOPS', 'BLACK_ROOKS', 'BLACK_QUEENS', 'BLACK_KINGS']
    WHITE_PIECE_ATTRIBUTES = ['WHITE_PAWNS', 'WHITE_KNIGHTS', 'WHITE_BISHOPS', 'WHITE_ROOKS', 'WHITE_QUEENS', 'WHITE_KINGS']

    PUSH_ITEMS = ['BLACK_PAWNS', 'BLACK_KNIGHTS', 'BLACK_BISHOPS', 'BLACK_ROOKS', 'BLACK_QUEENS', 'BLACK_KINGS',
                  'WHITE_PAWNS', 'WHITE_KNIGHTS', 'WHITE_BISHOPS', 'WHITE_ROOKS', 'WHITE_QUEENS', 'WHITE_KINGS',
                  'EN_PASSANT', 'CASTLING', 'FULL_MOVES', 'HALF_MOVES']

    POP_ITEMS = ['HALF_MOVES', 'FULL_MOVES', 'CASTLING', 'EN_PASSANT',
                 'WHITE_KINGS', 'WHITE_QUEENS', 'WHITE_ROOKS', 'WHITE_BISHOPS', 'WHITE_KNIGHTS', 'WHITE_PAWNS',
                 'BLACK_KINGS', 'BLACK_QUEENS', 'BLACK_ROOKS', 'BLACK_BISHOPS', 'BLACK_KNIGHTS', 'BLACK_PAWNS']

    def __init__(self) -> None:
        self.RANK_MASKS = [0] * 8
        self.FILE_MASKS = [0] * 8
        self.HV_MASKS = [0] * 64
        self.ULDR_DIAGONAL_MASKS = [0] * 64
        self.URDL_DIAGONAL_MASKS = [0] * 64
        self.CASTLING = {'K': 1, 'Q': 1, 'k': 1, 'q': 1}
        self.FULL_MOVES = 0
        self.HALF_MOVES = 0
        self.GAME_STACK = []
        self.setup_horizontal_and_vertical_masks()
        self.setup_uldr_diagonal_and_urdl_diagonal_masks()
        self.reset()

    def reset(self) -> None:
        self.WHITE_PAWNS =   0b00000000_00000000_00000000_00000000_00000000_00000000_11111111_00000000
        self.WHITE_ROOKS =   0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_10000001
        self.WHITE_KNIGHTS = 0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_01000010
        self.WHITE_BISHOPS = 0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00100100
        self.WHITE_QUEENS =  0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00010000
        self.WHITE_KINGS =   0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00001000

        self.BLACK_PAWNS =   0b00000000_11111111_00000000_00000000_00000000_00000000_00000000_00000000
        self.BLACK_ROOKS =   0b10000001_00000000_00000000_00000000_00000000_00000000_00000000_00000000
        self.BLACK_KNIGHTS = 0b01000010_00000000_00000000_00000000_00000000_00000000_00000000_00000000
        self.BLACK_BISHOPS = 0b00100100_00000000_00000000_00000000_00000000_00000000_00000000_00000000
        self.BLACK_QUEENS =  0b00010000_00000000_00000000_00000000_00000000_00000000_00000000_00000000
        self.BLACK_KINGS =   0b00001000_00000000_00000000_00000000_00000000_00000000_00000000_00000000

        self.EN_PASSANT =    0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00000000

        self.CASTLING = {'K': 1, 'Q': 1, 'k': 1, 'q': 1}

        self.FULL_MOVES = 0
        self.HALF_MOVES = 0

        self.GAME_STACK.clear()

    def clear(self) -> None:
        self.WHITE_PAWNS =   0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00000000
        self.WHITE_ROOKS =   0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00000000
        self.WHITE_KNIGHTS = 0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00000000
        self.WHITE_BISHOPS = 0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00000000
        self.WHITE_QUEENS =  0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00000000
        self.WHITE_KINGS =   0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00000000

        self.BLACK_PAWNS =   0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00000000
        self.BLACK_ROOKS =   0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00000000
        self.BLACK_KNIGHTS = 0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00000000
        self.BLACK_BISHOPS = 0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00000000
        self.BLACK_QUEENS =  0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00000000
        self.BLACK_KINGS =   0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00000000

        self.EN_PASSANT =    0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00000000

        self.CASTLING = {'K': 0, 'Q': 0, 'k': 0, 'q': 0}

        self.FULL_MOVES = 0
        self.HALF_MOVES = 0

        self.GAME_STACK.clear()

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
            for key in self.CASTLING.keys():
                if key in castling:
                    self.CASTLING[key] = 1
                else:
                    self.CASTLING[key] = 0
            log.info(f'Setting castling of {castling} to: {self.CASTLING}')

        def process_en_passant(en_passant: str) -> None:
            self.EN_PASSANT = 0
            if len(en_passant) == 2:
                en_passant_board_position = BitBoardChess.convert_algebraic_notation_to_position(en_passant)
                self.EN_PASSANT = BitBoardChess.convert_position_to_mask(en_passant_board_position)

        process_board_layout(board_string=board_string)
        process_castling(castling=castling)
        process_en_passant(en_passant=en_passant)
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

        # for square in range(64):
        #     rank = 7 - (square // 8)
        #     file = square % 8
        #     mask_value = (self.RANK_MASKS[rank] | self.FILE_MASKS[file]) & ~(1 << (63 - square))
        #     self.HV_MASKS[square] = mask_value
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

    @staticmethod
    def reverse_bits(bitboard: int) -> int:
        bits_string = f"{bitboard:064b}"
        reversed_bits_string = ''.join(bits_string[::-1])
        log.debug(f'{bits_string} -> {reversed_bits_string}')
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
        Converts a two-character algebraic notation (b2, etc) to the board position index.
        """
        algebraic_notation = algebraic_notation.lower()
        file = ord(algebraic_notation[0]) - 97
        rank = int(algebraic_notation[1])
        rank = 8 - rank
        rank *= 8
        board_position = rank + file
        return board_position

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
        move_mask = self.generate_diagonal_uldr_moves(board_position=board_position, piece_color=piece_color) | self.generate_diagonal_urdl_moves(board_position=board_position, piece_color=piece_color)
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
        else:
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

    def process_pawn_promotion(self, board_position: int, piece_color: int) -> int:
        """
        Handles calculating all possible destination squares for the pawn piece.
        Assumes a one-square vertical move by default, unless that square is occupied by any piece.
        Pawns can promote to a Queen, Rook, Bishop, or Knight.
        """
        # print(' ' + '*' * 6 + ' ' + BitBoardChess.convert_position_to_algebraic_notation(board_position) + ' ' + '*' * 6)
        initial_position = 0 | 1 << (63 - board_position)
        if (piece_color == BitBoardChess.WHITE and board_position > 15) or (piece_color == BitBoardChess.BLACK and board_position < 48):
            return None

        # Move
        if piece_color == BitBoardChess.WHITE:
            # Moving up the board, but not to the last rank -- promotion is handled separately
            move_mask = (initial_position << 8) & BitBoardChess.SIXTY_FOUR_BIT_MASK & self.EMPTY_SQUARES & BitBoardChess.RANK_8
        elif piece_color == BitBoardChess.BLACK:
            # Moving down the board, but not to the last rank -- promotion is handled separately
            move_mask = (initial_position >> 8) & BitBoardChess.SIXTY_FOUR_BIT_MASK & self.EMPTY_SQUARES & BitBoardChess.RANK_1

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

    def process_knight_move(self, board_position: int, piece_color: int) -> None:
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
        else:
            move_mask = move_mask & (~self.BLACK_PIECES)

        return move_mask

    def process_castling_moves(self, piece_color: int) -> list:
        castling_options = []
        if piece_color == BitBoardChess.WHITE:
            if self.CASTLING['K']:
                castling_options.append('O-O')
            if self.CASTLING['Q']:
                castling_options.append('O-O-O')
        elif piece_color == BitBoardChess.BLACK:
            if self.CASTLING['k']:
                castling_options.append('O-O')
            if self.CASTLING['q']:
                castling_options.append('O-O-O')
        return castling_options

    def generate_all_possible_moves(self, piece_color: int) -> list:
        all_possible_moves = []
        # ******************** Pawns ********************
        # Pawn movement
        for pawn_square in BitBoardChess.generate_positions_from_mask(self.WHITE_PAWNS if piece_color == BitBoardChess.WHITE else self.BLACK_PAWNS):
            destinations = self.process_pawn_move(pawn_square, piece_color=piece_color)
            if destinations:
                for destination in BitBoardChess.generate_positions_from_mask(destinations):
                    all_possible_moves.append(f'{BitBoardChess.convert_position_to_algebraic_notation(pawn_square)}{BitBoardChess.convert_position_to_algebraic_notation(destination)}')
        # Pawn captures - LEFT
        for pawn_square in BitBoardChess.generate_positions_from_mask(self.WHITE_PAWNS if piece_color == BitBoardChess.WHITE else self.BLACK_PAWNS):
            destinations = self.process_pawn_capture_left(pawn_square, piece_color=piece_color)
            if destinations:
                for destination in BitBoardChess.generate_positions_from_mask(destinations):
                    all_possible_moves.append(f'{BitBoardChess.convert_position_to_algebraic_notation(pawn_square)}{BitBoardChess.convert_position_to_algebraic_notation(destination)}')
        # Pawn captures - RIGHT
        for pawn_square in BitBoardChess.generate_positions_from_mask(self.WHITE_PAWNS if piece_color == BitBoardChess.WHITE else self.BLACK_PAWNS):
            destinations = self.process_pawn_capture_right(pawn_square, piece_color=piece_color)
            if destinations:
                for destination in BitBoardChess.generate_positions_from_mask(destinations):
                    all_possible_moves.append(f'{BitBoardChess.convert_position_to_algebraic_notation(pawn_square)}{BitBoardChess.convert_position_to_algebraic_notation(destination)}')
        # Pawn captures - En Passant
        if self.EN_PASSANT:
            for pawn_square in BitBoardChess.generate_positions_from_mask(self.WHITE_PAWNS if piece_color == BitBoardChess.WHITE else self.BLACK_PAWNS):
                destinations = self.process_pawn_capture_en_passant(pawn_square, piece_color=piece_color)
                if destinations:
                    for destination in BitBoardChess.generate_positions_from_mask(destinations):
                        all_possible_moves.append(f'{BitBoardChess.convert_position_to_algebraic_notation(pawn_square)}{BitBoardChess.convert_position_to_algebraic_notation(destination)} EN PASSANT BITCHES!!!')
        # Promotion
        for pawn_square in BitBoardChess.generate_positions_from_mask(self.WHITE_PAWNS if piece_color == BitBoardChess.WHITE else self.BLACK_PAWNS):
            destinations = self.process_pawn_promotion(pawn_square, piece_color=piece_color)
            if destinations:
                for destination in BitBoardChess.generate_positions_from_mask(destinations):
                    all_possible_moves.append(f'{BitBoardChess.convert_position_to_algebraic_notation(pawn_square)}{BitBoardChess.convert_position_to_algebraic_notation(destination)}->Q')
                    all_possible_moves.append(f'{BitBoardChess.convert_position_to_algebraic_notation(pawn_square)}{BitBoardChess.convert_position_to_algebraic_notation(destination)}->R')
                    all_possible_moves.append(f'{BitBoardChess.convert_position_to_algebraic_notation(pawn_square)}{BitBoardChess.convert_position_to_algebraic_notation(destination)}->B')
                    all_possible_moves.append(f'{BitBoardChess.convert_position_to_algebraic_notation(pawn_square)}{BitBoardChess.convert_position_to_algebraic_notation(destination)}->N')

        # ******************** Knights ********************
        for knight_square in BitBoardChess.generate_positions_from_mask(self.WHITE_KNIGHTS if piece_color == BitBoardChess.WHITE else self.BLACK_KNIGHTS):
            destinations = self.process_knight_move(knight_square, piece_color=piece_color)
            if destinations:
                for destination in BitBoardChess.generate_positions_from_mask(destinations):
                    all_possible_moves.append(f'{BitBoardChess.convert_position_to_algebraic_notation(knight_square)}{BitBoardChess.convert_position_to_algebraic_notation(destination)}')

        # ******************** Bishops ********************
        for bishop_square in BitBoardChess.generate_positions_from_mask(self.WHITE_BISHOPS if piece_color == BitBoardChess.WHITE else self.BLACK_BISHOPS):
            destinations = self.process_bishop_move(bishop_square, piece_color=piece_color)
            if destinations:
                for destination in BitBoardChess.generate_positions_from_mask(destinations):
                    all_possible_moves.append(f'{BitBoardChess.convert_position_to_algebraic_notation(bishop_square)}{BitBoardChess.convert_position_to_algebraic_notation(destination)}')

        # ******************** Rooks ********************
        for rook_square in BitBoardChess.generate_positions_from_mask(self.WHITE_ROOKS if piece_color == BitBoardChess.WHITE else self.BLACK_ROOKS):
            destinations = self.process_rook_move(rook_square, piece_color=piece_color)
            if destinations:
                for destination in BitBoardChess.generate_positions_from_mask(destinations):
                    all_possible_moves.append(f'{BitBoardChess.convert_position_to_algebraic_notation(rook_square)}{BitBoardChess.convert_position_to_algebraic_notation(destination)}')

        # ******************** Queens ********************
        for queen_square in BitBoardChess.generate_positions_from_mask(self.WHITE_QUEENS if piece_color == BitBoardChess.WHITE else self.BLACK_QUEENS):
            destinations = self.process_queen_move(queen_square, piece_color=piece_color)
            if destinations:
                for destination in BitBoardChess.generate_positions_from_mask(destinations):
                    all_possible_moves.append(f'{BitBoardChess.convert_position_to_algebraic_notation(queen_square)}{BitBoardChess.convert_position_to_algebraic_notation(destination)}')

        # ******************** King ********************
        for king_square in BitBoardChess.generate_positions_from_mask(self.WHITE_KINGS if piece_color == BitBoardChess.WHITE else self.BLACK_KINGS):
            destinations = self.process_king_move(king_square, piece_color=piece_color)
            if destinations:
                for destination in BitBoardChess.generate_positions_from_mask(destinations):
                    all_possible_moves.append(f'{BitBoardChess.convert_position_to_algebraic_notation(king_square)}{BitBoardChess.convert_position_to_algebraic_notation(destination)}')

        # ******************** Castling ********************
        # castling_options = self.process_castling_moves(piece_color=piece_color)
        # for castling_option in castling_options:
        #     all_possible_moves.append(f'{castling_option}')

        log.info(f"""{len(all_possible_moves)} moves generated for {"WHITE" if piece_color == BitBoardChess.WHITE else "BLACK"}: {all_possible_moves}""")
        return all_possible_moves

    def apply_move(self, move: str) -> None:
        """
        Do I need the capture checks? Can I just & ~ the whole thing?
        """
        start_square = BitBoardChess.convert_algebraic_notation_to_position(move[0:2])
        end_square = BitBoardChess.convert_algebraic_notation_to_position(move[2:])
        start_mask = BitBoardChess.convert_position_to_mask(start_square)
        end_mask = BitBoardChess.convert_position_to_mask(end_square)
        self.EN_PASSANT = 0

        if self.WHITE_PIECES & start_mask:
            piece_color = BitBoardChess.WHITE
            for PIECE_BOARD in BitBoardChess.WHITE_PIECE_ATTRIBUTES:
                if self.__getattribute__(PIECE_BOARD) & start_mask:
                    log.debug(f'Found WHITE piece in {PIECE_BOARD}.')
                    self.__setattr__(PIECE_BOARD, self.__getattribute__(PIECE_BOARD) & ~start_mask)
                    self.__setattr__(PIECE_BOARD, self.__getattribute__(PIECE_BOARD) | end_mask)
                    break

            if self.WHITE_PAWNS & end_mask and ((end_mask >> 16) & start_mask):
                self.EN_PASSANT = (end_mask >> 8)
                log.debug(f'En Passant move detected: {move}.')

            # Check for captures
            if self.BLACK_PIECES & end_mask:
                for CAPTURE_BOARD in BitBoardChess.BLACK_PIECE_ATTRIBUTES:
                    if self.__getattribute__(CAPTURE_BOARD) & end_mask:
                        self.__setattr__(CAPTURE_BOARD, self.__getattribute__(CAPTURE_BOARD) & ~end_mask)
                        log.debug(f'Found BLACK piece being captured in {CAPTURE_BOARD}.')

        elif self.BLACK_PIECES & start_mask:
            piece_color = BitBoardChess.BLACK
            for PIECE_BOARD in BitBoardChess.BLACK_PIECE_ATTRIBUTES:
                if self.__getattribute__(PIECE_BOARD) & start_mask:
                    log.debug(f'Found BLACK piece in {PIECE_BOARD}.')
                    self.__setattr__(PIECE_BOARD, self.__getattribute__(PIECE_BOARD) & ~start_mask)
                    self.__setattr__(PIECE_BOARD, self.__getattribute__(PIECE_BOARD) | end_mask)
                    break

            if self.BLACK_PAWNS & end_mask and ((end_mask << 16) & start_mask):
                self.EN_PASSANT = (end_mask << 8)
                log.debug(f'En Passant move detected: {move}.')

            # Check for captures
            if self.WHITE_PIECES & end_mask:
                for CAPTURE_BOARD in BitBoardChess.WHITE_PIECE_ATTRIBUTES:
                    if self.__getattribute__(CAPTURE_BOARD) & end_mask:
                        self.__setattr__(CAPTURE_BOARD, self.__getattribute__(CAPTURE_BOARD) & ~end_mask)
                        log.debug(f'Found WHITE piece being captured in {CAPTURE_BOARD}.')

        else:
            raise Exception('Move not found on board.')

        return

    def save_state(self) -> None:
        # board_state = tuple(self.__getattribute__(attribute) for attribute in BitBoardChess.PUSH_ITEMS)
        board_state = {attribute: self.__getattribute__(attribute) for attribute in BitBoardChess.PUSH_ITEMS}
        self.GAME_STACK.append(board_state)      

    def load_state(self) -> None:
        board_state = self.GAME_STACK.pop()
        # for idx, item in enumerate(BitBoardChess.PUSH_ITEMS):
        #     self.__setattr__(item, board_state[idx])
        for attribute, value in board_state.items():
            self.__setattr__(attribute, value)



if __name__ == '__main__':
    chess_board = BitBoardChess()
    chess_board.print_board()
    chess_board.generate_all_possible_moves(piece_color=BitBoardChess.WHITE)
    chess_board.generate_all_possible_moves(piece_color=BitBoardChess.BLACK)
    chess_board.apply_move('e2e4')
    chess_board.print_board()
    BitBoardChess.print_bitboard(chess_board.EN_PASSANT)
    chess_board.clear()
    chess_board.WHITE_PAWNS = 0b00000000_00000000_00000000_00000000_00000000_00000000_00001000_00000000
    chess_board.BLACK_PAWNS = 0b00000000_10010000_00000000_00000000_00000000_00000000_00000000_00000000
    chess_board.print_board()
    chess_board.apply_move('e2e4')
    chess_board.apply_move('a7a6')
    chess_board.apply_move('e4e5')
    chess_board.apply_move('d7d5')
    chess_board.print_board()
    # BitBoardChess.print_bitboard(chess_board.EN_PASSANT)
    print(chess_board.generate_all_possible_moves(piece_color=BitBoardChess.WHITE))
    # chess_board.save_state()
    # print(chess_board.GAME_STACK)
    # chess_board.WHITE_PAWNS = 0b00000000_00000000_00000000_00000000_00000000_11110000_00111100_00001111
    # chess_board.BLACK_PAWNS = 0b11111111_10101010_01010101_00000000_00000000_00000000_00000000_00000000
    # chess_board.print_board()
    # chess_board.load_state()
    # print(chess_board.GAME_STACK)
    # chess_board.print_board()

    # chess_board.apply_move('e7e5')
    # chess_board.print_board()
    # chess_board.apply_move('d4e5')
    # chess_board.print_board()
    # chess_board.clear()
    # chess_board.load_from_fen_string("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1")
    # chess_board.print_board()
    # BitBoardChess.print_bitboard(chess_board.EN_PASSANT)
    # # https://www.chessprogramming.org/Encoding_Moves
    # chess_board.load_from_fen_string(fen_string="3Q4/1Q4Q1/4Q3/2Q4R/Q4Q2/3Q4/1Q4Rp/1K1BBNNk w - - 0 1")
    # chess_board.print_board()
    # chess_board.generate_all_possible_moves(piece_color=BitBoardChess.WHITE)  # Looking for 218 here
    # chess_board.load_from_fen_string(fen_string="R6R/3Q4/1Q4Q1/4Q3/2Q4Q/Q4Q2/pp1Q4/kBNN1KB1 w - - 0 1")
    # chess_board.print_board()
    # chess_board.generate_all_possible_moves(piece_color=BitBoardChess.WHITE)  # Looking for 218 here
    # chess_board.reset()
    # color = BitBoardChess.WHITE
    # for turns in range(20):
    #     moves = chess_board.generate_all_possible_moves(piece_color=color)
    #     if moves:
    #         move = random.choice(moves)
    #         chess_board.apply_move(move, piece_color=color)
    #     color = BitBoardChess.WHITE if color == BitBoardChess.BLACK else BitBoardChess.BLACK
    # chess_board.print_board()
    # print(turns + 1)


    # chess_board.reset()
    # for move in chess_board.generate_all_possible_moves(piece_color=BitBoardChess.WHITE):
    #     print(move)
    #     chess_board.apply_move(move, piece_color=BitBoardChess.WHITE)
    #     chess_board.print_board()
    #     chess_board.reset()
