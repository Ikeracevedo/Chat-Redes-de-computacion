import struct
from typing import Optional

HEADER_FMT = ">I" # unsigned int, big-endian
HEADER_SIZE = struct.calcsize(HEADER_FMT)

def pack_message(payload: bytes) -> bytes:
    return struct.pack(HEADER_FMT, len(payload)) + payload

def read_exact(sock, n: int) -> Optional[bytes]:
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            return None
        data += chunk
    return data

def recv_framed(sock) -> Optional[bytes]:
    header = read_exact(sock, HEADER_SIZE)
    if header is None:
        return None
    (length,) = struct.unpack(HEADER_FMT, header)
    if length == 0:
        return b""
    payload = read_exact(sock, length)
    return payload

