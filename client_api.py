# client.py 客户端程序
import socket
import re
import threading
from server.enhanced_server.global_mq import END_MARK, EXIT_CMD, REPLY_TRIGGER, ENCODING

# 客户端网络配置
SERVER_HOST = '127.0.0.1'  # 局域网重连改为服务端实际IP
SERVER_PORT = 19278
BUFFER_SIZE = 4096
CONNECT_TIMEOUT = 10       # 连接超时时间（秒）

# 线程安全的连接状态
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

# ---------------------- 消息收发 ----------------------
def recv_thread(conn: socket.socket, state: ConnectionState):
    """接收线程：实时接收服务端消息，区分普通数据、应答指令、权限拒绝"""
    print(f"📥 接收线程已启动 | 实时监听服务端消息")
    try:
        while state.is_connected():
            resp_data = b''
            while state.is_connected():
                chunk = conn.recv(BUFFER_SIZE)
                if not chunk:
                    raise ConnectionResetError("与服务端连接断开")
                resp_data += chunk
                if b'0\r\n\r\n' in resp_data and END_MARK.encode(ENCODING) in resp_data:
                    break
            # 解析消息
            resp_str = resp_data.decode(ENCODING, errors='ignore')
            pattern = r'Keep-Alive: .*?\n.*?\n(.*?)\[END\]'
            msg_match = re.search(pattern, resp_str, re.DOTALL)
            # msg_match = re.search(r'\r\n(.*?)' + END_MARK, resp_str, re.DOTALL)
            if not msg_match:
                print(f"❌ 服务端消息解析失败")
                continue
            # server_msg = msg_match.group(1).strip()
            server_msg = msg_match.group(1).strip().split("\n")[1]

            # 消息类型判断与展示
            if server_msg == REPLY_TRIGGER:
                print(f"\n🔔 【服务端指令】→ {server_msg}（现在可发送应答消息，单次有效）")
            elif server_msg.startswith("【权限拒绝】"):
                print(f"\n🚫 {server_msg}")
            elif server_msg.startswith("【消息已接收】"):
                print(f"\n✅ {server_msg}")
            elif EXIT_CMD in server_msg or "Session结束" in server_msg:
                print(f"\n📤 【服务端指令】→ {server_msg}")
                state.set_disconnected()
                break
            else:
                print(f"\n📊 【服务端数据】→ {server_msg}")

    except (ConnectionResetError, BrokenPipeError, OSError) as e:
        if state.is_connected():
            print(f"\n❌ 与服务端连接断开 | 原因：{str(e)[:20]}...")
            state.set_disconnected()
    finally:
        print(f"📥 接收线程已终止")

def send_thread(conn: socket.socket, state: ConnectionState):
    """发送线程：支持连续发送消息，由服务端控制是否接收"""
    print(f"📤 发送线程已启动")
    print(f"💡 发送规则：输入消息直接发送，{EXIT_CMD}=断开连接")
    print(f"⚠️  提示：仅当收到「请客户端回答」指令时，消息才会被接收\n")
    try:
        while state.is_connected():
            client_msg = input(f"📤 客户端发送 > ").strip()
            if not client_msg:
                continue
            # 退出命令
            if client_msg == EXIT_CMD:
                send_http_request(conn, client_msg)
                state.set_disconnected()
                print(f"📤 客户端发送退出命令，即将断开")
                break
            # 发送普通消息
            send_http_request(conn, client_msg)
            print(f"📤 消息已发出 | 等待服务端处理...")
    except Exception as e:
        if state.is_connected():
            print(f"\n❌ 发送失败 | 与服务端连接已断开")
    finally:
        print(f"📤 发送线程已终止")

def send_http_request(conn: socket.socket, msg: str):
    """构造HTTP 1.1长连接POST请求"""
    request_body = f"{msg}{END_MARK}"
    headers = (
        f"POST /queue-driver HTTP/1.1\r\n"
        f"Host: {SERVER_HOST}:{SERVER_PORT}\r\n"
        f"Connection: Keep-Alive\r\n"
        f"Content-Length: {len(request_body)}\r\n"
        f"Content-Type: text/plain; charset={ENCODING}\r\n"
        "Keep-Alive: timeout=300, max=0\r\n"
        "\r\n"
    )
    full_req = headers.encode(ENCODING) + request_body.encode(ENCODING)
    conn.sendall(full_req)

# ---------------------- 客户端主启动 ----------------------
def start_client():
    """启动客户端，支持断开重连，适配应答权限控制"""
    client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_sock.settimeout(CONNECT_TIMEOUT)
    try:
        client_sock.connect((SERVER_HOST, SERVER_PORT))
        client_sock.settimeout(None)  # 取消连接超时
        # 打印连接成功信息
        print(f"\n" + "="*60)
        print(f"✅ 客户端连接成功 | 服务端：{SERVER_HOST}:{SERVER_PORT}")
        print(f"✅ 长连接Session已建立 | 支持重连/异步收发")
        print(f"🎯 核心规则：仅收到「请客户端回答」后，消息才会被接收")
        print(f"💡 操作提示：输入消息直接发送，{EXIT_CMD}=断开连接")
        print(f"="*60 + "\n")
        # 启动收发线程
        conn_state = ConnectionState()
        t_recv = threading.Thread(target=recv_thread, args=(client_sock, conn_state), daemon=True)
        t_send = threading.Thread(target=send_thread, args=(client_sock, conn_state), daemon=True)
        t_recv.start()
        t_send.start()
        t_recv.join()
        t_send.join()
    except socket.timeout:
        print(f"❌ 连接超时 | 服务端未启动或地址不可达")
    except ConnectionRefusedError:
        print(f"❌ 连接被拒绝 | 请先启动服务端！")
    except KeyboardInterrupt:
        print(f"\n⚠️  客户端收到中断信号，即将退出")
    finally:
        client_sock.close()
        print(f"\n🔌 客户端连接已释放 | 如需重连，直接重启本程序即可")

start_client()