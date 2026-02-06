# server.py 服务端主程序
import socket
import re
import threading
import time
from typing import Tuple, Optional
import asyncio

from app.agent.manus import Manus
from server.enhanced_server.global_mq import (global_server_msg_dict, set_agent_status, get_agent_status, clear_agent_status,
                                              client_lock, set_reply_permission, get_reply_permission, clear_reply_permission,
                                              END_MARK, EXIT_CMD, ENCODING, global_client_msg_dict
                                              )
import uuid
# 服务端网络配置
HOST = '0.0.0.0'         # 绑定所有网卡，支持本地/局域网
PORT = 19278
BUFFER_SIZE = 4096
MAX_LISTEN_QUEUE = 20    # 最大监听队列
# 客户端唯一ID生成器
client_id_generator = 1
id_lock = threading.Lock()

# 线程安全的连接状态（每个客户端独立实例）
class ConnectionState:
    def __init__(self):
        self.connected = True
        self.lock = threading.Lock()

    def set_disconnected(self):
        with self.lock:
            self.connected = False

    def is_connected(self):
        with self.lock:
            return self.connected

# ---------------------- 客户端ID管理 ----------------------
def get_next_session_id():
    return str(uuid.uuid4())

async def add_online_client(client_id, conn: socket.socket, addr: Tuple[str, int], state: ConnectionState):
    """添加客户端到在线列表（线程安全）"""
    with client_lock:
        online_clients[client_id] = (conn, addr, state)
        # todo 在这边加入具体的manus实例

    # 初始化应答权限为False（默认不允许回答）

    set_reply_permission(client_id, True)
    # 构造queue
    global_client_msg_dict.initialize_queue(client_id)
    global_server_msg_dict.initialize_queue(client_id)
    print(f"📇 客户端[{client_id}] | 加入在线列表 | 在线数：{len(online_clients)}")


def remove_online_client(client_id: int):
    """从在线列表移除客户端（线程安全）"""
    with client_lock:
        if client_id in online_clients:
            del online_clients[client_id]
    # 清理应答权限
    clear_reply_permission(client_id)
    clear_agent_status(client_id)
    global_client_msg_dict.cleanup(client_id)
    global_server_msg_dict.cleanup(client_id)
    print(f"📇 客户端[{client_id}] | 移出在线列表 | 在线数：{len(online_clients)}")

def get_client_conn(client_id: int) -> Optional[Tuple[socket.socket, Tuple[str, int], ConnectionState]]:
    """根据ID获取客户端连接信息（线程安全）"""
    with client_lock:
        return online_clients.get(client_id)

# ---------------------- 队列监听与自动下发 ----------------------
# 获取服务端信息，下发给客户端。
def queue_listen_thread(client_id):
    """
    全局队列监听线程：持续消费队列数据，自动精准下发给指定客户端
    这个是一直启动的，只要有数据就往客户端下发，恰当时机打开接收客户端信息的开关
    """

    print(f"📜 全局队列监听线程已启动 | 等待生产者写入数据...")
    while True:
        try:
            # 阻塞获取队列消息（队列有数据则立即处理）
            server_queue = global_server_msg_dict.get(client_id)
            queue_msg = server_queue.get(block=True, timeout=None)
            # queue_msg = global_msg_queue.get(block=True, timeout=None)

            # 分离目标客户端ID和实际消息
            send_content = queue_msg.strip()

            # 获取目标客户端连接
            target_client = get_client_conn(client_id)
            if not target_client:
                print(f"❌ 队列下发失败 | 客户端[{client_id}]离线或不存在 | 消息：{send_content}")
                server_queue.task_done()
                continue
            target_sock, target_addr, target_state = target_client
            if not target_state.is_connected():
                print(f"❌ 队列下发失败 | 客户端[{client_id}]已断开 | 消息：{send_content}")
                remove_online_client(client_id)
                server_queue.task_done()
                continue

            # 发送消息并处理应答权限
            full_msg = f"{send_content}{END_MARK}"
            send_http_response(target_sock, full_msg)
            print(f"✅ 队列自动下发成功 | 客户端[{client_id}]（{target_addr}）| 消息：{send_content}")
            server_queue.task_done()
        except Exception as e:
            print(f"⚠️  队列监听线程异常 | 原因：{str(e)}...")
            time.sleep(1)  # 异常后短暂休眠，避免死循环

