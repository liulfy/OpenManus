import socket
import re
import threading
import time
from typing import Dict, Tuple, Optional

# 全局配置（客户端需严格一致）
HOST = '0.0.0.0'         # 绑定所有网卡，支持本地/局域网连接
PORT = 8080
BUFFER_SIZE = 4096
END_MARK = '[END]'       # 单轮消息结束标识
EXIT_CMD = 'exit'        # 主动退出命令
ENCODING = 'utf-8'       # 消息编码
MAX_LISTEN_QUEUE = 20    # 最大监听队列，支持更多客户端同时等待

# 客户端连接信息：(socket连接, 客户端地址, 连接状态)
ClientConn = Tuple[socket.socket, Tuple[str, int], 'ConnectionState']
# 在线客户端映射表：{客户端ID: 连接信息}
online_clients: Dict[int, ClientConn] = {}
# 全局锁：保证映射表和ID生成器的线程安全
client_lock = threading.Lock()
# 客户端唯一ID生成器（自增，保证全局唯一）
client_id_generator = 1

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

def get_next_client_id() -> int:
    """生成下一个全局唯一的客户端ID（线程安全）"""
    global client_id_generator
    with client_lock:
        current_id = client_id_generator
        client_id_generator += 1
    return current_id

def add_online_client(client_id: int, conn: socket.socket, addr: Tuple[str, int], state: ConnectionState):
    """将客户端添加到在线映射表（线程安全）"""
    with client_lock:
        online_clients[client_id] = (conn, addr, state)
    print(f"📇 客户端[{client_id}] | 已加入在线列表，当前在线数：{get_online_client_count()}")

def remove_online_client(client_id: int):
    """将客户端从在线映射表移除（线程安全）"""
    with client_lock:
        if client_id in online_clients:
            del online_clients[client_id]
    print(f"📇 客户端[{client_id}] | 已移出在线列表，当前在线数：{get_online_client_count()}")

def get_online_client_count() -> int:
    """获取当前在线客户端数量（线程安全）"""
    with client_lock:
        return len(online_clients)

def get_online_clients() -> Dict[int, Tuple[str, int]]:
    """获取当前所有在线客户端信息 {ID: 地址}（线程安全）"""
    with client_lock:
        return {cid: addr for cid, (_, addr, _) in online_clients.items()}

def get_client_conn(client_id: int) -> Optional[ClientConn]:
    """根据ID获取客户端连接信息（线程安全），不存在则返回None"""
    with client_lock:
        return online_clients.get(client_id)

def print_online_clients():
    """打印当前所有在线客户端列表，方便服务端选择下发"""
    online = get_online_clients()
    if not online:
        print(f"\n📭 当前无在线客户端！")
        return
    print(f"\n📭 当前在线客户端列表（共{len(online)}个）：")
    for cid, addr in online.items():
        print(f"   → 客户端ID：{cid} | 连接地址：{addr[0]}:{addr[1]}")
    print("-" * 40)

def recv_thread(client_id: int, conn: socket.socket, addr, state: ConnectionState):
    """接收线程：独立接收指定客户端消息，异常时移除映射表"""
    print(f"📥 客户端[{client_id}] | 接收线程已启动")
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
            body_match = re.search(r'\r\n\r\n(.*?)' + END_MARK, request_str, re.DOTALL)
            if body_match:
                client_msg = body_match.group(1).strip()
                print(f"\n✅ 客户端[{client_id}] | 收到消息：{client_msg}")
                if client_msg == EXIT_CMD:
                    print(f"📤 客户端[{client_id}] | 发送退出命令，准备断开")
                    send_http_response(conn, f"服务端已接收退出命令，连接即将关闭{END_MARK}")
                    state.set_disconnected()
                    break
    except (ConnectionResetError, BrokenPipeError, OSError) as e:
        if state.is_connected():
            print(f"❌ 客户端[{client_id}] | 连接断开（{str(e)[:20]}...）")
            state.set_disconnected()
    finally:
        remove_online_client(client_id)  # 无论何种原因断开，均移出映射表
        print(f"📥 客户端[{client_id}] | 接收线程已终止")

