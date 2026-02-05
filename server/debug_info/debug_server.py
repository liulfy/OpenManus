# server.py 服务端主程序
import socket
import re
import threading
import time
from typing import Dict, Tuple, Optional
from server.enhanced_server.global_mq import (
    global_msg_queue, online_clients, client_lock,
    set_reply_permission, get_reply_permission, clear_reply_permission,
    END_MARK, EXIT_CMD, REPLY_TRIGGER, ENCODING
)

# 服务端网络配置
HOST = '0.0.0.0'         # 绑定所有网卡，支持本地/局域网
PORT = 8080
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
def get_next_client_id() -> int:
    """生成全局唯一客户端ID（线程安全）"""
    global client_id_generator
    with id_lock:
        current_id = client_id_generator
        client_id_generator += 1
    return current_id

def add_online_client(client_id: int, conn: socket.socket, addr: Tuple[str, int], state: ConnectionState):
    """添加客户端到在线列表（线程安全）"""
    with client_lock:
        online_clients[client_id] = (conn, addr, state)
    # 初始化应答权限为False（默认不允许回答）
    set_reply_permission(client_id, False)
    print(f"📇 客户端[{client_id}] | 加入在线列表 | 在线数：{len(online_clients)}")

def remove_online_client(client_id: int):
    """从在线列表移除客户端（线程安全）"""
    with client_lock:
        if client_id in online_clients:
            del online_clients[client_id]
    # 清理应答权限
    clear_reply_permission(client_id)
    print(f"📇 客户端[{client_id}] | 移出在线列表 | 在线数：{len(online_clients)}")

def get_client_conn(client_id: int) -> Optional[Tuple[socket.socket, Tuple[str, int], ConnectionState]]:
    """根据ID获取客户端连接信息（线程安全）"""
    with client_lock:
        return online_clients.get(client_id)

# ---------------------- 队列监听与自动下发 ----------------------
def queue_listen_thread():
    """全局队列监听线程：持续消费队列数据，自动精准下发给指定客户端"""
    print(f"📜 全局队列监听线程已启动 | 等待生产者写入数据...")
    while True:
        try:
            # 阻塞获取队列消息（队列有数据则立即处理）
            queue_msg = global_msg_queue.get(block=True, timeout=None)
            # 解析队列消息：格式必须为 "目标ID:消息内容"
            if ':' not in queue_msg:
                print(f"❌ 队列消息格式错误 | 忽略：{queue_msg} | 正确格式：ID:内容")
                global_msg_queue.task_done()
                continue
            # 分离目标客户端ID和实际消息
            target_cid_str, send_content = queue_msg.split(':', 1)
            if not target_cid_str.isdigit() or not send_content.strip():
                print(f"❌ 队列消息解析失败 | 忽略：{queue_msg}")
                global_msg_queue.task_done()
                continue
            target_cid = int(target_cid_str)
            send_content = send_content.strip()

            # 获取目标客户端连接
            target_client = get_client_conn(target_cid)
            if not target_client:
                print(f"❌ 队列下发失败 | 客户端[{target_cid}]离线或不存在 | 消息：{send_content}")
                global_msg_queue.task_done()
                continue
            target_sock, target_addr, target_state = target_client
            if not target_state.is_connected():
                print(f"❌ 队列下发失败 | 客户端[{target_cid}]已断开 | 消息：{send_content}")
                remove_online_client(target_cid)
                global_msg_queue.task_done()
                continue

            # 发送消息并处理应答权限
            full_msg = f"{send_content}{END_MARK}"
            send_http_response(target_sock, full_msg)
            print(f"✅ 队列自动下发成功 | 客户端[{target_cid}]（{target_addr}）| 消息：{send_content}")
            # 关键：若下发的是REPLY_TRIGGER，开启该客户端的应答权限
            if send_content == REPLY_TRIGGER:
                set_reply_permission(target_cid, True)
                print(f"🔓 客户端[{target_cid}] | 已开启应答权限（仅本次有效）")

            global_msg_queue.task_done()
        except Exception as e:
            print(f"⚠️  队列监听线程异常 | 原因：{str(e)[:50]}...")
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

