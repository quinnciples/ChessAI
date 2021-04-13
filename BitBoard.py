"""
TO-DO
    Modify the up-down movement code to use a "movement mask" argument, and isolate this code
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
        self.WHITE_PAWNS =   0b00000000_00000000_00000000_00000000_00000000_00000000_11111111_00000000
        self.WHITE_ROOKS =   0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_10000001
        self.WHITE_KNIGHTS = 0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_01000010
        self.WHITE_BISHOPS = 0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00100100
        self.WHITE_QUEENS =  0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00010000
        self.WHITE_KINGS =   0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00001000

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
        board_position_reversed = 63 - board_position

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

        return move_mask

    def process_pawn_move(self, board_position: int, piece_color: int) -> int:
        """
        Handles calculating all possible destination squares for the pawn piece.
        Assumes a one-square vertical move by default, unless that square is occupied by any piece.
        If a one-square move is possible, and the pawn is still on its starting rank,
        an initial move of 2 squares is available if this destination square is also unoccupied.
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
            # Moving up the board, but not to the last rank -- promotion is handled separately
            move_mask = (initial_position >> 8) & BitBoardChess.SIXTY_FOUR_BIT_MASK & self.EMPTY_SQUARES & ~BitBoardChess.RANK_1
            if move_mask > 0 and initial_position & BitBoardChess.RANK_7:
                # We started on the initial rank, and we were able to move 1 square -- let's try for two.
                move_mask |= (initial_position >> 16) & BitBoardChess.SIXTY_FOUR_BIT_MASK & self.EMPTY_SQUARES & ~BitBoardChess.RANK_1

        return move_mask

    def process_pawn_capture_left(self, board_position: int, piece_color: int) -> int:
        """
        Handles calculating all possible destination squares for the king piece.
        Utilizes KING_SPAN to determine which squares are in reach, and the
        span is bit-shifted across the board to the king's location
        """
        pass

    def process_pawn_capture_right(self, board_position: int, piece_color: int) -> int:
        """
        Handles calculating all possible destination squares for the king piece.
        Utilizes KING_SPAN to determine which squares are in reach, and the
        span is bit-shifted across the board to the king's location
        """
        pass

    def process_pawn_promotion(self, board_position: int, piece_color: int) -> int:
        """
        Handles calculating all possible destination squares for the king piece.
        Utilizes KING_SPAN to determine which squares are in reach, and the
        span is bit-shifted across the board to the king's location
        """
        pass

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

    def generate_all_possible_moves(self, piece_color: int) -> list:
        all_possible_moves = []
        # ******************** Pawns ********************
        # Pawn movement
        for pawn_square in BitBoardChess.generate_positions_from_mask(self.WHITE_PAWNS):
            destinations = self.process_pawn_move(pawn_square, piece_color=piece_color)
            if destinations:
                for destination in BitBoardChess.generate_positions_from_mask(destinations):
                    all_possible_moves.append(f'{BitBoardChess.convert_position_to_algebraic_notation(pawn_square)}{BitBoardChess.convert_position_to_algebraic_notation(destination)}')

        # ******************** Knights ********************
        for knight_square in BitBoardChess.generate_positions_from_mask(self.WHITE_KNIGHTS):
            destinations = self.process_knight_move(knight_square, piece_color=piece_color)
            if destinations:
                for destination in BitBoardChess.generate_positions_from_mask(destinations):
                    all_possible_moves.append(f'{BitBoardChess.convert_position_to_algebraic_notation(knight_square)}{BitBoardChess.convert_position_to_algebraic_notation(destination)}')

        # ******************** Bishops ********************
        for bishop_square in BitBoardChess.generate_positions_from_mask(self.WHITE_BISHOPS):
            destinations = self.process_bishop_move(bishop_square, piece_color=piece_color)
            if destinations:
                for destination in BitBoardChess.generate_positions_from_mask(destinations):
                    all_possible_moves.append(f'{BitBoardChess.convert_position_to_algebraic_notation(bishop_square)}{BitBoardChess.convert_position_to_algebraic_notation(destination)}')

        # ******************** Rooks ********************
        for rook_square in BitBoardChess.generate_positions_from_mask(self.WHITE_ROOKS):
            destinations = self.process_rook_move(rook_square, piece_color=piece_color)
            if destinations:
                for destination in BitBoardChess.generate_positions_from_mask(destinations):
                    all_possible_moves.append(f'{BitBoardChess.convert_position_to_algebraic_notation(bishop_square)}{BitBoardChess.convert_position_to_algebraic_notation(destination)}')

        # ******************** Queens ********************
        for queen_square in BitBoardChess.generate_positions_from_mask(self.WHITE_QUEENS):
            destinations = self.process_queen_move(queen_square, piece_color=piece_color)
            if destinations:
                for destination in BitBoardChess.generate_positions_from_mask(destinations):
                    all_possible_moves.append(f'{BitBoardChess.convert_position_to_algebraic_notation(queen_square)}{BitBoardChess.convert_position_to_algebraic_notation(destination)}')

        print(all_possible_moves)


if __name__ == '__main__':
    # for move in range(64):
    #     process_knight_move(move)

    chess_board = BitBoardChess()
    # chess_board.process_knight_move(board_position=1, piece_color=BitBoardChess.BLACK)
    # BitBoardChess.print_bitboard(chess_board.process_pawn_move(board_position=10, piece_color=BitBoardChess.BLACK))
    # BitBoardChess.print_bitboard(chess_board.process_pawn_move(board_position=50, piece_color=BitBoardChess.WHITE))
    chess_board.generate_all_possible_moves(piece_color=BitBoardChess.WHITE)

    # for position in BitBoardChess.generate_positions_from_mask(board=chess_board.BLACK_PIECES):
    #     print(BitBoardChess.convert_position_to_algebraic_notation(position))

    # for position in BitBoardChess.generate_positions_from_mask(board=chess_board.WHITE_PIECES):
    #     print(BitBoardChess.convert_position_to_algebraic_notation(position))
