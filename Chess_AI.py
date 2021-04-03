import logging
from mariadb_handler import MariaDBHandler
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s.%(msecs)03d - %(levelname)8s - %(filename)s - Function: %(funcName)20s - Line: %(lineno)4s // %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    handlers=[
                        logging.FileHandler(filename='log.txt'),
                        logging.StreamHandler(),
                        MariaDBHandler(username="alexander", password="udder1998", host="pi.hole")
                    ])
# logging.disable(level=logging.CRITICAL)
logging.info('Loaded.')


class Board:
    def __init__(self) -> None:
        self.board = [None] * 64
        self.active_color = Piece.WHITE
        self.halfmoves = 0
        self.fullmoves = 1

    def reset(self) -> None:
        for column in range(1, 9):
            self.board[Board.translatePos(row=2, column=column)] = Piece.WHITE | Piece.PAWN
            self.board[Board.translatePos(row=7, column=column)] = Piece.BLACK | Piece.PAWN

        self.board[0] = Piece.ROOK | Piece.BLACK
        self.board[7] = Piece.ROOK | Piece.BLACK
        self.board[1] = Piece.KNIGHT | Piece.BLACK
        self.board[6] = Piece.KNIGHT | Piece.BLACK
        self.board[2] = Piece.BISHOP | Piece.BLACK
        self.board[5] = Piece.BISHOP | Piece.BLACK
        self.board[3] = Piece.QUEEN | Piece.BLACK
        self.board[4] = Piece.KING | Piece.BLACK

        self.board[56] = Piece.ROOK | Piece.WHITE
        self.board[63] = Piece.ROOK | Piece.WHITE
        self.board[57] = Piece.KNIGHT | Piece.WHITE
        self.board[62] = Piece.KNIGHT | Piece.WHITE
        self.board[58] = Piece.BISHOP | Piece.WHITE
        self.board[61] = Piece.BISHOP | Piece.WHITE
        self.board[59] = Piece.QUEEN | Piece.WHITE
        self.board[60] = Piece.KING | Piece.WHITE

    def print(self) -> None:
        print('-' * 41)
        for idx, piece in enumerate(self.board):
            print('| ' + Piece.getPieceType(piece) + ' ', end='')
            if (idx + 1) % 8 == 0:
                print('|')
                print('-' * 41)

    def generateValidMoves(self, color: int) -> list:
        for position, piece in enumerate(self.board):
            if not (piece & color):
                continue

    def getFENString(self) -> str:
        def determineCastling(board) -> str:
            castling = ''
            # White
            if board[63] & Piece.MOVED == 0 and board[63] & Piece.ROOK and board[63] & Piece.WHITE and board[60] & Piece.MOVED == 0 and board[60] & Piece.KING and board[60] & Piece.WHITE:
                castling += 'K'
            else:
                castling += ' '
            if board[56] & Piece.MOVED == 0 and board[56] & Piece.ROOK and board[56] & Piece.WHITE and board[60] & Piece.MOVED == 0 and board[60] & Piece.KING and board[60] & Piece.WHITE:
                castling += 'Q'
            else:
                castling += ' '
            # Black
            if board[7] & Piece.MOVED == 0 and board[7] & Piece.ROOK and board[7] & Piece.BLACK and board[4] & Piece.MOVED == 0 and board[4] & Piece.KING and board[4] & Piece.BLACK:
                castling += 'k'
            else:
                castling += ' '
            if board[0] & Piece.MOVED == 0 and board[0] & Piece.ROOK and board[0] & Piece.BLACK and board[4] & Piece.MOVED == 0 and board[4] & Piece.KING and board[4] & Piece.BLACK:
                castling += 'q'
            else:
                castling += ' '
            return castling

        fen = ''
        empty = 0
        for position, piece in enumerate(self.board):
            if position % 8 == 0 and position > 0:
                if empty:
                    fen += str(empty)
                    empty = 0
                fen += '/'
            if piece is None:
                empty += 1
            elif empty > 0:
                fen += str(empty)
                empty = 0
            else:
                this_piece = Piece.getPieceType(piece)
                if this_piece[0] == 'B':
                    this_piece = this_piece[1].lower()
                else:
                    this_piece = this_piece[1].upper()
                fen += this_piece
        fen += ' '
        fen += 'w' if self.active_color & Piece.WHITE else 'b'
        fen += ' '
        fen += determineCastling(self.board)
        fen += ' '
        # En Passant
        fen += '-'
        fen += ' '
        # Half moves
        fen += str(self.halfmoves)
        fen += ' '
        # Full moves
        fen += str(self.fullmoves)
        return fen

    @staticmethod
    def translatePos(row: int = 1, column: int = 1) -> int:
        position = ((9 - row - 1) * 8) + column - 1
        if position >= 0 and position < 64:
            return position
        else:
            return None


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


def main():
    p = Piece()
    colors = [128, 256]
    for col in colors:
        for piece in range(1, 7):
            p.value = (2 ** piece) + col
            print(p.value, Piece.getPieceType(p.value))

    print()
    print()

    b = Board()
    b.reset()
    b.print()
    print()
    print(b.getFENString())


if __name__ == '__main__':
    main()
