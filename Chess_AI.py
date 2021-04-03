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