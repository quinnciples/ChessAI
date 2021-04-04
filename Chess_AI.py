import logging
from mariadb_handler import MariaDBHandler
logging.basicConfig(level=logging.DEBUG,
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
        self.clear()
        self.reset()

    @classmethod
    def fromBoard(cls, board):
        new_board = cls()
        new_board.board = board
        return new_board

    def clear(self) -> None:
        self.board = [None] * 64

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

        self.halfmoves = 0
        self.fullmoves = 1
        self.active_color = Piece.WHITE

    def print(self) -> None:
        print('-' * 41)
        for idx, piece in enumerate(self.board):
            print('| ' + Piece.getPieceType(piece) + ' ', end='')
            if (idx + 1) % 8 == 0:
                print(f'| {8 - ((idx // 8))}')
                print('-' * 41)
        print('- A -- B -- C -- D -- E -- F -- G -- H -')
        print()

    def generateValidMoves(self, color: int) -> list:
        def handlePawnMoves(board, pawnLocation):
            moves = []
            # White: -8, -16
            # Black: 8, 16
            if pawnLocation > 7 and board[pawnLocation] & Piece.WHITE:
                if board[pawnLocation] & Piece.MOVED == 0:
                    new_board = [p for p in board]
                    piece = new_board[pawnLocation] | Piece.MOVED
                    new_board[pawnLocation] = None
                    new_board[pawnLocation - 16] = piece
                    b = Board.fromBoard(board=new_board)
                    moves.append(b)
                    b.print()
                new_board = [p for p in board]
                piece = new_board[pawnLocation] | Piece.MOVED
                new_board[pawnLocation] = None
                new_board[pawnLocation - 8] = piece
                b = Board.fromBoard(board=new_board)
                moves.append(b)
                b.print()
            elif pawnLocation < 55 and board[pawnLocation] & Piece.BLACK:
                if board[pawnLocation] & Piece.MOVED == 0:
                    new_board = [p for p in board]
                    piece = new_board[pawnLocation] | Piece.MOVED
                    new_board[pawnLocation] = None
                    new_board[pawnLocation + 16] = piece
                    b = Board.fromBoard(board=new_board)
                    moves.append(b)
                    b.print()
                new_board = [p for p in board]
                piece = new_board[pawnLocation] | Piece.MOVED
                new_board[pawnLocation] = None
                new_board[pawnLocation + 8] = piece
                b = Board.fromBoard(board=new_board)
                moves.append(b)
                b.print()
            return moves

        def handleKnightMoves(board, knightLocation):
            moves = []
            piece_color = board[knightLocation] & (Piece.BLACK | Piece.WHITE)
            rank = (7 - (knightLocation // 8)) + 1
            file = (knightLocation % 8) + 1
            # knightLocation % 8 - number of spaces away from left side
            # 7 - (knightLocation % 8) - number of spaces away from right side
            # knightLocation // 8 - number of spaces away from bottom side
            # 7 - (knightLocation // 8) - number of spaces away from top side

            # Up 1 Left 2 = -10
            if rank <= 7 and file >= 3:
                movement = -10
                if board[knightLocation + movement] is None or board[knightLocation + movement] & piece_color == 0:
                    new_board = [p for p in board]
                    piece = new_board[knightLocation] | Piece.MOVED
                    new_board[knightLocation] = None
                    new_board[knightLocation + movement] = piece
                    b = Board.fromBoard(board=new_board)
                    moves.append(b)
                    b.print()
            # Up 2 Left 1 = -17
            if rank <= 6 and file >= 2:
                movement = -17
                if board[knightLocation + movement] is None or board[knightLocation + movement] & piece_color == 0:
                    new_board = [p for p in board]
                    piece = new_board[knightLocation] | Piece.MOVED
                    new_board[knightLocation] = None
                    new_board[knightLocation + movement] = piece
                    b = Board.fromBoard(board=new_board)
                    moves.append(b)
                    b.print()
            # Up 1 Right 2 = -6
            if rank <= 7 and file <= 6:
                movement = -6
                if board[knightLocation + movement] is None or board[knightLocation + movement] & piece_color == 0:
                    new_board = [p for p in board]
                    piece = new_board[knightLocation] | Piece.MOVED
                    new_board[knightLocation] = None
                    new_board[knightLocation + movement] = piece
                    b = Board.fromBoard(board=new_board)
                    moves.append(b)
                    b.print()
            # Up 2 Right 1 = -15
            if rank <= 6 and file <= 7:
                movement = -15
                if board[knightLocation + movement] is None or board[knightLocation + movement] & piece_color == 0:
                    new_board = [p for p in board]
                    piece = new_board[knightLocation] | Piece.MOVED
                    new_board[knightLocation] = None
                    new_board[knightLocation + movement] = piece
                    b = Board.fromBoard(board=new_board)
                    moves.append(b)
                    b.print()
            # Down 1 Left 2 = +6
            if rank >= 2 and file >= 3:
                movement = 6
                if board[knightLocation + movement] is None or board[knightLocation + movement] & piece_color == 0:
                    new_board = [p for p in board]
                    piece = new_board[knightLocation] | Piece.MOVED
                    new_board[knightLocation] = None
                    new_board[knightLocation + movement] = piece
                    b = Board.fromBoard(board=new_board)
                    moves.append(b)
                    b.print()
            # Down 2 Left 1 = 15
            if rank >= 3 and file >= 2:
                movement = 15
                if board[knightLocation + movement] is None or board[knightLocation + movement] & piece_color == 0:
                    new_board = [p for p in board]
                    piece = new_board[knightLocation] | Piece.MOVED
                    new_board[knightLocation] = None
                    new_board[knightLocation + movement] = piece
                    b = Board.fromBoard(board=new_board)
                    moves.append(b)
                    b.print()
            # Down 1 Right 2 = 10
            if rank >= 2 and file <= 6:
                movement = 10
                if board[knightLocation + movement] is None or board[knightLocation + movement] & piece_color == 0:
                    new_board = [p for p in board]
                    piece = new_board[knightLocation] | Piece.MOVED
                    new_board[knightLocation] = None
                    new_board[knightLocation + movement] = piece
                    b = Board.fromBoard(board=new_board)
                    moves.append(b)
                    b.print()
            # Down 2 Right 1 = +17
            if rank >= 3 and file <= 7:
                movement = 17
                if board[knightLocation + movement] is None or board[knightLocation + movement] & piece_color == 0:
                    new_board = [p for p in board]
                    piece = new_board[knightLocation] | Piece.MOVED
                    new_board[knightLocation] = None
                    new_board[knightLocation + movement] = piece
                    b = Board.fromBoard(board=new_board)
                    moves.append(b)
                    b.print()
            return moves

        moves = []
        piece_moves = []
        positions_to_move = []
        for position, piece in enumerate(self.board):
            if not piece or not (piece & color):
                continue
            positions_to_move.append(position)
        logging.debug(f'Need to handle these positions: {positions_to_move}')

        for board_position in positions_to_move:
            piece = self.board[board_position]
            if piece & Piece.PAWN:
                piece_moves = handlePawnMoves(self.board, board_position)
                for move in piece_moves:
                    moves.append(move)
            elif piece & Piece.KNIGHT:
                piece_moves = handleKnightMoves(self.board, board_position)
                for move in piece_moves:
                    moves.append(move)

        logging.info(f'Number of moves generated: {len(moves)}')
        return moves

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
        board = ''
        empty = 0
        for position, piece in enumerate(self.board):
            if position % 8 == 0 and position > 0:
                if empty:
                    board += str(empty)
                    empty = 0
                board += '/'
            if piece is None:
                empty += 1
            elif empty > 0:
                board += str(empty)
                empty = 0
            else:
                this_piece = Piece.getPieceType(piece)
                if this_piece[0] == 'B':
                    this_piece = this_piece[1].lower()
                else:
                    this_piece = this_piece[1].upper()
                board += this_piece
        fen += board
        fen += ' '
        color = 'w' if self.active_color & Piece.WHITE else 'b'
        fen += color
        fen += ' '
        castling = determineCastling(self.board)
        fen += castling
        fen += ' '
        # En Passant
        fen += '-'
        fen += ' '
        # Half moves
        fen += str(self.halfmoves)
        fen += ' '
        # Full moves
        fen += str(self.fullmoves)

        logging.debug(f'{self.board} translated to {fen}')
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
    # Board.print(b.board)
    # print()
    # print(b.getFENString())
    print()
    b.generateValidMoves(Piece.WHITE)
    b.generateValidMoves(Piece.BLACK)
    print()
    b = Board()
    b.clear()
    b.board[8] = Piece.PAWN | Piece.BLACK
    b.print()
    set_done = list()
    set_pending = [brd.board for brd in b.generateValidMoves(Piece.BLACK)]
    while set_pending:
        next_board = set_pending.pop()
        next_results = Board.fromBoard(next_board).generateValidMoves(Piece.BLACK)
        for result in next_results:
            if result.board not in set_done and result.board not in set_pending:
                set_pending.append(result.board)
        set_done.append(next_board)
    print(len(set_done))


if __name__ == '__main__':
    main()
