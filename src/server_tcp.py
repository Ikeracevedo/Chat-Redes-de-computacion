#!/usr/bin/env python3
import socket
import threading
from typing import Dict

from common.util import setup_logging, now_ts, gen_id
from common.proto import ChatMessage
from common.framing import pack_message, recv_framed

HOST = "0.0.0.0"  # escucha en todas las interfaces
PORT = 5555

log = setup_logging("server")

clients_lock = threading.Lock()
clients: Dict[socket.socket, str] = {}


def broadcast(sender_sock: socket.socket, msg_bytes: bytes):
    with clients_lock:
        dead = []
        for sock in clients.keys():
            if sock is sender_sock:
                continue
            try:
                sock.sendall(msg_bytes)
            except Exception as e:
                log.warning(f"Error enviando a {sock}: {e}")
                dead.append(sock)
        for d in dead:
            alias = clients.pop(d, "?")
            log.info(f"Cliente removido: {alias}")
            try:
                d.close()
            except Exception:
                pass


def handle_client(sock: socket.socket, addr):
    peer_ip = addr[0]
    with clients_lock:
        clients[sock] = peer_ip  # alias por defecto = IP
    log.info(f"Conectado {peer_ip}")

    # Mensaje de bienvenida
    welcome = ChatMessage(
        from_id="server",
        msg=f"Bienvenido {peer_ip}! Usa /who, /nick <alias>, /quit",
        ts=now_ts(),
        mid=gen_id(),
    )
    try:
        sock.sendall(pack_message(welcome.to_bytes()))
    except Exception:
        pass

    try:
        while True:
            payload = recv_framed(sock)
            if payload is None:
                break
            try:
                chat = ChatMessage.from_bytes(payload)
            except Exception as e:
                log.warning(f"Payload inválido de {peer_ip}: {e} {payload!r}")
                continue
            if chat.cmd:  # comandos
                if chat.cmd == "who":
                    with clients_lock:
                        lista = ", ".join(sorted(set(clients.values())))
                    reply = ChatMessage(
                        from_id="server",
                        msg=f"Conectados: {lista}",
                        ts=now_ts(),
                        mid=gen_id(),
                    )
                    sock.sendall(pack_message(reply.to_bytes()))
                    continue
                if chat.cmd.startswith("nick "):
                    new_alias = chat.cmd.split(" ", 1)[1].strip()
                    if new_alias:
                        with clients_lock:
                            clients[sock] = new_alias
                        info = ChatMessage(
                            from_id="server",
                            msg=f"Alias actualizado a {new_alias}",
                            ts=now_ts(),
                            mid=gen_id(),
                        )
                        sock.sendall(pack_message(info.to_bytes()))
                        continue
                if chat.cmd == "quit":
                    break

            # Mensaje normal → retransmitir
            sender_alias = None
            with clients_lock:
                sender_alias = clients.get(sock, peer_ip)
            forward = ChatMessage(
                from_id=sender_alias,
                msg=chat.msg,
                ts=chat.ts,
                mid=chat.mid,
            )
            packed = pack_message(forward.to_bytes())
            broadcast(sock, packed)

    except Exception as e:
        log.warning(f"Error con {peer_ip}: {e}")
    finally:
        with clients_lock:
            alias = clients.pop(sock, peer_ip)
        log.info(f"Desconectado {alias}")
        try:
            sock.close()
        except Exception:
            pass


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen()
        log.info(f"Servidor escuchando en {HOST}:{PORT}")
        while True:
            client_sock, addr = server.accept()
            th = threading.Thread(target=handle_client, args=(client_sock, addr), daemon=True)
            th.start()


if __name__ == "__main__":
    main()