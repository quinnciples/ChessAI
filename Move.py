from math import log2


class Move:
    NONE = 0
    PAWN = 1
    KNIGHT = 2
    BISHOP = 3
    ROOK = 4
    QUEEN = 5
    KING = 6

    def __init__(self, starting_square: int = 0, ending_square: int = 0, is_capture: bool = False, is_en_passant: bool = False, is_check: bool = False, is_promotion: bool = False, is_castle: bool = False, extra_piece_info: int = 0):
        self.starting_square = starting_square
        self.ending_square = ending_square
        self.is_capture = is_capture
        self.is_en_passant = is_en_passant
        self.is_check = is_check
        self.is_promotion = is_promotion
        self.is_castle = is_castle
        self.extra_piece_info = extra_piece_info  # Stores type of piece being promoted to, captured, or direction of castling

    @classmethod
    def from_ufci(cls, ufci_move: str, is_capture: bool = False, is_en_passant: bool = False, is_check: bool = False, is_promotion: bool = False, is_castle: bool = False, extra_piece_info: int = 0):
        starting_square = Move.convert_algebraic_notation_to_position(algebraic_notation=ufci_move[0:2])
        ending_square = Move.convert_algebraic_notation_to_position(algebraic_notation=ufci_move[2:])
        return Move(starting_square=starting_square, ending_square=ending_square, is_capture=is_capture, is_en_passant=is_en_passant, is_check=is_check, is_promotion=is_promotion, is_castle=is_castle, extra_piece_info=extra_piece_info)

    @classmethod
    def from_masks(cls, starting_mask: int, ending_mask: int, is_capture: bool = False, is_en_passant: bool = False, is_check: bool = False, is_promotion: bool = False, is_castle: bool = False, extra_piece_info: int = 0):
        starting_square = Move.convert_position_to_mask(board=starting_mask)
        ending_square = Move.convert_position_to_mask(board=ending_mask)
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
    def convert_position_to_mask(board: int) -> int:
        bit_value = board & ~(board - 1)
        return 63 - int(log2(bit_value))

    @property
    def starting_mask(self) -> int:
        return 1 << self.starting_square

    @property
    def ending_mask(self) -> int:
        return 1 << self.ending_square

    @property
    def ufci_format(self) -> str:
        start_rank = 8 - (self.starting_square // 8)
        start_file = self.starting_square % 8 + 1
        start = chr(97 + start_file - 1) + str(start_rank)

        end_rank = 8 - (self.ending_square // 8)
        end_file = self.ending_square % 8 + 1
        end = chr(97 + end_file - 1) + str(end_rank)

        return start + end


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
