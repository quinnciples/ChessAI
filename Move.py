from datetime import datetime
from math import log2
import logging
log = logging.getLogger(__name__)


class Move:
    NONE = 0
    PAWN = 1
    KNIGHT = 2
    BISHOP = 4
    ROOK = 8
    QUEEN = 16
    KING = 32

    def __init__(self, piece_type: int, starting_square: int = 0, ending_square: int = 0, is_capture: bool = False, is_en_passant: bool = False, is_check: bool = False, is_promotion: bool = False, is_castle: bool = False, extra_piece_info: int = 0):
        self.starting_square = starting_square
        self.ending_square = ending_square
        self.is_capture = is_capture
        self.is_en_passant = is_en_passant
        self.is_check = is_check
        self.is_promotion = is_promotion
        self.is_castle = is_castle
        self.piece_type = piece_type
        self.extra_piece_info = extra_piece_info  # Stores type of piece being promoted to, captured, or direction of castling
        self._ufci_format = None

    def __str__(self):
        return self.ufci_format
        
            

    """
    __hash__, __eq__, __ne__ probably need to be looked at later
    to determine if objects are truly identical to each other.
    """

    def __hash__(self):
        return hash(self.ufci_format)

    def __eq__(self, other):
        if isinstance(other, str):
            return self.ufci_format == other
        elif isinstance(other, Move):
            return self.starting_square == other.starting_square and self.ending_square == other.ending_square

    def __ne__(self, other):
        # Not strictly necessary, but to avoid having both x==y and x!=y
        # True at the same time
        return not(self == other)

    @classmethod
    def from_ufci(cls, ufci_move: str, is_capture: bool = False, is_en_passant: bool = False, is_check: bool = False, is_promotion: bool = False, is_castle: bool = False, extra_piece_info: int = 0):
        starting_square = Move.convert_algebraic_notation_to_position(algebraic_notation=ufci_move[0:2])
        ending_square = Move.convert_algebraic_notation_to_position(algebraic_notation=ufci_move[2:])
        new_move = Move(starting_square=starting_square, ending_square=ending_square, is_capture=is_capture, is_en_passant=is_en_passant, is_check=is_check, is_promotion=is_promotion, is_castle=is_castle, extra_piece_info=extra_piece_info)
        new_move._ufci_format = ufci_move
        return new_move

    @classmethod
    def from_masks(cls, starting_mask: int, ending_mask: int, is_capture: bool = False, is_en_passant: bool = False, is_check: bool = False, is_promotion: bool = False, is_castle: bool = False, extra_piece_info: int = 0):
        starting_square = Move.convert_mask_to_position(board=starting_mask)
        ending_square = Move.convert_mask_to_position(board=ending_mask)
        return Move(starting_square=starting_square, ending_square=ending_square, is_capture=is_capture, is_en_passant=is_en_passant, is_check=is_check, is_promotion=is_promotion, is_castle=is_castle, extra_piece_info=extra_piece_info)

    @staticmethod
    def convert_algebraic_notation_to_position(algebraic_notation: str) -> int:
        """
        Converts a two-character algebraic notation (b2, c4, etc) to the board position index.
        """
        file = ord(algebraic_notation.lower()[0]) - 97
        rank = 8 - int(algebraic_notation[1])
        return (rank * 8) + file

    @staticmethod
    def convert_mask_to_position(board: int) -> int:
        bit_value = board & ~(board - 1)
        return 63 - int(log2(bit_value))

    @property
    def starting_mask(self) -> int:
        return 1 << (63 - self.starting_square)

    @property
    def ending_mask(self) -> int:
        return 1 << (63 - self.ending_square)

    @property
    def ufci_format(self) -> str:
        if self._ufci_format is not None:
            return self._ufci_format
        else:
            start_rank = 8 - (self.starting_square // 8)
            start_file = self.starting_square % 8 + 1
            start = chr(97 + start_file - 1) + str(start_rank)

            end_rank = 8 - (self.ending_square // 8)
            end_file = self.ending_square % 8 + 1
            end = chr(97 + end_file - 1) + str(end_rank)
            self._ufci_format = start + end

            if self.is_promotion:
                if self.extra_piece_info == Move.KNIGHT:
                    suffix = 'n'
                elif self.extra_piece_info == Move.BISHOP:
                    suffix = 'b'
                elif self.extra_piece_info == Move.ROOK:
                    suffix = 'r'
                elif self.extra_piece_info == Move.QUEEN:
                    suffix = 'q'
                self._ufci_format += suffix

        return self._ufci_format

    @property
    def estimated_score(self) -> int:
        return 0


if __name__ == '__main__':
    base_move = Move(2, 24)
    print(base_move.starting_square)
    print(base_move.ending_square)
    print(base_move.ufci_format)
    print(base_move.starting_mask)
    print(base_move.ending_mask)

    ufci_move = Move.from_ufci(ufci_move='c8a5')
    print(ufci_move.starting_square)
    print(ufci_move.ending_square)
    print(ufci_move.ufci_format)
    print(ufci_move.starting_mask)
    print(ufci_move.ending_mask)

    mask_move = Move.from_masks(starting_mask=2305843009213693952, ending_mask=549755813888)
    print(mask_move.starting_square)
    print(mask_move.ending_square)
    print(mask_move.ufci_format)
    print(mask_move.starting_mask)
    print(mask_move.ending_mask)

    print(base_move == ufci_move == mask_move)

    print('Creating objects...')
    objects = [Move.from_ufci('a4d3') for x in range(10_000_000)]
    print('Creating objects... Done.')
    start_time = datetime.now()
    for obj in objects:
        obj.ufci_format
    print(datetime.now() - start_time)

    start_time = datetime.now()
    for obj in objects:
        obj.ufci_format
    print(datetime.now() - start_time)
