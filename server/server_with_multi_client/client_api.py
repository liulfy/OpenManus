import socket
import re
import threading
import time

# 全局配置（与服务端严格一致）
SERVER_HOST = '127.0.0.1'  # 局域网重连改为服务端实际IP（如192.168.1.100）
SERVER_PORT = 8080
BUFFER_SIZE = 4096
END_MARK = '[END]'
EXIT_CMD = 'exit'
ENCODING = 'utf-8'
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

def recv_thread(conn: socket.socket, state: ConnectionState):
    """接收线程：实时接收服务端消息（含精准下发消息）"""
    print(f"📥 接收线程已启动 | 实时接收服务端消息（含精准下发）")
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
            # 解析服务端消息
            resp_str = resp_data.decode(ENCODING, errors='ignore')
            msg_match = re.search(r'\r\n(.*?)' + END_MARK, resp_str, re.DOTALL)
            if msg_match:
                server_msg = msg_match.group(1).strip()
                # 区分普通消息和精准下发消息，优化展示
                if server_msg.startswith("[服务端精准下发]"):
                    print(f"\n🎯 【服务端精准下发】→ 消息：{server_msg.replace('[服务端精准下发]', '').strip()}")
                else:
                    print(f"\n✅ 【服务端普通消息】→ 消息：{server_msg}")
                # 检测服务端退出命令
                if EXIT_CMD in server_msg or "Session结束" in server_msg:
                    print(f"📤 服务端发送退出命令，准备断开连接")
                    state.set_disconnected()
                    break
    except (ConnectionResetError, BrokenPipeError, OSError) as e:
        if state.is_connected():
            print(f"\n❌ 与服务端连接断开 | 原因：{str(e)[:20]}...")
            state.set_disconnected()
    finally:
        print(f"📥 接收线程已终止")

def send_thread(conn: socket.socket, state: ConnectionState):
    """发送线程：支持连续发送消息，输入exit断开"""
    print(f"📤 发送线程已启动 | 可连续发送消息，输入{EXIT_CMD}断开\n")
    try:
        while state.is_connected():
            client_msg = input(f"📤 客户端发送消息：")
            if not client_msg:
                continue
            if client_msg == EXIT_CMD:
                send_http_request(conn, client_msg)
                state.set_disconnected()
                print(f"📤 客户端发送退出命令，即将断开")
                break
            send_http_request(conn, client_msg)
            print(f"✅ 客户端消息已发送：{client_msg}")
    except (BrokenPipeError, OSError):
        if state.is_connected():
            print(f"\n❌ 消息发送失败 | 与服务端连接已断开")
            state.set_disconnected()
    finally:
        print(f"📤 发送线程已终止")

def send_http_request(conn: socket.socket, msg: str):
    """构造HTTP 1.1长连接POST请求"""
    request_body = f"{msg}{END_MARK}"
    headers = (
        f"POST /precision-send HTTP/1.1\r\n"
        f"Host: {SERVER_HOST}:{SERVER_PORT}\r\n"
        f"Connection: Keep-Alive\r\n"
        f"Content-Length: {len(request_body)}\r\n"
        f"Content-Type: text/plain; charset={ENCODING}\r\n"
        "Keep-Alive: timeout=300, max=0\r\n"
        "\r\n"
    )
    full_req = headers.encode(ENCODING) + request_body.encode(ENCODING)
    conn.sendall(full_req)

def start_reconnect_client():
    """启动客户端，支持断开重连，兼容服务端精准下发"""
    client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_sock.settimeout(CONNECT_TIMEOUT)
    try:
        client_sock.connect((SERVER_HOST, SERVER_PORT))
        client_sock.settimeout(None)  # 取消连接超时，恢复正常收发
        # 打印连接成功核心信息
        print(f"\n" + "="*60)
        print(f"✅ 客户端连接成功 | 服务端：{SERVER_HOST}:{SERVER_PORT}")
        print(f"✅ 长连接Session已建立 | 支持重连/异步连发")
        print(f"🎯 兼容特性：接收服务端精准下发消息、普通消息")
        print(f"💡 操作规则：直接输入=发送消息，{EXIT_CMD}=断开，重启=重连")
        print(f"="*60 + "\n")
        # 初始化状态，启动收发线程
        conn_state = ConnectionState()
        t_recv = threading.Thread(target=recv_thread, args=(client_sock, conn_state), daemon=True)
        t_send = threading.Thread(target=send_thread, args=(client_sock, conn_state), daemon=True)
        t_recv.start()
        t_send.start()
        # 等待线程结束
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


start_reconnect_client()