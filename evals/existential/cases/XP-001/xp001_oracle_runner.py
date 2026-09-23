from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORACLE = HERE / "xp001_layout_oracle.mjs"

def main() -> int:
    if len(sys.argv) != 2:
        print("usage: xp001_oracle_runner.py <candidate-dir>", file=sys.stderr)
        return 2

    candidate = Path(sys.argv[1]).resolve()
    target = candidate / "scripts" / "_xp001_layout_oracle.mjs"
    scope_test = candidate / "tests" / "test_production_scope_browser.py"
    if not scope_test.exists():
        print(f"missing fixture server: {scope_test}", file=sys.stderr)
        return 2

    sys.path.insert(0, str(candidate))
    old_cwd = Path.cwd()
    try:
        import os
        os.chdir(candidate)
        spec = importlib.util.spec_from_file_location("xp001_scope_fixture", scope_test)
        if spec is None or spec.loader is None:
            raise RuntimeError("cannot load fixture module")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        handler = module.ScopeFixtureHandler

        shutil.copyfile(ORACLE, target)
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            result = subprocess.run(
                ["node", "scripts/_xp001_layout_oracle.mjs", f"http://127.0.0.1:{server.server_port}"],
                cwd=candidate,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=60,
                check=False,
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
        return result.returncode
    finally:
        try:
            target.unlink(missing_ok=True)
        finally:
            import os
            os.chdir(old_cwd)

if __name__ == "__main__":
    raise SystemExit(main())
