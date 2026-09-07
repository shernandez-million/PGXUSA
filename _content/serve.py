#!/usr/bin/env python3
"""Local dev server that mimics Vercel's cleanUrls: /foo -> foo.html."""
import http.server
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080


class CleanURLHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def send_head(self):
        path = self.path.split("?", 1)[0].split("#", 1)[0]
        if path != "/" and "." not in os.path.basename(path):
            candidate = os.path.join(ROOT, path.lstrip("/") + ".html")
            if os.path.isfile(candidate):
                self.path = path + ".html"
        return super().send_head()


SEMAFORO = os.path.expanduser("~/Project-120/scripts/semaforo.sh")


def claim(owner):
    """Register this pid in the fleet's claim file.

    The environment label alone is not enough: `ps -E` is blind from inside a
    sandboxed session, so another session literally cannot read it and would see
    this server as unowned. The claim file is the readable channel. Never fatal —
    a preview server that refuses to start because a bookkeeping script moved is
    worse than one nobody has claimed.
    """
    if not owner or not os.path.isfile(SEMAFORO):
        return
    bash = shutil.which("bash")
    if not bash:
        return
    try:
        r = subprocess.run(
            [bash, SEMAFORO, "--reclamar", str(os.getpid()), owner, f"pgx serve :{PORT}"],
            capture_output=True, text=True, timeout=15)
        print((r.stdout or r.stderr).strip() or "semaforo: claimed", flush=True)
    except (OSError, subprocess.SubprocessError) as e:
        print(f"warning: could not claim this pid ({e}); it will look unowned",
              file=sys.stderr)


if __name__ == "__main__":
    # Fleet rule: a long-running process says who owns it, so no other session has
    # to guess. Unlabelled is UNKNOWN, never orphaned — nobody kills what they did
    # not start. Read it back with:
    #     ps -E -p <PID> -o command= | grep -o 'APEX_SESSION=[^ ]*'
    owner = os.environ.get("APEX_SESSION")
    if not owner:
        print("warning: no APEX_SESSION set — this server will look unowned to the "
              "rest of the fleet. Launch it as: APEX_SESSION=<session-id> "
              f"python3 {os.path.relpath(__file__, ROOT)} {PORT}", file=sys.stderr)
    with http.server.ThreadingHTTPServer(("", PORT), CleanURLHandler) as httpd:
        # after the bind, never before: a claim for a pid that dies on a port
        # collision is a row saying a dead process owns something
        claim(owner)
        # flush: piped stdout is block-buffered, and a line announcing ownership
        # is worthless if it only appears once the buffer happens to fill
        print(f"serving {ROOT} on http://localhost:{PORT} (cleanUrls on) "
              f"· pid {os.getpid()} · owner {owner or 'UNSET'}", flush=True)
        httpd.serve_forever()
