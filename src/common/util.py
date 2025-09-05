import logging
import socket
import time
import uuid

def setup_logging(name: str = "chat", level: int = logging.INFO) -> logging.Logger:
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    return logging.getLogger(name)

def now_ts() -> float:
    return time.time()

def gen_id() -> str:
    return str(uuid.uuid4())


def socket_peer_name(sock: socket.socket) -> str:
    try:
        host,port = sock.getpeername()
        return f"{host}:{port}"
    except Exception:
        return "unknown"