def recv_thread(client_id: int, conn: socket.socket, addr, state: ConnectionState):
    """接收线程：仅当开启应答权限时，才接收客户端消息，否则拒绝"""
    print(f"📥 客户端[{client_id}] | 接收线程已启动（需授权才能接收消息）")
    try:
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
            print(f"server request_str: {request_str}")
            pattern = r'Keep-Alive: .*?\n(.*?)\[END\]'
            body_match = re.search(pattern, request_str, re.DOTALL)
            # body_match = re.search(r'\r\n\r\n(.*?)\[\[END\]', request_str, re.DOTALL)
            print(f"body_match: {body_match}")
            if not body_match:
                print(f"❌ 客户端[{client_id}] | 消息解析失败")
                continue
            client_msg = body_match.group(1).strip()
            print(f"\n📨 客户端[{client_id}] | 尝试发送消息：{client_msg}")

            # 处理退出命令（不受权限控制）
            if client_msg == EXIT_CMD:
                print(f"📤 客户端[{client_id}] | 发送退出命令，准备断开")
                send_http_response(conn, f"服务端已接收退出命令，连接即将关闭{END_MARK}")
                state.set_disconnected()
                break

            # 核心：判断是否有应答权限，无则拒绝并提示
            if not get_reply_permission(client_id):
                refuse_msg = f"【权限拒绝】当前未收到服务端应答指令，禁止发送消息！{END_MARK}"
                send_http_response(conn, refuse_msg)
                print(f"🚫 客户端[{client_id}] | 无应答权限，消息已拒绝")
                continue

            # 有应答权限：接收消息并打印，同时关闭应答权限（单次有效）
            print(f"✅ 客户端[{client_id}] | 有权限，消息已接收：{client_msg}")
            send_http_response(conn, f"【消息已接收】你的应答：{client_msg}{END_MARK}")
            set_reply_permission(client_id, False)  # 应答后立即关闭权限，防止重复发送

    except (ConnectionResetError, BrokenPipeError, OSError) as e:
        if state.is_connected():
            print(f"❌ 客户端[{client_id}] | 连接断开（{str(e)[:20]}...）")
            state.set_disconnected()
    finally:
        remove_online_client(client_id)
        print(f"📥 客户端[{client_id}] | 接收线程已终止")

def send_thread(client_id: int, conn: socket.socket, state: ConnectionState):
    """服务端手动操作线程：查看在线/手动下发/手动开启应答权限"""
    print(f"📤 客户端[{client_id}] | 手动操作线程已启动")
    print(f"💡 操作规则：")
    print(f"   1. list → 查看在线客户端")
    print(f"   2. ID:消息 → 手动精准下发（如 1:手动发送数据）")
    print(f"   3. ID:请客户端回答 → 手动开启指定客户端应答权限")
    print(f"   4. exit → 断开当前客户端\n")
    try:
        while state.is_connected():
            server_input = input(f"📤 服务端手动操作 > ").strip()
            if not server_input:
                continue
            # 查看在线客户端
            if server_input == 'list':
                print(f"\n📭 当前在线客户端（共{len(online_clients)}个）：")
                with client_lock:
                    for cid, (_, addr, _) in online_clients.items():
                        perm = "✅ 已授权" if get_reply_permission(cid) else "❌ 未授权"
                        print(f"   → ID:{cid} | 地址:{addr} | 应答权限:{perm}")
                print("-" * 40)
                continue
            # 断开当前客户端
            if server_input == EXIT_CMD:
                send_http_response(conn, f"服务端主动断开，Session结束{END_MARK}")
                state.set_disconnected()
                break
            # 手动精准下发（格式：ID:消息）
            if ':' in server_input:
                cid_str, msg = server_input.split(':', 1)
                if not cid_str.isdigit() or not msg.strip():
                    print(f"❌ 格式错误 | 正确格式：ID:消息内容")
                    continue
                target_cid = int(cid_str)
                target_msg = msg.strip()
                target_client = get_client_conn(target_cid)
                if not target_client:
                    print(f"❌ 操作失败 | 客户端[{target_cid}]离线")
                    continue
                target_sock, target_addr, _ = target_client
                # 发送手动消息
                send_http_response(target_sock, f"{target_msg}{END_MARK}")
                print(f"✅ 手动下发成功 | 客户端[{target_cid}] | 消息：{target_msg}")
                # 若手动下发应答指令，开启权限
                if target_msg == REPLY_TRIGGER:
                    set_reply_permission(target_cid, True)
                    print(f"🔓 客户端[{target_cid}] | 手动开启应答权限")
                continue
            # 无效输入
            print(f"❌ 无效指令 | 输入list查看帮助")
    except Exception as e:
        if state.is_connected():
            print(f"❌ 手动操作线程异常 | {str(e)[:30]}...")
    finally:
        print(f"📤 客户端[{client_id}] | 手动操作线程已终止")

# ---------------------- 客户端连接处理 ----------------------
def handle_single_client(conn: socket.socket, addr):
    """处理单个客户端完整生命周期"""
    client_id = get_next_client_id()
    conn_state = ConnectionState()
    add_online_client(client_id, conn, addr, conn_state)
    # 打印连接信息
    print(f"\n" + "="*60)
    print(f"✅ 新客户端连接 | ID:{client_id} | 地址:{addr}")
    print(f"✅ 连接时间：{time.strftime('%Y-%m-%d %H:%M:%S')} | 在线数:{len(online_clients)}")
    print(f"="*60 + "\n")
    try:
        # 启动收发线程
        t_recv = threading.Thread(target=recv_thread, args=(client_id, conn, addr, conn_state), daemon=True)
        t_send = threading.Thread(target=send_thread, args=(client_id, conn, conn_state), daemon=True)
        t_recv.start()
        t_send.start()
        t_recv.join()
        t_send.join()
    finally:
        conn.close()
        print(f"🔌 客户端[{client_id}] | 连接已释放")
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
    # 启动全局队列监听线程（守护线程）
    t_queue = threading.Thread(target=queue_listen_thread, daemon=True)
    t_queue.start()
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