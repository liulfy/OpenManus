from multiprocessing import Manager
from queue import Queue

class GlobalDict:
    def __init__(self):
        # 创建跨进程的线程安全字典（全局生效）
        manager = Manager()
        self.cross_process_safe_map = manager.dict()

    def add_data(self, session_id, log_data):
        if not session_id in self.cross_process_safe_map:
            this_queue = Queue()
        else:
            this_queue = self.cross_process_safe_map.get(session_id)
        this_queue.put(log_data)
        self.cross_process_safe_map.__setitem__(session_id, this_queue)

    def cleanup(self, session_id):
        self.cross_process_safe_map.pop(session_id)
# 这个存放的是直接输出出去给到用户的数据
golbal_dict = GlobalDict()
