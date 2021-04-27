import time


def log_execution_time(method):
    def timed(*args, **kw):
        ts = time.perf_counter()
        result = method(*args, **kw)
        te = time.perf_counter()
        # print(f'{method.__name__} -- {(te - ts) * 1000:02f} ms')
        with open('execution_log.csv', 'a') as execution_log:
            execution_log.write(f'{method.__name__},{(te - ts):.8f}\n')

        return result
    return timed


if __name__ == '__main__':
    pass
