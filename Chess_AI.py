import logging
import configparser
from mariadb_handler import MariaDBHandler
from Piece import Piece
from Board import Board

config = configparser.ConfigParser()
config.read('config.ini')
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s.%(msecs)03d - %(levelname)8s - %(filename)s - Function: %(funcName)20s - Line: %(lineno)4s // %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    handlers=[
                        logging.FileHandler(filename='log.txt'),
                        logging.StreamHandler(),
                        MariaDBHandler(username=config['log']['log_db_user'], password=config['log']['log_db_password'], host=config['log']['log_db_host'])
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
    white_boards = []
    for turns in range(2):
        white_boards.clear()
        for b in black_boards:
            for wb in b.possibleMoveGenerator(Piece.WHITE):
                if not wb.isCheckForColor(Piece.WHITE):
                    white_boards.append(wb)
        logging.info(f'Turn {turns + 1} for WHITE: {len(white_boards):,}')

        black_boards.clear()
        for b in white_boards:
            for bb in b.possibleMoveGenerator(Piece.BLACK):
                if not bb.isCheckForColor(Piece.BLACK):
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

    


if __name__ == '__main__':
    main()
