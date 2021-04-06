import logging
log = logging.getLogger(__name__)


class Piece:
    """
    0 / 1 - Piece is Black
    0 / 1 - Piece is White
    ---------------------------
    0 / 1 - Piece is a King
    0 / 1 - Piece is a Queen
    0 / 1 - Piece is a Rook
    0 / 1 - Piece is a Bishop
    0 / 1 - Piece is a Knight
    0 / 1 - Piece is a Pawn
    0 / 1 - Piece has been moved
    """

    LOOKUP_TABLE = {1: 'P',
                    2: 'N',
                    3: 'B',
                    4: 'R',
                    5: 'Q',
                    6: 'K'
                    }

    MOVED = 1
    PAWN = 2
    KNIGHT = 4
    BISHOP = 8
    ROOK = 16
    QUEEN = 32
    KING = 64
    WHITE = 128
    BLACK = 256

    def __init__(self) -> None:
        self.value = 0
        pass

    @staticmethod
    def getPieceType(piece: int) -> str:
        if piece is None:
            return '  '
        label = ''
        if piece & 0b100000000:  # 256
            label += 'B'
        elif piece & 0b010000000:  # 128
            label += 'W'
        else:
            return None
        for shift, piece_type in Piece.LOOKUP_TABLE.items():
            if piece >> shift & 0b1:
                label += piece_type
                return label
        else:
            return None


if __name__ == '__main__':
    pass
