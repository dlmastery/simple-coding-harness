"""Step 02 demo: the same prompt as a nested tree and as a flat element map.

Runs both shapes in the headless page, replays the recorded deltas through
progress.py, and prints when each shape first painted a component and when
its layout was known. Saves demo.png (the finished flat layout) and
demo_streaming.png (both shapes replayed to the same point of their stream).
Needs an API key.
"""

import socket
import threading
import time
from pathlib import Path

import uvicorn
from playwright.sync_api import sync_playwright

import progress
import server

HERE = Path(__file__).parent
PROMPT = "show me a dashboard for a lemonade stand"


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def serve(port):
    """Run uvicorn on a daemon thread and return once it accepts connections."""
    config = uvicorn.Config(server.app, host="127.0.0.1", port=port, log_level="warning")
    instance = uvicorn.Server(config)
    threading.Thread(target=instance.run, daemon=True).start()
    while not instance.started:
        time.sleep(0.05)
    return instance


def run_shape(page, shape):
    """One run in the page. Returns the deltas, their arrival times and the done message."""
    page.select_option("#mode", shape)
    page.fill("#prompt", PROMPT)
    page.click("#run")
    page.wait_for_selector("body[data-state=done]", timeout=180_000)
    events = page.evaluate("window.__events")
    timeline = page.evaluate("window.__timeline")
    deltas = [e["delta"] for e in events if "delta" in e]
    return deltas, timeline, events[-1]


def at(timeline, chunk):
    return "-" if chunk is None else f"chunk {chunk:>3} / {timeline[chunk - 1] / 1000:.2f}s"


def main():
    port = free_port()
    serve(port)
    results = {}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1000, "height": 720})
        page.goto(f"http://127.0.0.1:{port}/")
        for shape in ("tree", "flat"):
            deltas, timeline, done = run_shape(page, shape)
            results[shape] = (deltas, timeline, done, progress.replay(deltas, shape))
        page.screenshot(path=str(HERE / "demo.png"), full_page=True)

        # Photograph both shapes at the same point: a third of the way through the stream.
        moment = max(results["flat"][3]["skeleton_chunk"] or 1, results["flat"][3]["chunks"] // 3)
        page.set_viewport_size({"width": 560, "height": 720})
        page.evaluate("([text, mode]) => window.__replay(text, mode)", ["".join(results["tree"][0][:moment]), "tree"])
        page.wait_for_timeout(100)
        tree_shot = page.locator("#dashboard").screenshot()
        page.evaluate("([text, mode]) => window.__replay(text, mode)", ["".join(results["flat"][0][:moment]), "flat"])
        page.wait_for_timeout(100)
        flat_shot = page.locator("#dashboard").screenshot()
        browser.close()

    side_by_side(tree_shot, flat_shot, HERE / "demo_streaming.png", moment)

    print(f"prompt: {PROMPT}")
    print(f"{'shape':<6} {'chunks':>6} {'chars':>6} {'first paint':>22} {'layout known':>22} {'done':>7}  valid  tokens")
    for shape, (deltas, timeline, done, replay) in results.items():
        usage = done.get("usage") or {}
        print(
            f"{shape:<6} {replay['chunks']:>6} {replay['chars']:>6} {at(timeline, replay['first_paint_chunk']):>22} "
            f"{at(timeline, replay['skeleton_chunk']):>22} {timeline[-1] / 1000:>6.2f}s  {'yes' if done['valid'] else 'no':<5}  "
            f"{usage.get('completion_tokens')}"
        )
        for error in done["errors"][:3]:
            print(f"       {error}")
    print(f"demo_streaming.png: both shapes replayed to chunk {moment} (tree left, flat right)")
    print("saved demo.png, demo_streaming.png")


def side_by_side(left, right, path, moment):
    """Two PNGs next to each other, with a caption; a plain pair of files if PIL is missing."""
    import io

    try:
        from PIL import Image, ImageDraw
    except ImportError:
        path.with_name("demo_streaming_tree.png").write_bytes(left)
        path.with_name("demo_streaming_flat.png").write_bytes(right)
        return
    a, b = Image.open(io.BytesIO(left)), Image.open(io.BytesIO(right))
    height = max(a.height, b.height) + 28
    out = Image.new("RGB", (a.width + b.width + 24, height), "#f5f7fa")
    draw = ImageDraw.Draw(out)
    draw.text((8, 6), f"nested tree at chunk {moment}", fill="#1f2933")
    draw.text((a.width + 32, 6), f"flat element map at chunk {moment}", fill="#1f2933")
    out.paste(a, (8, 28))
    out.paste(b, (a.width + 16, 28))
    out.save(path)


if __name__ == "__main__":
    main()