# ---------------------- HTTP消息收发 ----------------------
def send_http_response(conn: socket.socket, body: str):
    """构造HTTP 1.1长连接分块响应"""
    headers = (
        "HTTP/1.1 200 OK\r\n"
        "Connection: Keep-Alive\r\n"
        "Transfer-Encoding: chunked\r\n"
        f"Content-Type: text/plain; charset={ENCODING}\r\n"
        "Keep-Alive: timeout=300, max=0\r\n"
        "\r\n"
    )
    chunk_size = hex(len(body))[2:]
    chunked_body = f"{chunk_size}\r\n{body}\r\n0\r\n\r\n"
    full_resp = headers.encode(ENCODING) + chunked_body.encode(ENCODING)
    conn.sendall(full_resp)

# 这是客户端向服务端发送信息
async def run_recv_thread(session_id, conn: socket.socket, state: ConnectionState):
    agent = await Manus.create_with_session_id(session_id)
    while state.is_connected():
        request_data = b''
        while state.is_connected():
            chunk = conn.recv(BUFFER_SIZE)
            if not chunk:
                raise ConnectionResetError("客户端socket关闭")
            request_data += chunk
            if b'\r\n\r\n' in request_data and END_MARK.encode(ENCODING) in request_data:
                break
        # 解析客户端消息
        request_str = request_data.decode(ENCODING, errors='ignore')
        pattern = r'Keep-Alive: .*?\n(.*?)\[END\]'
        body_match = re.search(pattern, request_str, re.DOTALL)
        # body_match = re.search(r'\r\n\r\n(.*?)' + END_MARK, request_str, re.DOTALL)
        if not body_match:
            print(f"❌ 客户端[{session_id}] | 消息解析失败")
            continue
        client_msg = body_match.group(1).strip()
        print(f"\n📨 客户端[{session_id}] | 尝试发送消息：{client_msg}")

        # 处理退出命令（不受权限控制）
        if client_msg == EXIT_CMD:
            print(f"📤 客户端[{session_id}] | 发送退出命令，准备断开")
            send_http_response(conn, f"服务端已接收退出命令，连接即将关闭{END_MARK}")
            state.set_disconnected()
            break

        # 核心：判断是否有应答权限，无则拒绝并提示
        if not get_reply_permission(session_id):
            refuse_msg = f"【权限拒绝】当前未收到服务端应答指令，禁止发送消息！{END_MARK}"
            send_http_response(conn, refuse_msg)
            print(f"🚫 客户端[{session_id}] | 无应答权限，消息已拒绝")
            continue

        # 有应答权限：接收消息并打印，同时关闭应答权限（单次有效）
        """
        第一次接收到的话，就是prompt；后面就是触发ask human了。
        """

        agent_running = get_agent_status(session_id)
        if not agent_running:
            t = threading.Thread(target=run_agent, args = (agent, client_msg,), daemon=True)
            # 启动线程：核心，后台任务开始执行，主程序不等待
            t.start()
            set_agent_status(session_id, True)
        else:
            # todo 这里需要自动发送到ask human那边
            global_client_msg_dict.add_data(session_id, client_msg)
        print(f"✅ 客户端[{session_id}] | 有权限，消息已接收：{client_msg}")

        send_http_response(conn, f"【消息已接收】你的应答：{client_msg}{END_MARK}")
        set_reply_permission(session_id, False)  # 应答后立即关闭权限，防止重复发送
        print(f"已关闭{session_id}接收权限")

"""
agent run不能写在recv这边，会阻塞，必须搞个线程来执行。
"""
def run_agent(agent, client_msg):
    asyncio.run(async_run_agent(agent, client_msg))
async def async_run_agent(agent, client_msg):
    await agent.run(client_msg)



def recv_thread(session_id, conn: socket.socket, addr, state: ConnectionState):
    """接收线程：仅当开启应答权限时，才接收客户端消息，否则拒绝"""
    print(f"📥 客户端[{session_id}] | 接收线程已启动（需授权才能接收消息）")
    try:
        asyncio.run(run_recv_thread(session_id, conn, state))

    except (ConnectionResetError, BrokenPipeError, OSError) as e:
        if state.is_connected():
            print(f"❌ 客户端[{session_id}] | 连接断开（{str(e)[:20]}...）")
            state.set_disconnected()
    finally:
        remove_online_client(session_id)
        print(f"📥 客户端[{session_id}] | 接收线程已终止")

