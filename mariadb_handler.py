import logging
import time
import mariadb


class MariaDBHandler(logging.Handler):
    initial_sql = """CREATE TABLE IF NOT EXISTS log(
                        LogID bigint auto_increment primary key,
                        Created text,
                        FileName text,
                        Name text,
                        LogLevel int,
                        LogLevelName text,
                        Message text,
                        Args text,
                        Module text,
                        FuncName text,
                        LineNo int,
                        Exception text,
                        Process int,
                        Thread text,
                        ThreadName text
                   )"""

    insertion_sql = """INSERT INTO log(
                        Created,
                        FileName,
                        Name,
                        LogLevel,
                        LogLevelName,
                        Message,
                        Args,
                        Module,
                        FuncName,
                        LineNo,
                        Exception,
                        Process,
                        Thread,
                        ThreadName
                   )
                   VALUES (
                        '%(asctime)s.%(msecs)03d',
                        '%(filename)s',
                        '%(name)s',
                        %(levelno)d,
                        '%(levelname)s',
                        '%(message)s',
                        '%(args)s',
                        '%(module)s',
                        '%(funcName)s',
                        %(lineno)d,
                        '%(exc_text)s',
                        %(process)d,
                        '%(thread)s',
                        '%(threadName)s'
                   );
                   """

    def __init__(self, username, password, host="localhost", port=3306, database="logs"):

        logging.Handler.__init__(self)
        self.conn = mariadb.connect(
            user=username,
            password=password,
            host=host,
            port=port,
            database=database)
        self.conn.autocommit = False
        self.cursor = self.conn.cursor()
        # Create table if needed:
        self.cursor.execute(MariaDBHandler.initial_sql)
        self.conn.commit()

    def formatDBTime(self, record):
        record.dbtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(record.created))

    def emit(self, record):
        self.format(record)
        self.formatDBTime(record)

        if record.exc_info:
            record.exc_text = logging._defaultFormatter.formatException(record.exc_info)
        else:
            record.exc_text = ""

        # Process string elements of record dict to escape special characters
        record_dict = {k: self.conn.escape_string(v) if type(v) == str else v for k, v in record.__dict__.items()}

        sql = MariaDBHandler.insertion_sql % record_dict
        self.cursor.execute(sql)
        self.conn.commit()

    def __del__(self):
        self.conn.close()

    def __exit__(self, type, value, traceback):
        self.conn.close()
