from types import prepare_class
from Piece import Piece
from MoveList import MoveList
import logging
log = logging.getLogger(__name__)

ml = MoveList()
check_cache = {}
move_cache = {}

import sqlite3
db_file = 'moves_database.db'
log.info('Loading moves database...')
moves_database = sqlite3.connect(db_file, isolation_level=None)
db_cursor = moves_database.cursor()
log.info('Loaded')
# db_cursor.execute("DROP TABLE IF EXISTS moves;")
# db_cursor.execute("CREATE TABLE IF NOT EXISTS moves (position TEXT, move TEXT, PRIMARY KEY (position, move));")


def db_cache(func):
    def wrapper_do_twice(*args, **kwargs):
        fen_key = args[0].fen_key
        # moves_database = sqlite3.connect(db_file, isolation_level=None)
        # db_cursor = moves_database.cursor()
        cache = db_cursor.execute(f"""SELECT move FROM moves WHERE position = '{fen_key}';""").fetchall()
        if cache:
            # moves_database.close()
            returned_boards = []
            for board in cache:
                b = Board()
                b.load_from_fen_string(board[0] + ' 0 0')
                returned_boards.append(b)
            # log.info('CACHE HIT')
            return returned_boards
        result = func(*args, **kwargs)
        # log.debug('CACHE MISS')
        if result:
            items_to_insert = [(fen_key, move.fen_key) for move in result]
            # db_cursor.execute(f"INSERT INTO moves (position, move) VALUES ('{fen_key}', '{move.fen_key}');")
            db_cursor.executemany(f"INSERT INTO moves (position, move) VALUES (?, ?);", items_to_insert)
            # print(f"INSERT INTO moves (position, move) VALUES ('{fen_key}', '{move.fen_key}');")
            # moves_database.close()
        return result
    return wrapper_do_twice


