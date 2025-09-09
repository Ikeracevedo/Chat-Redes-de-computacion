#!/usr/bin/env python3
import argparse, subprocess, time, csv, sys, os
from pathlib import Path

def run_spammer(host, port, size, count, dest):
    # usar el MISMO intérprete y ruta absoluta al spammer
    here = os.path.dirname(os.path.abspath(__file__))
    spammer = os.path.join(here, "spammer.py")
    cmd = [sys.executable, spammer, "--host", host, "--port", str(port),
           "--size", str(size), "--count", str(count), "--to", dest]
    out = subprocess.check_output(cmd, text=True).strip()
    return out

def main():
    ap = argparse.ArgumentParser(description="Corre una batería de tamaños y guarda CSV con resultados.")
    ap.add_argument("--host", required=True)
    ap.add_argument("--port", type=int, default=5555)
    ap.add_argument("--sizes", default="1,64,512,1024,4096,16384,65536")
    ap.add_argument("--count", type=int, default=100)
    ap.add_argument("--to", default="*")
    ap.add_argument("--outfile", default=None)
    args = ap.parse_args()

    sizes = [int(s.strip()) for s in args.sizes.split(",") if s.strip()]
    ts = int(time.time())
    outdir = Path("resultados"); outdir.mkdir(parents=True, exist_ok=True)
    outfile = Path(args.outfile) if args.outfile else outdir / f"size_results_{ts}.csv"

    rows = []
    for sz in sizes:
        print(f"==> size {sz} bytes")
        out = run_spammer(args.host, args.port, sz, args.count, args.to)
        print(out)

        # Parse robusto: tokens "clave=valor"
        parts = {}
        for tok in out.split():
            if "=" in tok:
                k, v = tok.split("=", 1)
                parts[k] = v

        row = {
            "host": parts.get("host",""),
            "to": parts.get("to",""),
            "size": int(parts.get("size","0").rstrip("B")),
            "count": int(parts.get("count","0")),
            "duration_s": float(parts.get("duration","0")),
            "app_throughput_KiB_s": float(parts.get("app_throughput_KiB_s","0")),
        }
        rows.append(row)

    with open(outfile, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["host","to","size","count","duration_s","app_throughput_KiB_s"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nCSV guardado en: {outfile}")

if __name__ == "__main__":
    main()
