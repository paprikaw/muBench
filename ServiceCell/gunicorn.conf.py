loglevel = 'info'
accesslog = '-'  # 输出到标准输出
errorlog = '-'  # 输出到标准输出
def worker_exit(server, worker):
    from prometheus_client import multiprocess
    multiprocess.mark_process_dead(worker.pid)