class Board:
    def __init__(self) -> None:
        self.possible_moves = ml.move_list
        self.en_passant_square = ''
        self.clear()
        self.reset()

    @classmethod
    def fromBoard(cls, board):
        new_board = cls()
        new_board.board = board
        return new_board

    def clear(self) -> None:
        self.board = [None] * 64
        self.en_passant_square = ''
        self.history = []

    def reset(self) -> None:
        self.clear()
        # for column in range(1, 9):
        #     self.board[Board.translatePos(row=2, column=column)] = Piece.WHITE | Piece.PAWN
        #     self.board[Board.translatePos(row=7, column=column)] = Piece.BLACK | Piece.PAWN

        # self.board[0] = Piece.ROOK | Piece.BLACK
        # self.board[7] = Piece.ROOK | Piece.BLACK
        # self.board[1] = Piece.KNIGHT | Piece.BLACK
        # self.board[6] = Piece.KNIGHT | Piece.BLACK
        self.board[2] = Piece.BISHOP | Piece.BLACK
        self.board[5] = Piece.BISHOP | Piece.BLACK
        # self.board[3] = Piece.QUEEN | Piece.BLACK
        self.board[4] = Piece.KING | Piece.BLACK

        # self.board[56] = Piece.ROOK | Piece.WHITE
        # self.board[63] = Piece.ROOK | Piece.WHITE
        # self.board[57] = Piece.KNIGHT | Piece.WHITE
        # self.board[62] = Piece.KNIGHT | Piece.WHITE
        self.board[58] = Piece.BISHOP | Piece.WHITE
        self.board[61] = Piece.BISHOP | Piece.WHITE
        # self.board[59] = Piece.QUEEN | Piece.WHITE
        self.board[60] = Piece.KING | Piece.WHITE

        self.halfmoves = 0
        self.fullmoves = 1
        self.active_color = Piece.WHITE
        self.en_passant_square = ''

    def print(self) -> None:
        print('-' * 41)
        for idx, piece in enumerate(self.board):
            print('| ' + Piece.getPieceType(piece) + ' ', end='')
            if (idx + 1) % 8 == 0:
                print(f'| {8 - ((idx // 8))}')
                print('-' * 41)
        print('- A -- B -- C -- D -- E -- F -- G -- H -')
        print()
        print(self.fen_key)
        print()

    def isCheckForColor(self, color) -> bool:
        if (str(self.board), color) in check_cache.keys():
            return check_cache[(str(self.board), color)]
        else:
            # Find King on board
            for board_index in range(64):
                if self.board[board_index] is not None and self.board[board_index] & color and self.board[board_index] & Piece.KING:
                    king_position = board_index
                    break
            else:
                # raise Exception('King not found on board.')
                return False

            # Run through all possible moves for the opponent, and check if any would capture the King
            if color & Piece.WHITE:
                color_to_test = Piece.BLACK
            elif color & Piece.BLACK:
                color_to_test = Piece.WHITE

            for board in self.possibleMoveGenerator(color=color_to_test):
                if board.board[king_position] and board.board[king_position] & color == 0:
                    check_cache[(str(self.board), color)] = True
                    return True
            else:
                check_cache[(str(self.board), color)] = False
                return False

    # @db_cache
    def possibleMoveGenerator(self, color: int) -> list:
        """Need to implement:
                Pawn capturing
                En Passant
                Pawn promotion
                Castling
                Pawns can only move 2 spaces on initial move if BOTH spaces are unoccupied
                Check for checks

            Reference https://en.wikipedia.org/wiki/Shannon_number
            for testing
            https://en.wikipedia.org/wiki/Solving_chess for cool example
        """
        # if (str(self.board), color) in move_cache.keys():
        #     # log.info('Using move cache')
        #     return move_cache[(str(self.board), color)]
        moves = []
        for board_index in range(64):
            if self.board[board_index] is not None and self.board[board_index] & color:
                all_possible_moves = self.possible_moves[(self.board[board_index] & 0b111111110, board_index)]
                if all_possible_moves:
                    for move_group in all_possible_moves:
                        if move_group:
                            for move in move_group:
                                if self.board[move] is None or (self.board[move] is not None and self.board[move] & color == 0):
                                    new_board = Board.fromBoard(board=[p for p in self.board])
                                    piece = new_board.board[board_index] | Piece.MOVED
                                    new_board.board[board_index] = None
                                    new_board.board[move] = piece
                                    new_board.history = [h for h in self.history]
                                    new_board.history.append(Board.algebraic_notation(board_index=board_index) + Board.algebraic_notation(board_index=move))
                                    new_board.active_color = Piece.BLACK if color & Piece.WHITE else Piece.WHITE
                                    # yield new_board
                                    moves.append(new_board)
                                if self.board[move]:
                                    break

                # Pawn movement
                if self.board[board_index] & Piece.PAWN:
                    if color & Piece.WHITE:
                        move = board_index - 8
                        if move >= 0 and self.board[move] is None:
                            new_board = Board.fromBoard(board=[p for p in self.board])
                            piece = new_board.board[board_index] | Piece.MOVED
                            new_board.board[board_index] = None
                            new_board.board[move] = piece
                            new_board.history = [h for h in self.history]
                            new_board.history.append(Board.algebraic_notation(board_index=board_index) + Board.algebraic_notation(board_index=move))
                            new_board.active_color = Piece.BLACK if color & Piece.WHITE else Piece.WHITE
                            # yield new_board
                            moves.append(new_board)

                            if board_index // 8 == 6 and self.board[move - 8] is None:
                                new_board = Board.fromBoard(board=[p for p in self.board])
                                piece = new_board.board[board_index] | Piece.MOVED
                                new_board.board[board_index] = None
                                new_board.board[move - 8] = piece
                                new_board.history = [h for h in self.history]
                                new_board.history.append(Board.algebraic_notation(board_index=board_index) + Board.algebraic_notation(board_index=move))
                                new_board.en_passant_square = Board.algebraic_notation(move - 8)
                                new_board.active_color = Piece.BLACK if color & Piece.WHITE else Piece.WHITE
                                # print(new_board.fen_key)
                                # yield new_board
                                moves.append(new_board)

                    elif color & Piece.BLACK:
                        move = board_index + 8
                        if move < 64 and self.board[move] is None:
                            new_board = Board.fromBoard(board=[p for p in self.board])
                            piece = new_board.board[board_index] | Piece.MOVED
                            new_board.board[board_index] = None
                            new_board.board[move] = piece
                            new_board.history = [h for h in self.history]
                            new_board.history.append(Board.algebraic_notation(board_index=board_index) + Board.algebraic_notation(board_index=move))
                            new_board.active_color = Piece.BLACK if color & Piece.WHITE else Piece.WHITE
                            # yield new_board
                            moves.append(new_board)

                            if board_index // 8 == 1 and self.board[move + 8] is None:
                                new_board = Board.fromBoard(board=[p for p in self.board])
                                piece = new_board.board[board_index] | Piece.MOVED
                                new_board.board[board_index] = None
                                new_board.board[move + 8] = piece
                                new_board.en_passant_square = Board.algebraic_notation(move + 8)
                                new_board.history = [h for h in self.history]
                                new_board.history.append(Board.algebraic_notation(board_index=board_index) + Board.algebraic_notation(board_index=move))
                                new_board.active_color = Piece.BLACK if color & Piece.WHITE else Piece.WHITE
                                # print(new_board.fen_key)
                                # yield new_board
                                moves.append(new_board)

                # Pawn capture
                if self.board[board_index] & Piece.PAWN:
                    # Check eligible captures going LEFT
                    if color & Piece.WHITE:
                        offsets = [-9]
                    elif color & Piece.BLACK:
                        offsets = [7]
                    for offset in offsets:
                        move = board_index + offset
                        if move >= 0 and move < 64 and move % 8 < board_index % 8 and self.board[move] is not None and (self.board[move] & color == 0):
                            new_board = Board.fromBoard(board=[p for p in self.board])
                            piece = new_board.board[board_index] | Piece.MOVED
                            new_board.board[board_index] = None
                            new_board.board[move] = piece
                            new_board.history = [h for h in self.history]
                            new_board.history.append(Board.algebraic_notation(board_index=board_index) + Board.algebraic_notation(board_index=move))
                            new_board.active_color = Piece.BLACK if color & Piece.WHITE else Piece.WHITE
                            # yield new_board
                            moves.append(new_board)
                    # Check eligible captures going RIGHT
                    if color & Piece.WHITE:
                        offsets = [-7]
                    elif color & Piece.BLACK:
                        offsets = [9]
                    for offset in offsets:
                        move = board_index + offset
                        if move >= 0 and move < 64 and move % 8 > board_index % 8 and self.board[move] is not None and (self.board[move] & color == 0):
                            new_board = Board.fromBoard(board=[p for p in self.board])
                            piece = new_board.board[board_index] | Piece.MOVED
                            new_board.board[board_index] = None
                            new_board.board[move] = piece
                            new_board.history = [h for h in self.history]
                            new_board.history.append(Board.algebraic_notation(board_index=board_index) + Board.algebraic_notation(board_index=move))
                            new_board.active_color = Piece.BLACK if color & Piece.WHITE else Piece.WHITE
                            # yield new_board
                            moves.append(new_board)

                # White Castling
                if board_index >= 56 and color & Piece.WHITE and self.board[board_index] & Piece.ROOK and self.board[board_index] & Piece.MOVED == 0 and self.board[60] is not None and self.board[60] & Piece.KING and self.board[60] & Piece.WHITE and self.board[60] & Piece.MOVED == 0:
                    king = 60
                    rook = board_index
                    if rook > king:
                        # King side
                        if self.board[king + 1] is None and self.board[king + 2] is None:
                            new_board = Board.fromBoard(board=[p for p in self.board])
                            new_king = new_board.board[king] | Piece.MOVED
                            new_rook = new_board.board[rook] | Piece.MOVED
                            new_board.board[king] = None
                            new_board.board[rook] = None
                            new_board.board[king + 2] = new_king
                            new_board.board[rook - 2] = new_rook
                            new_board.active_color = Piece.BLACK if color & Piece.WHITE else Piece.WHITE
                            # yield new_board
                            moves.append(new_board)
                    elif rook < king:
                        # Queen side
                        if self.board[king - 1] is None and self.board[king - 2] is None:
                            new_board = Board.fromBoard(board=[p for p in self.board])
                            new_king = new_board.board[king] | Piece.MOVED
                            new_rook = new_board.board[rook] | Piece.MOVED
                            new_board.board[king] = None
                            new_board.board[rook] = None
                            new_board.board[king - 2] = new_king
                            new_board.board[rook + 3] = new_rook
                            new_board.active_color = Piece.BLACK if color & Piece.WHITE else Piece.WHITE
                            # yield new_board
                            moves.append(new_board)

                # Black Castling
                elif board_index <= 7 and color & Piece.BLACK and self.board[board_index] & Piece.ROOK and self.board[board_index] & Piece.MOVED == 0 and self.board[4] is not None and self.board[4] & Piece.KING and self.board[4] & Piece.BLACK and self.board[4] & Piece.MOVED == 0:
                    king = 4
                    rook = board_index
                    if rook > king:
                        # King side
                        if self.board[king + 1] is None and self.board[king + 2] is None:
                            new_board = Board.fromBoard(board=[p for p in self.board])
                            new_king = new_board.board[king] | Piece.MOVED
                            new_rook = new_board.board[rook] | Piece.MOVED
                            new_board.board[king] = None
                            new_board.board[rook] = None
                            new_board.board[king + 2] = new_king
                            new_board.board[rook - 2] = new_rook
                            new_board.active_color = Piece.BLACK if color & Piece.WHITE else Piece.WHITE
                            # yield new_board
                            moves.append(new_board)
                    elif rook < king:
                        # Queen side
                        if self.board[king - 1] is None and self.board[king - 2] is None:
                            new_board = Board.fromBoard(board=[p for p in self.board])
                            new_king = new_board.board[king] | Piece.MOVED
                            new_rook = new_board.board[rook] | Piece.MOVED
                            new_board.board[king] = None
                            new_board.board[rook] = None
                            new_board.board[king - 2] = new_king
                            new_board.board[rook + 3] = new_rook
                            new_board.active_color = Piece.BLACK if color & Piece.WHITE else Piece.WHITE
                            # yield new_board
                            moves.append(new_board)

        # move_cache[(str(self.board), color)] = moves
        return moves

    def load_from_fen_string(self, fen_string: str) -> None:
        keys = fen_string.split(' ')
        board_string, player_turn, castling, en_passant, half_turns, full_turns = keys
        # print(board_string, player_turn, castling, en_passant, half_turns, full_turns)

        def process_board_layout(board_string):
            log.debug(f'Loading FEN string {board_string}...')
            position = 0
            self.clear()
            for char in board_string:
                log.debug(f'Processing {char}...')
                if char.isdigit():
                    position += int(char)
                    log.debug(f'Skipping {int(char)} spaces...')
                elif char.isalpha():
                    piece_type = None
                    if char.isupper():
                        piece_color = Piece.WHITE
                    else:
                        piece_color = Piece.BLACK
                    if char.upper() == 'R':
                        piece_type = Piece.ROOK
                        log.debug(f'Adding a ROOK to {position}...')
                    elif char.upper() == 'N':
                        piece_type = Piece.KNIGHT
                        log.debug(f'Adding a KNIGHT to {position}...')
                    elif char.upper() == 'B':
                        piece_type = Piece.BISHOP
                        log.debug(f'Adding a BISHOP to {position}...')
                    elif char.upper() == 'Q':
                        piece_type = Piece.QUEEN
                        log.debug(f'Adding a QUEEN to {position}...')
                    elif char.upper() == 'K':
                        piece_type = Piece.KING
                        log.debug(f'Adding a KING to {position}...')
                    elif char.upper() == 'P':
                        piece_type = Piece.PAWN
                        log.debug(f'Adding a PWN to {position}...')
                    elif char == '/':
                        continue

                    if char != '/':
                        self.board[position] = piece_type | piece_color
                        position += 1

        def process_castling(castling: str) -> None:
            if not castling:
                return
            if 'k' not in castling:
                if self.board[4] and self.board[4] & Piece.KING and self.board[4] & Piece.BLACK:
                    self.board[4] = self.board[4] | Piece.MOVED
                if self.board[7] and self.board[7] & Piece.ROOK and self.board[7] & Piece.BLACK:
                    self.board[7] = self.board[7] | Piece.MOVED
            if 'q' not in castling:
                if self.board[4] and self.board[4] & Piece.KING and self.board[4] & Piece.BLACK:
                    self.board[4] = self.board[4] | Piece.MOVED
                if self.board[0] and self.board[0] & Piece.ROOK and self.board[0] & Piece.BLACK:
                    self.board[0] = self.board[0] | Piece.MOVED

            if 'K' not in castling:
                if self.board[60] and self.board[60] & Piece.KING and self.board[60] & Piece.WHITE:
                    self.board[60] = self.board[60] | Piece.MOVED
                if self.board[63] and self.board[63] & Piece.ROOK and self.board[63] & Piece.WHITE:
                    self.board[63] = self.board[63] | Piece.MOVED
            if 'Q' not in castling:
                if self.board[60] and self.board[60] & Piece.KING and self.board[60] & Piece.WHITE:
                    self.board[60] = self.board[60] | Piece.MOVED
                if self.board[56] and self.board[56] & Piece.ROOK and self.board[56] & Piece.WHITE:
                    self.board[56] = self.board[56] | Piece.MOVED

        process_board_layout(board_string=board_string)
        process_castling(castling=castling)


    @property
    def fen_key(self) -> str:
        def determineCastling(board) -> str:
            castling = ''
            # White
            if board[63] and board[60] and board[63] & Piece.MOVED == 0 and board[63] & Piece.ROOK and board[63] & Piece.WHITE and board[60] & Piece.MOVED == 0 and board[60] & Piece.KING and board[60] & Piece.WHITE:
                castling += 'K'
            if board[56] and board[60] and board[56] & Piece.MOVED == 0 and board[56] & Piece.ROOK and board[56] & Piece.WHITE and board[60] & Piece.MOVED == 0 and board[60] & Piece.KING and board[60] & Piece.WHITE:
                castling += 'Q'
            # Black
            if board[7] and board[4] and board[7] & Piece.MOVED == 0 and board[7] & Piece.ROOK and board[7] & Piece.BLACK and board[4] & Piece.MOVED == 0 and board[4] & Piece.KING and board[4] & Piece.BLACK:
                castling += 'k'
            if board[0] and board[4] and board[0] & Piece.MOVED == 0 and board[0] & Piece.ROOK and board[0] & Piece.BLACK and board[4] & Piece.MOVED == 0 and board[4] & Piece.KING and board[4] & Piece.BLACK:
                castling += 'q'
            if castling == '':
                castling = '-'
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
            if piece and empty > 0:
                board += str(empty)
                empty = 0
            if piece and empty == 0:
                this_piece = Piece.getPieceType(piece)
                if this_piece[0] == 'B':
                    this_piece = this_piece[1].lower()
                else:
                    this_piece = this_piece[1].upper()
                board += this_piece
        if empty:
            board += str(empty)
        fen += board
        fen += ' '
        color = 'w' if self.active_color & Piece.WHITE else 'b'
        fen += color
        fen += ' '
        castling = determineCastling(self.board)
        fen += castling
        fen += ' '
        # En Passant
        if self.en_passant_square:    
            fen += self.en_passant_square
        # fen += ' '
        # # Half moves
        # fen += str(self.halfmoves)
        # fen += ' '
        # # Full moves
        # fen += str(self.fullmoves)

        log.debug(f'{self.board} translated to {fen}')
        return fen

    @staticmethod
    def translatePos(row: int = 1, column: int = 1) -> int:
        position = ((9 - row - 1) * 8) + column - 1
        if position >= 0 and position < 64:
            return position
        else:
            return None

    @staticmethod
    def algebraic_notation(board_index: int) -> str:
        if board_index < 0 or board_index > 63:
            return None
        rank = 8 - (board_index // 8)
        file = board_index % 8
        rank_str = str(rank)
        file_str = chr(97 + file)
        notation = file_str + rank_str
        return notation