# todo 每启动一个客户端，都需要启动一个manus服务示例。
# todo 这是服务端向客户端下发信息
def send_thread(session_id, conn: socket.socket, state: ConnectionState):
    """服务端手动操作线程：查看在线/手动下发/手动开启应答权限"""
    print(f"📤 客户端[{session_id}] | 手动操作线程已启动")
    print(f"💡 操作规则：")
    print(f"   1. list → 查看在线客户端")
    print(f"   2. ID:消息 → 手动精准下发（如 1:手动发送数据）")
    print(f"   3. ID:请客户端回答 → 手动开启指定客户端应答权限")
    print(f"   4. exit → 断开当前客户端\n")
    try:
        while state.is_connected():

            # todo 专门搞个debug的线程，来进行控制
            # # 查看在线客户端
            # if server_input == 'list':
            #     print(f"\n📭 当前在线客户端（共{len(online_clients)}个）：")
            #     with client_lock:
            #         for cid, (_, addr, _) in online_clients.items():
            #             perm = "✅ 已授权" if get_reply_permission(cid) else "❌ 未授权"
            #             print(f"   → ID:{cid} | 地址:{addr} | 应答权限:{perm}")
            #     print("-" * 40)
            #     continue
            # # 断开当前客户端
            # if server_input == EXIT_CMD:
            #     send_http_response(conn, f"服务端主动断开，Session结束{END_MARK}")
            #     state.set_disconnected()
            #     break


            # target_msg = msg.strip()
            target_client = get_client_conn(session_id)
            if not target_client:
                print(f"❌ 操作失败 | 客户端[{session_id}]离线")
                time.sleep(0.5)
                continue
            target_sock, target_addr, _ = target_client
            # 发送手动消息
            server_msg_queue = global_server_msg_dict.get(session_id)
            # 阻塞获取，不需要用循环包起来
            client_msg = server_msg_queue.get(block=True, timeout=None)

            client_msg = client_msg.strip()
            send_http_response(target_sock, f"{client_msg}{END_MARK}")
            print(f"✅ 手动下发成功 | 客户端[{session_id}] | 消息：{client_msg}")
            continue
    except Exception as e:
        if state.is_connected():
            print(f"❌ 手动操作线程异常 | {str(e)}...")
    finally:
        print(f"📤 客户端[{session_id}] | 手动操作线程已终止")

# ---------------------- 客户端连接处理 ----------------------
def handle_single_client(conn: socket.socket, addr):
    """处理单个客户端完整生命周期"""
    session_id = get_next_session_id()
    conn_state = ConnectionState()
    asyncio.run(add_online_client(session_id, conn, addr, conn_state))

    # 打印连接信息
    print(f"\n" + "="*60)
    print(f"✅ 新客户端连接 | ID:{session_id} | 地址:{addr}")
    print(f"✅ 连接时间：{time.strftime('%Y-%m-%d %H:%M:%S')} | 在线数:{len(online_clients)}")
    print(f"="*60 + "\n")
    try:
        # 启动收发线程
        t_recv = threading.Thread(target=recv_thread, args=(session_id, conn, addr, conn_state), daemon=True)
        t_send = threading.Thread(target=send_thread, args=(session_id, conn, conn_state), daemon=True)
        # 启动全局队列监听线程（守护线程）
        t_queue = threading.Thread(target=queue_listen_thread, args=(session_id, ), daemon=True)
        t_recv.start()
        t_send.start()
        t_queue.start()
        t_recv.join()
        t_send.join()
        t_send.join()
    finally:
        conn.close()
        print(f"🔌 客户端[{session_id}] | 连接已释放")
        print(f"="*60 + "\n")

# ---------------------- 服务端主启动 ----------------------
def start_server():
    """启动永久运行的服务端主程序"""
    # 初始化在线客户端表（与global_mq中的映射表关联）
    global online_clients
    online_clients = {}
    # 创建服务端socket
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((HOST, PORT))
    server_sock.listen(MAX_LISTEN_QUEUE)
    # 打印启动信息
    print(f"🚀 全局队列驱动的服务端已启动 | 永久运行模式")
    print(f"📌 监听地址：{HOST}:{PORT} | 支持多客户端并发/重连")
    print(f"🎯 核心特性：队列自动下发、应答权限控制、精准指定客户端")
    print(f"📜 队列格式：目标ID:消息内容（如 1:设备数据 2:请客户端回答）")
    print(f"⚙️  手动命令：list=查看在线、ID:消息=手动下发、exit=断开\n")

    try:
        # 无限循环监听客户端连接
        while True:
            conn, addr = server_sock.accept()
            threading.Thread(target=handle_single_client, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        print(f"\n⚠️  服务端收到中断信号，即将优雅关闭")
    finally:
        server_sock.close()
        with client_lock:
            online_clients.clear()
        print(f"🔒 服务端主监听已关闭 | 所有资源已清理")

start_server()