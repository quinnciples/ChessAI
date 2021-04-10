from collections import defaultdict
from Piece import Piece
import logging
log = logging.getLogger(__name__)


class MoveList:
    """
    Key = (Piece color | Piece type | Piece has moved, Board index)
    Value = [[Possible destination squares along path 1], [Possible destination squares along path 2], ... ]
    """

    def __init__(self) -> None:
        self.move_list = defaultdict(list)
        self.generate_possible_moves()

    def generate_possible_moves(self) -> None:
        for PIECE_TYPE in [Piece.KING, Piece.QUEEN, Piece.ROOK, Piece.BISHOP, Piece.KNIGHT, Piece.PAWN]:
            log.info(f'Processing {PIECE_TYPE} moves...')
            for PIECE_COLOR in [Piece.WHITE, Piece.BLACK]:
                for BOARD_INDEX in range(64):  # 64
                    # Up
                    up_moves = []
                    if PIECE_TYPE in [Piece.ROOK, Piece.QUEEN]:
                        for spot in range(1, 8):
                            new_square = BOARD_INDEX - (spot * 8)
                            if new_square >= 0:
                                up_moves.append(new_square)

                    elif PIECE_TYPE in [Piece.KING]:
                        new_square = BOARD_INDEX - 8
                        if new_square >= 0:
                            up_moves.append(new_square)

                    # Down
                    down_moves = []
                    if PIECE_TYPE in [Piece.ROOK, Piece.QUEEN]:
                        for spot in range(1, 8):
                            new_square = BOARD_INDEX + (spot * 8)
                            if new_square < 64:
                                down_moves.append(new_square)

                    elif PIECE_TYPE in [Piece.KING]:
                        new_square = BOARD_INDEX + 8
                        if new_square < 64:
                            down_moves.append(new_square)

                    # Left
                    left_moves = []
                    if PIECE_TYPE in [Piece.ROOK, Piece.QUEEN]:
                        for spot in range(1, 8):
                            new_square = BOARD_INDEX - spot
                            if new_square // 8 == BOARD_INDEX // 8:  # Check if we're still on the same row
                                left_moves.append(new_square)
                    elif PIECE_TYPE in [Piece.KING]:
                        new_square = BOARD_INDEX - 1
                        if new_square // 8 == BOARD_INDEX // 8:  # Check if we're still on the same row
                            left_moves.append(new_square)

                    # Right
                    right_moves = []
                    if PIECE_TYPE in [Piece.ROOK, Piece.QUEEN]:
                        for spot in range(1, 8):
                            new_square = BOARD_INDEX + spot
                            if new_square // 8 == BOARD_INDEX // 8:  # Check if we're still on the same row
                                right_moves.append(new_square)
                    elif PIECE_TYPE in [Piece.KING]:
                        new_square = BOARD_INDEX + 1
                        if new_square // 8 == BOARD_INDEX // 8:  # Check if we're still on the same row
                            right_moves.append(new_square)

                    # Up-Left diagonal
                    up_left_moves = []
                    if PIECE_TYPE in [Piece.BISHOP, Piece.QUEEN]:
                        for spot in range(1, 8):
                            new_square = BOARD_INDEX - (spot * 9)
                            if new_square >= 0 and new_square % 8 < BOARD_INDEX % 8:  # Check if we're still to the left of where we started
                                up_left_moves.append(new_square)
                    elif PIECE_TYPE in [Piece.KING]:
                        new_square = BOARD_INDEX - 9
                        if new_square >= 0 and new_square % 8 < BOARD_INDEX % 8:  # Check if we're still to the left of where we started
                            up_left_moves.append(new_square)

                    # Up-Right diagonal
                    up_right_moves = []
                    if PIECE_TYPE in [Piece.BISHOP, Piece.QUEEN]:
                        for spot in range(1, 8):
                            new_square = BOARD_INDEX - (spot * 7)
                            if new_square >= 0 and new_square % 8 > BOARD_INDEX % 8:  # Check if we're still to the right of where we started
                                up_right_moves.append(new_square)
                    elif PIECE_TYPE in [Piece.KING]:
                        new_square = BOARD_INDEX - 7
                        if new_square >= 0 and new_square % 8 > BOARD_INDEX % 8:  # Check if we're still to the left of where we started
                            up_right_moves.append(new_square)

                    # Down-Right diagonal
                    down_right_moves = []
                    if PIECE_TYPE in [Piece.BISHOP, Piece.QUEEN]:
                        for spot in range(1, 8):
                            new_square = BOARD_INDEX + (spot * 9)
                            if new_square < 64 and new_square % 8 > BOARD_INDEX % 8:  # Check if we're still to the right of where we started
                                down_right_moves.append(new_square)
                    elif PIECE_TYPE in [Piece.KING]:
                        new_square = BOARD_INDEX + 9
                        if new_square < 64 and new_square % 8 > BOARD_INDEX % 8:  # Check if we're still to the left of where we started
                            down_right_moves.append(new_square)

                    # Down-Left diagonal
                    down_left_moves = []
                    if PIECE_TYPE in [Piece.BISHOP, Piece.QUEEN]:
                        for spot in range(1, 8):
                            new_square = BOARD_INDEX + (spot * 7)
                            if new_square < 64 and new_square % 8 < BOARD_INDEX % 8:  # Check if we're still to the left of where we started
                                down_left_moves.append(new_square)
                    elif PIECE_TYPE in [Piece.KING]:
                        new_square = BOARD_INDEX + 7
                        if new_square < 64 and new_square % 8 < BOARD_INDEX % 8:  # Check if we're still to the left of where we started
                            down_left_moves.append(new_square)

                    # Knight moves
                    knight_moves = []
                    if PIECE_TYPE in [Piece.KNIGHT]:
                        knight_movements = (-15, -6, 10, 17, 15, 6, -10, -17)
                        for idx, movement in enumerate(knight_movements):
                            new_square = BOARD_INDEX + movement
                            # Check that moves which should take us to the left end up left of our starting position, and vice versa
                            if new_square >= 0 and new_square < 64 and ((idx < 4 and new_square % 8 > BOARD_INDEX % 8) or (idx >= 4 and new_square % 8 < BOARD_INDEX % 8)):
                                knight_moves.append(new_square)

                    if up_moves:
                        self.move_list[(PIECE_COLOR | PIECE_TYPE, BOARD_INDEX)].append(up_moves)
                    if down_moves:
                        self.move_list[(PIECE_COLOR | PIECE_TYPE, BOARD_INDEX)].append(down_moves)
                    if left_moves:
                        self.move_list[(PIECE_COLOR | PIECE_TYPE, BOARD_INDEX)].append(left_moves)
                    if right_moves:
                        self.move_list[(PIECE_COLOR | PIECE_TYPE, BOARD_INDEX)].append(right_moves)

                    if up_right_moves:
                        self.move_list[(PIECE_COLOR | PIECE_TYPE, BOARD_INDEX)].append(up_right_moves)
                    if down_right_moves:
                        self.move_list[(PIECE_COLOR | PIECE_TYPE, BOARD_INDEX)].append(down_right_moves)
                    if down_left_moves:
                        self.move_list[(PIECE_COLOR | PIECE_TYPE, BOARD_INDEX)].append(down_left_moves)
                    if up_left_moves:
                        self.move_list[(PIECE_COLOR | PIECE_TYPE, BOARD_INDEX)].append(up_left_moves)

                    if knight_moves:
                        for km in knight_moves:
                            self.move_list[(PIECE_COLOR | PIECE_TYPE, BOARD_INDEX)].append([km])


if __name__ == '__main__':
    movelist = MoveList()
    print(movelist.move_list)
    pass