def send_thread(client_id: int, conn: socket.socket, addr, state: ConnectionState):
    """发送线程：支持【查看在线客户端】+【精准下发】+【本客户端单独发送】"""
    print(f"📤 客户端[{client_id}] | 发送线程已启动")
    print(f"💡 客户端[{client_id}] | 发送规则：")
    print(f"   1. 输入 list → 查看所有在线客户端")
    print(f"   2. 输入 ID+消息 → 精准下发给指定ID客户端（如 2你好客户端2）")
    print(f"   3. 输入 exit → 断开当前客户端连接")
    print(f"   4. 直接输入消息 → 仅发送给当前客户端[{client_id}]\n")
    try:
        while state.is_connected():
            # todo 这里直接将服务端的内容输出下来
            server_input = input(f"📤 服务端 | 输入发送内容：")
            if not server_input:
                continue
            # 命令1：查看在线客户端列表
            if server_input.strip().lower() == 'list':
                print_online_clients()
                continue
            # 命令2：退出当前客户端连接
            if server_input.strip() == EXIT_CMD:
                send_http_response(conn, f"服务端主动断开，Session结束{END_MARK}")
                state.set_disconnected()
                break
            # 尝试解析：是否为精准下发（以数字ID开头）
            target_cid = None
            send_msg = server_input
            if server_input[0].isdigit():
                # 分离ID和消息（如"2你好" → ID=2，消息="你好"）
                for i, char in enumerate(server_input):
                    if not char.isdigit():
                        target_cid = int(server_input[:i])
                        send_msg = server_input[i:].strip()
                        break
                # 无消息内容则忽略
                if not send_msg:
                    print(f"❌ 精准下发失败 | 请输入【ID+消息内容】（如 2你好）")
                    continue
            # 精准下发：发送给指定ID客户端
            if target_cid is not None:
                target_conn = get_client_conn(target_cid)
                if not target_conn:
                    print(f"❌ 精准下发失败 | 客户端[{target_cid}]不存在或已离线！")
                else:
                    target_sock, target_addr, _ = target_conn
                    send_http_response(target_sock, f"[服务端精准下发] {send_msg}{END_MARK}")
                    print(f"✅ 精准下发成功 | 客户端[{target_cid}]（{target_addr}）| 消息：{send_msg}")
            # 普通发送：仅发送给当前客户端
            else:
                send_http_response(conn, f"{send_msg}{END_MARK}")
                print(f"✅ 发送成功 | 客户端[{client_id}] | 消息：{send_msg}")
    except (BrokenPipeError, OSError):
        if state.is_connected():
            print(f"❌ 客户端[{client_id}] | 发送失败，连接已断开")
            state.set_disconnected()
    finally:
        print(f"📤 客户端[{client_id}] | 发送线程已终止")

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

def handle_single_client(conn: socket.socket, addr):
    """处理单个客户端完整生命周期：分配ID→加入映射表→启动线程→释放资源"""
    # 分配唯一ID，初始化连接状态
    client_id = get_next_client_id()
    conn_state = ConnectionState()
    # 将客户端加入在线映射表
    add_online_client(client_id, conn, addr, conn_state)
    # 打印连接成功信息
    print(f"\n" + "="*60)
    print(f"✅ 新客户端连接 | ID：{client_id} | 地址：{addr}")
    print(f"✅ 连接时间：{time.strftime('%Y-%m-%d %H:%M:%S')} | 当前在线数：{get_online_client_count()}")
    print(f"="*60 + "\n")
    try:
        # 启动独立的收发线程（守护线程）
        t_recv = threading.Thread(target=recv_thread, args=(client_id, conn, addr, conn_state), daemon=True)
        t_send = threading.Thread(target=send_thread, args=(client_id, conn, addr, conn_state), daemon=True)
        t_recv.start()
        t_send.start()
        # 等待收发线程结束
        t_recv.join()
        t_send.join()
    finally:
        # 关闭当前客户端socket，不影响服务端主监听
        conn.close()
        print(f"🔌 客户端[{client_id}] | 连接已释放")
        print(f"="*60 + "\n")

def start_permanent_server():
    """启动永久运行的服务端，支持多客户端精准下发"""
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((HOST, PORT))
    server_sock.listen(MAX_LISTEN_QUEUE)
    # 打印启动核心信息
    print(f"🚀 多客户端精准下发服务端已启动 | 永久运行模式")
    print(f"📌 监听地址：{HOST}:{PORT} | 支持多客户端并发/重连")
    print(f"🎯 核心特性：精准指定客户端下发、在线列表查看、异步连发")
    print(f"⚙️  核心命令：list=查看在线、ID+消息=精准下发、exit=断开当前\n")

    try:
        # 无限循环监听，永久等待客户端连接
        while True:
            conn, addr = server_sock.accept()
            # 为每个客户端创建独立线程，主线程继续监听
            threading.Thread(target=handle_single_client, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        print(f"\n⚠️  服务端收到中断信号，即将优雅关闭")
    finally:
        # 关闭主监听socket，清理所有在线客户端
        server_sock.close()
        with client_lock:
            online_clients.clear()
        print(f"🔒 服务端主监听已关闭 | 所有客户端连接已清理")


start_permanent_server()