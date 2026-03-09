# global_mq.py 全局队列与公共配置模块
import queue
import threading
from typing import Dict, Tuple

# 核心常量（服务端、客户端、生产者需严格一致）
END_MARK = '[END]'               # 单轮消息结束标识
EXIT_CMD = 'exit'                # 客户端退出命令
REPLY_TRIGGER = '请客户端回答'   # 触发客户端应答权限的指令
ENCODING = 'utf-8'               # 消息编码
QUEUE_MAXSIZE = 0                # 全局队列最大容量，0表示无限制

# 全局线程安全队列：生产者写入，服务端消费（元素格式："目标ID:消息内容"）
global_msg_queue = queue.Queue(maxsize=QUEUE_MAXSIZE)

## todo new
# from multiprocessing import Manager
from queue import Queue

class GlobalDict:
    def __init__(self):
        # 创建跨进程的线程安全字典（全局生效）
        # manager = Manager()
        # self.cross_process_safe_map = manager.dict()
        self.cross_process_safe_map = {}

    def get(self, session_id):
        return self.cross_process_safe_map[session_id]

    def initialize_queue(self, session_id):
        this_queue = Queue()
        self.cross_process_safe_map.__setitem__(session_id, this_queue)

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
global_server_msg_dict = GlobalDict()
# 这个存放的是客户端输入进来的数据
global_client_msg_dict = GlobalDict()

# 客户端应答权限映射表：{客户端ID: 是否允许应答}，线程安全
client_reply_permission: Dict[int, bool] = {}
agent_management = {}
permission_lock = threading.Lock()  # 权限表操作锁

# 在线客户端映射表（服务端维护，此处仅做类型声明，实际在服务端初始化）
online_clients: Dict[int, Tuple] = {}
client_lock = threading.Lock()    # 在线客户端表操作锁

def set_reply_permission(client_id, allow: bool):
    """设置客户端应答权限（线程安全）"""
    with permission_lock:
        client_reply_permission[client_id] = allow

def get_reply_permission(client_id) -> bool:
    """获取客户端应答权限（线程安全），默认不允许"""
    with permission_lock:
        return client_reply_permission.get(client_id, False)

def clear_reply_permission(client_id):
    """客户端断开时清理应答权限（线程安全）"""
    with permission_lock:
        if client_id in client_reply_permission:
            del client_reply_permission[client_id]


def set_agent_status(client_id, status = False):
    """设置客户端应答权限（线程安全）"""
    with permission_lock:
        agent_management[client_id] = status

def get_agent_status(client_id):
    """获取客户端应答权限（线程安全），默认不允许"""
    with permission_lock:
        return agent_management.get(client_id)

def clear_agent_status(client_id):
    """客户端断开时清理应答权限（线程安全）"""
    with permission_lock:
        if client_id in agent_management:
            del agent_management[client_id]