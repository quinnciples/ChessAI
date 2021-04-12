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

    def __init__(self) -> None:
        self.RANK_MASKS = [0] * 8
        self.FILE_MASKS = [0] * 8
        self.HV_MASKS = [0] * 64
        self.ULDR_DIAGONAL_MASKS = [0] * 64
        self.URDL_DIAGONAL_MASKS = [0] * 64
        self.setup_horizontal_and_vertical_masks()
        self.setup_uldr_diagonal_and_urdl_diagonal_masks()
        self.reset()

    def reset(self) -> None:
        self.WHITE_PAWNS =   0b0000000000000000000000000000000000000000000000001111111100000000
        self.WHITE_ROOKS =   0b0000000000000000000000000000000000000000000000000000000010000001
        self.WHITE_KNIGHTS = 0b0000000000000000000000000000000000000000000000000000000001000010
        self.WHITE_BISHOPS = 0b0000000000000000000000000000000000000000000000000000000000100100
        self.WHITE_QUEENS =  0b0000000000000000000000000000000000000000000000000000000000010000
        self.WHITE_KINGS =   0b0000000000000000000000000000000000000000000000000000000000001000

        self.BLACK_PAWNS =   0b0000000011111111000000000000000000000000000000000000000000000000
        self.BLACK_ROOKS =   0b1000000100000000000000000000000000000000000000000000000000000000
        self.BLACK_KNIGHTS = 0b0100001000000000000000000000000000000000000000000000000000000000
        self.BLACK_BISHOPS = 0b0010010000000000000000000000000000000000000000000000000000000000
        self.BLACK_QUEENS =  0b0001000000000000000000000000000000000000000000000000000000000000
        self.BLACK_KINGS =   0b0000100000000000000000000000000000000000000000000000000000000000

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
    def algebraic_notation(board_position: int) -> str:
        rank = 8 - (board_position // 8)
        file = board_position % 8 + 1
        file_str = chr(97 + file - 1)
        rank_str = str(rank)
        return file_str + rank_str

    @staticmethod
    def convert_position_to_mask(board_position: int) -> int:
        return 1 << (63 - board_position)

    @staticmethod
    def generate_positions_from_mask(board: int) -> int:
        if board & ~(board - 1) != 0:
            bit_value = board & ~(board - 1)
            while bit_value != 0:
                yield 63 - int(log2(bit_value))
                board = board & ~bit_value
                bit_value = board & ~(board - 1)
        return

    def generate_horizontal_moves(self, board_position: int, piece_color: int) -> int:
        """
        Used to generate all available destination squares for pieces which can slide horizontally:
            --> Rook, Queen
        """
        position_mask = 1 << (63 - board_position)
        occupied = self.ALL_PIECES
        left_mask = occupied ^ (occupied - (2 * position_mask))
        left_mask = left_mask & self.RANK_MASKS[BitBoardChess.convert_position_to_rank(board_position=board_position)]
        right_mask = occupied ^ BitBoardChess.reverse_bits((BitBoardChess.reverse_bits(occupied) - (2 * BitBoardChess.reverse_bits(position_mask))))
        right_mask = right_mask & self.RANK_MASKS[BitBoardChess.convert_position_to_rank(board_position=board_position)]
        horizontal_move_mask = left_mask ^ right_mask
        if piece_color == BitBoardChess.WHITE:
            horizontal_move_mask = horizontal_move_mask & (~self.WHITE_PIECES)
        else:
            horizontal_move_mask = horizontal_move_mask & (~self.BLACK_PIECES)
        return horizontal_move_mask

    def generate_vertical_moves(self, board_position: int, piece_color: int) -> int:
        """
        Used to generate all available destination squares for pieces which can slide vertically:
            --> Rook, Queen
        """
        position_mask = 1 << (63 - board_position)
        occupied = self.ALL_PIECES & self.FILE_MASKS[BitBoardChess.convert_position_to_file(board_position=board_position)]
        up_mask = occupied ^ (occupied - (2 * position_mask))
        up_mask = up_mask & self.FILE_MASKS[BitBoardChess.convert_position_to_file(board_position=board_position)]
        down_mask = occupied ^ BitBoardChess.reverse_bits((BitBoardChess.reverse_bits(occupied) - (2 * BitBoardChess.reverse_bits(position_mask))))
        down_mask = down_mask & self.FILE_MASKS[BitBoardChess.convert_position_to_file(board_position=board_position)]
        vertical_move_mask = up_mask ^ down_mask
        if piece_color == BitBoardChess.WHITE:
            vertical_move_mask = vertical_move_mask & (~self.WHITE_PIECES)
        else:
            vertical_move_mask = vertical_move_mask & (~self.BLACK_PIECES)
        return vertical_move_mask

    def process_king_move(self, board_position: int, piece_color: int) -> int:
        """
        Handles calculating all possible destination squares for the king piece.
        Utilizes KING_SPAN to determine which squares are in reach, and the
        span is bit-shifted across the board to the king's location
        """
        # print(' ' + '*' * 6 + ' ' + BitBoardChess.algebraic_notation(board_position) + ' ' + '*' * 6)
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

        return move_mask



def process_knight_move(knight_position: int) -> None:
    """
    Handles calculating all possible destination squares for the knight piece.
    Utilizes KNIGHT_SPAN to determine which squares are in reach, and the
    span is bit-shifted across the board to the knights's location
    """
    print(' ' + '*' * 6 + ' ' + BitBoardChess.algebraic_notation(knight_position) + ' ' + '*' * 6)
    board = 0 | 1 << (63 - knight_position)
    BitBoardChess.print_bitboard(board)
    if BitBoardChess.KNIGHT_SQUARE - knight_position > 0:
        knight_board = (BitBoardChess.KNIGHT_SPAN << (BitBoardChess.KNIGHT_SQUARE - knight_position)) & BitBoardChess.SIXTY_FOUR_BIT_MASK
    else:
        knight_board = (BitBoardChess.KNIGHT_SPAN >> (knight_position - BitBoardChess.KNIGHT_SQUARE)) & BitBoardChess.SIXTY_FOUR_BIT_MASK
    if knight_position % 8 < 2:
        knight_board = knight_board & ~BitBoardChess.FILE_GH
    elif knight_position % 8 > 5:
        knight_board = knight_board & ~BitBoardChess.FILE_AB
    BitBoardChess.print_bitboard(knight_board)
    print()
    print()
    # i = knight_board & ~(knight_board - 1)
    # print_bitboard(i)
    # knight_board = knight_board & ~i
    # i = knight_board & ~(knight_board - 1)
    # print_bitboard(i)
    # knight_board = knight_board & ~i
    # i = knight_board & ~(knight_board - 1)
    # print_bitboard(i)


if __name__ == '__main__':
    # for move in range(64):
    #     process_knight_move(move)

    chess_board = BitBoardChess()

    for position in BitBoardChess.generate_positions_from_mask(board=chess_board.BLACK_PIECES):
        print(position)

    for position in BitBoardChess.generate_positions_from_mask(board=chess_board.WHITE_PIECES):
        print(position)
    # BitBoardChess.print_bitboard(chess_board.WHITE_PIECES)
    # BitBoardChess.print_bitboard(chess_board.BLACK_PIECES)
    # BitBoardChess.print_bitboard(chess_board.ALL_PIECES)
    # print()
    # print('*' * 30)
    # print()
    # chess_board.WHITE_ROOKS |= (1 << 34)
    # chess_board.BLACK_PAWNS |= (1 << 38)
    # BitBoardChess.print_bitboard(chess_board.generate_horizontal_moves(29, piece_color=BitBoardChess.WHITE))
    # BitBoardChess.print_bitboard(chess_board.generate_vertical_moves(29, piece_color=BitBoardChess.WHITE))
