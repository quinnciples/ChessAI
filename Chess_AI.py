import logging
from mariadb_handler import MariaDBHandler
from Piece import Piece
from Board import Board
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


def main():

    print()
    print('*' * 13, ' STARTING BOARD ', '*' * 13)
    b = Board()
    b.reset()
    b.print()
    print('*' * 44)
    print()

    black_boards = [b]
    for turns in range(2):
        white_boards = []
        for b in black_boards:
            for wb in b.possibleMoveGenerator(Piece.WHITE):
                white_boards.append(wb)
        logging.info(f'Turn {turns + 1} for WHITE: {len(white_boards):,}')

        black_boards = []
        for b in white_boards:
            for bb in b.possibleMoveGenerator(Piece.BLACK):
                black_boards.append(bb)
        logging.info(f'Turn {turns + 1} for BLACK: {len(black_boards):,}')
    # 1 	20
    # 2 	400
    # 3 	8,902
    # 4 	197,281
    # 5 	4,865,609
    # 6 	119,060,324
    # 7 	3,195,901,860
    # 8 	84,998,978,956
    # 9 	2,439,530,234,167
    # 10 	69,352,859,712,417 

    b = Board()
    b.reset()
    b.clear()
    b.board[4] = Piece.KING | Piece.BLACK
    b.board[0] = Piece.ROOK | Piece.BLACK
    b.board[7] = Piece.ROOK | Piece.BLACK
    print('*' * 13, ' CASTLING TEST ', '*' * 13)
    b.print()
    moves = [brd for brd in b.possibleMoveGenerator(Piece.BLACK)]
    for brd in moves:
        brd.print()
    logging.info(f'{len(moves):,} possibilities')



if __name__ == '__main__':
    main()
