#!/usr/bin/env python3
import socket
import threading
import sys

from common.util import setup_logging, now_ts, gen_id
from common.proto import ChatMessage
from common.framing import pack_message, recv_framed

log = setup_logging("client")


def net_reader(sock: socket.socket):
    while True:
        payload = recv_framed(sock)
        if payload is None:
            print("[Conexión cerrada por el servidor]")
            break
        try:
            msg = ChatMessage.from_bytes(payload)
        except Exception as e:
            log.warning(f"Mensaje inválido/JSON desconocido: {e}")
            continue

        # Mostrar según destino
        dest = (msg.to or "*")
        if dest != "*":
            # Mensaje privado
            print(f"[privado {msg.from_id}→{dest}] {msg.msg}")
        elif msg.from_id == "server":
            # Mensaje informativo del servidor
            print(f"[*] {msg.msg}")
        else:
            # Mensaje grupal
            print(f"[{msg.from_id}] {msg.msg}")



def main():
    if len(sys.argv) < 3:
        print("Uso: python client_tcp.py <IP_SERVIDOR> <PUERTO>")
        print("Ej:  python client_tcp.py 127.0.0.1 5555")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((host, port))
        reader = threading.Thread(target=net_reader, args=(sock,), daemon=True)
        reader.start()

        try:
            while True:
                line = sys.stdin.readline()
                if not line:
                    break
                line = line.rstrip("\n")

                cmd = None
                text = line
                if line.startswith("/"):
                    # comandos: /who, /nick <alias>, /quit
                    if line == "/who":
                        cmd = "who"
                        text = ""
                    elif line.startswith("/nick "):
                        cmd = f"nick {line.split(' ', 1)[1]}"
                        text = ""
                    elif line == "/quit":
                        cmd = "quit"
                        text = ""
                    elif line.startswith("/msg "):
                        parts = line.split(" ", 2)
                        if len(parts) < 3:
                            print("Uso: /msg <destinatario> <mensaje>")
                            continue
                        dest, text = parts[1], parts[2]
                        chat = ChatMessage(
                            from_id="", msg=text, ts=now_ts(), mid=gen_id(), cmd=None, to=dest
                        )
                        sock.sendall(pack_message(chat.to_bytes()))
                        continue
                    
                    else:
                        print("Comandos: /who, /nick <alias>, /quit")
                        continue

                chat = ChatMessage(
                    from_id="",  # el server mostrará tu IP o alias
                    msg=text,
                    ts=now_ts(),
                    mid=gen_id(),
                    cmd=cmd,
                )
                sock.sendall(pack_message(chat.to_bytes()))

                if cmd == "quit":
                    break
        except KeyboardInterrupt:
            pass

    print("Cliente terminado")


if __name__ == "__main__":
    main()