#!/usr/bin/env python3
import socket, argparse, time, uuid, json, struct

def pack_message(payload: bytes) -> bytes:
    return struct.pack(">I", len(payload)) + payload

def mk_chat_payload(text: str, to: str):
    now = time.time()
    mid = str(uuid.uuid4())
    obj = {
        "from_id": "",
        "msg": text,
        "ts": now,
        "mid": mid,
        "cmd": None,
        "to": to or "*",
    }
    return json.dumps(obj, ensure_ascii=False).encode("utf-8")

def main():
    ap = argparse.ArgumentParser(description="Enviar N mensajes de tamaño fijo al servidor del chat.")
    ap.add_argument("--host", required=True)
    ap.add_argument("--port", type=int, default=5555)
    ap.add_argument("--size", type=int, default=1024)     # tamaño del campo 'msg'
    ap.add_argument("--count", type=int, default=100)     # número de mensajes
    ap.add_argument("--to", default="*")                  # '*' = broadcast; alias/IP = privado
    args = ap.parse_args()

    text = "x" * args.size

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((args.host, args.port))
        # Warm-up para evitar efectos de arranque
        s.sendall(pack_message(mk_chat_payload("warmup", args.to)))

        t0 = time.time()
        total_sent = 0
        for _ in range(args.count):
            payload = mk_chat_payload(text, args.to)
            s.sendall(pack_message(payload))
            total_sent += len(payload)  # bytes a nivel app (JSON)
        dur = max(time.time() - t0, 1e-9)
        thr_kib_s = (total_sent / 1024.0) / dur

        # FORMATO LIMPIO, claves fijas que size_runner entiende:
        print(
            f"host={args.host} to={args.to} size={args.size}B count={args.count} "
            f"duration={dur:.6f} app_throughput_KiB_s={thr_kib_s:.2f}"
        )

if __name__ == "__main__":
    main()
