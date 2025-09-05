from common.framing import pack_message, HEADER_SIZE, recv_framed
import socket
import threading


def test_pack_and_recv():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen()
    host, port = server.getsockname()

    def server_thread():
        conn, _ = server.accept()
        data = recv_framed(conn)
        assert data == b"hola"
        conn.close()
        server.close()

    th = threading.Thread(target=server_thread, daemon=True)
    th.start()

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((host, port))
    client.sendall(pack_message(b"hola"))
    client.close()