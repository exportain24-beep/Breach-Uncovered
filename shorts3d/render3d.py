"""Render a 3D shot list to video frames with headless Chromium (WebGL/three.js) and pipe them into ffmpeg.
usage: python3 render3d.py shots.json out_silent.mp4 [--w 1080 --h 1920 --fps 24 --seconds N --still T out.png]"""
import argparse, json, os, subprocess, sys, threading, time, http.server, socketserver, functools
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))

def serve():
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    srv = socketserver.ThreadingTCPServer(("127.0.0.1", 0), functools.partial(Q, directory=HERE)); srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start(); return srv, srv.server_address[1]

def open_page(p, port, w, h):
    b = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist", "--disable-gpu-vsync"])
    pg = b.new_page(viewport={"width": w, "height": h}); pg.on("console", lambda m: print("[browser]", m.text[:300]) if "ERR" in m.text or "rror" in m.text else None)
    pg.goto(f"http://127.0.0.1:{port}/player.html?w={w}&h={h}"); pg.wait_for_function("window.ready===true || window.err", timeout=120000)
    if pg.evaluate("window.err"): raise SystemExit("player error: " + pg.evaluate("window.err"))
    return b, pg

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("shots"); ap.add_argument("out", nargs="?"); ap.add_argument("--w", type=int, default=1080); ap.add_argument("--h", type=int, default=1920)
    ap.add_argument("--fps", type=int, default=24); ap.add_argument("--seconds", type=float); ap.add_argument("--still", type=float, nargs="*"); ap.add_argument("--stills_out", default="/tmp/still")
    a = ap.parse_args(); shots = json.load(open(a.shots)); total = shots[-1]["t1"] if isinstance(shots, list) else 0
    srv, port = serve()
    with sync_playwright() as p:
        b, pg = open_page(p, port, a.w, a.h); pg.evaluate("s => window.loadShots(s)", shots)
        if a.still:
            for t in a.still:
                pg.evaluate(f"window.draw({t})"); pg.locator("#c").screenshot(path=f"{a.stills_out}_{t:.1f}.png", type="png"); print("still", t)
            b.close(); return
        if a.seconds: total = min(total, a.seconds)
        n = int(total * a.fps); t0 = time.time()
        ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "image2pipe", "-framerate", str(a.fps), "-c:v", "mjpeg", "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p", a.out], stdin=subprocess.PIPE)
        for i in range(n):
            pg.evaluate(f"window.draw({i / a.fps})"); ff.stdin.write(pg.locator("#c").screenshot(type="jpeg", quality=93))
            if i % 48 == 0: print(f"  frame {i}/{n} ({time.time() - t0:.0f}s)", flush=True)
        ff.stdin.close(); ff.wait(); b.close(); print(f"rendered {a.out} in {time.time() - t0:.0f}s")

if __name__ == "__main__": main()
