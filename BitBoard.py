from bcolors import bcolors
import logging
log = logging.getLogger(__name__)


class BitBoardChess:

    SIXTY_FOUR_BIT_MASK = 0b1111111111111111111111111111111111111111111111111111111111111111
    KNIGHT_SPAN = 0b0000000000000000000000000000101000010001000000000001000100001010
    KNIGHT_SQUARE = 45
    FILE_AB = 0b1100000011000000110000001100000011000000110000001100000011000000
    FILE_GH = 0b0000001100000011000000110000001100000011000000110000001100000011
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

    def __init__(self) -> None:
        self.RANK_MASKS = [0] * 8
        self.FILE_MASKS = [0] * 8
        self.HV_MASKS = [0] * 64
        self.setup_horizontal_and_vertical_masks()
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
        rank_base = 0b11111111
        for rank in range(8):    
            self.RANK_MASKS[rank] = (0 | (rank_base << (rank * 8))) & BitBoardChess.SIXTY_FOUR_BIT_MASK
            BitBoardChess.print_bitboard(self.RANK_MASKS[rank])

        file_base_mask = 0b1000000010000000100000001000000010000000100000001000000010000000
        for file in range(8):
            self.FILE_MASKS[file] = (file_base_mask >> file) & BitBoardChess.SIXTY_FOUR_BIT_MASK
            BitBoardChess.print_bitboard(self.FILE_MASKS[file])

        for square in range(64):
            rank = 7 - (square // 8)
            file = square % 8
            mask_value = (self.RANK_MASKS[rank] | self.FILE_MASKS[file]) & ~(1 << (63 - square))
            self.HV_MASKS[square] = mask_value
            BitBoardChess.print_bitboard(self.HV_MASKS[square])


    @property
    def WHITE_PIECES(self) -> int:
        return self.WHITE_PAWNS | self.WHITE_KNIGHTS | self.WHITE_BISHOPS | self.WHITE_ROOKS | self.WHITE_QUEENS | self.WHITE_KINGS

    @property
    def BLACK_PIECES(self) -> int:
        return self.BLACK_PAWNS | self.BLACK_KNIGHTS | self.BLACK_BISHOPS | self.BLACK_ROOKS | self.BLACK_QUEENS | self.BLACK_KINGS

    @property
    def ALL_PIECES(self) -> int:
        return self.WHITE_PIECES | self.BLACK_PIECES

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


def process_knight_move(knight_position: int) -> None:
    print(' ' + '*' * 6 + ' ' + algebraic_notation(knight_position) + ' ' + '*' * 6)
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


def algebraic_notation(position: int) -> str:
    rank = 8 - (position // 8)
    file = position % 8 + 1
    file_str = chr(97 + file - 1)
    rank_str = str(rank)
    return file_str + rank_str


for move in range(1):
    process_knight_move(move)

chess_board = BitBoardChess()
# BitBoardChess.print_bitboard(chess_board.WHITE_PIECES)
# BitBoardChess.print_bitboard(chess_board.BLACK_PIECES)
# BitBoardChess.print_bitboard(chess_board.ALL_PIECES)
# print()
# s = 2 ** (63 - 28)  # 35
# occupied = chess_board.ALL_PIECES | s  | (2 ** 38)
# BitBoardChess.print_bitboard(occupied)
# left = occupied ^ (occupied - (2 * s))
# # left = (left & BitBoardChess.RANK_1 & BitBoardChess.FILE_E) | (left & BitBoardChess.RANK_2 & BitBoardChess.FILE_E) | (left & BitBoardChess.RANK_3 & BitBoardChess.FILE_E) | (left & BitBoardChess.RANK_4 & BitBoardChess.FILE_E) | (left & BitBoardChess.RANK_5) | (left & BitBoardChess.RANK_6 & BitBoardChess.FILE_E) | (left & BitBoardChess.RANK_7 & BitBoardChess.FILE_E) | (left & BitBoardChess.RANK_8 & BitBoardChess.FILE_E)
# left = left & chess_board.HV_MASKS[28]
# BitBoardChess.print_bitboard(left)
# right = occupied ^ BitBoardChess.reverse_bits((BitBoardChess.reverse_bits(occupied) - (2 * BitBoardChess.reverse_bits(s))))
# # right = (right & BitBoardChess.RANK_1 & BitBoardChess.FILE_E) | (right & BitBoardChess.RANK_2 & BitBoardChess.FILE_E) | (right & BitBoardChess.RANK_3 & BitBoardChess.FILE_E) | (right & BitBoardChess.RANK_4 & BitBoardChess.FILE_E) | (right & BitBoardChess.RANK_5) | (right & BitBoardChess.RANK_6 & BitBoardChess.FILE_E) | (right & BitBoardChess.RANK_7 & BitBoardChess.FILE_E) | (right & BitBoardChess.RANK_8 & BitBoardChess.FILE_E)
# right = right & chess_board.HV_MASKS[28]
# BitBoardChess.print_bitboard(right)
# BitBoardChess.print_bitboard(left ^ right)
