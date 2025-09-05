#!/usr/bin/env python3
import socket
import threading
from typing import Dict, Set, List

from common.util import setup_logging, now_ts, gen_id
from common.proto import ChatMessage
from common.framing import pack_message, recv_framed

HOST = "0.0.0.0"  # escucha en todas las interfaces
PORT = 5555

log = setup_logging("server")

# Mapa de sockets -> alias (por defecto, la IP)
clients_lock = threading.Lock()
clients: Dict[socket.socket, str] = {}

def send_safe(s: socket.socket, data: bytes) -> None:
    try:
        s.sendall(data)
    except Exception as e:
        log.warning(f"Error enviando a cliente: {e}")

def handle_client(sock: socket.socket, addr):
    peer_ip = addr[0]
    # registrar cliente con alias por defecto = IP
    with clients_lock:
        clients[sock] = peer_ip
    log.info(f"Conectado {peer_ip}")

    # Mensaje de bienvenida
    welcome = ChatMessage(
        from_id="server",
        msg="Bienvenido! Comandos: /who, /nick <alias>, /quit, /msg <dest> <texto>",
        ts=now_ts(),
        mid=gen_id(),
        to="*",
    )
    try:
        send_safe(sock, pack_message(welcome.to_bytes()))
    except Exception:
        pass

    try:
        while True:
            payload = recv_framed(sock)
            if payload is None:
                # conexión cerrada por el cliente
                break

            # Intentar parsear como ChatMessage
            try:
                chat = ChatMessage.from_bytes(payload)
            except Exception as e:
                log.warning(f"Payload inválido de {peer_ip}: {e} | {payload!r}")
                continue

            # --- Comandos ---
            if chat.cmd:
                cmd = chat.cmd.strip()
                if cmd == "who":
                    with clients_lock:
                        lista = ", ".join(sorted(set(clients.values())))
                    reply = ChatMessage(
                        from_id="server",
                        msg=f"Conectados: {lista if lista else '(ninguno)'}",
                        ts=now_ts(),
                        mid=gen_id(),
                        to="*",
                    )
                    send_safe(sock, pack_message(reply.to_bytes()))
                    continue

                if cmd.startswith("nick "):
                    new_alias = cmd.split(" ", 1)[1].strip()
                    if new_alias:
                        with clients_lock:
                            clients[sock] = new_alias
                        info = ChatMessage(
                            from_id="server",
                            msg=f"Alias actualizado a {new_alias}",
                            ts=now_ts(),
                            mid=gen_id(),
                            to="*",
                        )
                        send_safe(sock, pack_message(info.to_bytes()))
                    else:
                        err = ChatMessage(
                            from_id="server",
                            msg="Uso: /nick <alias>",
                            ts=now_ts(),
                            mid=gen_id(),
                            to="*",
                        )
                        send_safe(sock, pack_message(err.to_bytes()))
                    continue

                if cmd == "quit":
                    # cierre limpio solicitado por el cliente
                    break

                # comando no reconocido
                err = ChatMessage(
                    from_id="server",
                    msg="Comandos: /who, /nick <alias>, /quit, /msg <dest> <texto>",
                    ts=now_ts(),
                    mid=gen_id(),
                    to="*",
                )
                send_safe(sock, pack_message(err.to_bytes()))
                continue

            # --- Mensaje normal: grupal o privado ---
            with clients_lock:
                sender_alias = clients.get(sock, peer_ip)

            dest = (chat.to or "*").strip()

            # Construir el mensaje a reenviar (preservando 'to')
            forward = ChatMessage(
                from_id=sender_alias,
                msg=chat.msg,
                ts=chat.ts,
                mid=chat.mid,
                to=dest,
            )
            packed = pack_message(forward.to_bytes())

            log.info(f"[RX] from={sender_alias} to={dest} msg={chat.msg!r}")

            with clients_lock:
                if dest == "*" or dest.lower() == "all":
                    # Broadcast: a todos menos el remitente
                    for s in list(clients.keys()):
                        if s is not sock:
                            send_safe(s, packed)
                else:
                    # Privado o multicast: soporta "B" / "C" / "B,C" / "192.168.10.13"
                    targets: List[str] = [d.strip() for d in dest.split(",") if d.strip()]
                    dest_socks: Set[socket.socket] = set()

                    for s, alias in clients.items():
                        # 1) match por alias (recomendado en localhost)
                        if alias in targets:
                            dest_socks.add(s)
                            continue
                        # 2) match por IP (útil en la red real)
                        try:
                            ip = s.getpeername()[0]
                        except Exception:
                            ip = None
                        if ip and ip in targets:
                            dest_socks.add(s)

                    log.info(f"[ROUTE] targets={targets} resolved={len(dest_socks)}")

                    if not dest_socks:
                        info = ChatMessage(
                            from_id="server",
                            msg=f"Destino no encontrado: {dest}",
                            ts=now_ts(),
                            mid=gen_id(),
                            to="*",
                        )
                        send_safe(sock, pack_message(info.to_bytes()))
                    else:
                        for s in dest_socks:
                            if s is not sock:  # sin eco al remitente
                                send_safe(s, packed)

    except Exception as e:
        log.warning(f"Error con {peer_ip}: {e}")
    finally:
        # limpieza al desconectar
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
