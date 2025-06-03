#!/usr/bin/env python3
"""
auto_click.py – capture l’écran, demande à GPT-4o Vision « où est <cible> »,
déplace simplement le curseur au-dessus (hover) et tape du texte si fourni.

Ex. :
    python auto_click.py                             # capture auto + API KEY via $OPENAI_API_KEY
    python auto_click.py -s screenshot.png           # utiliser image existante
    python auto_click.py -k sk-...                   # clé OpenAI explicite
    python auto_click.py --no-hover -t "Zone"        # debug : pas de mouvement
    python auto_click.py --test-firefox              # mode test Firefox
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import mimetypes
import os
import re
import sys
import time
from pathlib import Path

import pyautogui
from openai import OpenAI, OpenAIError

# ─────────────────────────────────────────────────────────────────
#  Helpers : capture → base64, image size
# ────────────────────────────────────────────────────────────────

def screenshot_to_b64(save_path: Path | None = None, max_size: int = 2000) -> tuple[str, Path]:
    """Capture l’écran, évent. redimensionne, retourne base64 et path (temporaire).
    Si ``save_path`` est fourni, réutilise l’image déjà existante."""
    if save_path and save_path.exists():
        img_data = save_path.read_bytes()
        print(f"📷  Reuse existing screenshot: {save_path}")
    else:
        img = pyautogui.screenshot()
        w, h = img.size
        if max(w, h) > max_size:
            img = img.resize((int(w * max_size / max(w, h)), int(h * max_size / max(w, h))))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        img_data = buf.getvalue()
        save_path = Path("screenshot.png")
        save_path.write_bytes(img_data)
        print(f"📷  Screenshot saved as {save_path} ({img.width}×{img.height})")
    return base64.b64encode(img_data).decode(), save_path


def image_size(path: Path) -> tuple[int, int]:
    """Return (width, height) in pixels.

    Falls back to 1920×1080 when Pillow is not installed."""
    try:
        from PIL import Image  # pillow (optional but recommended)
    except ImportError:
        return 1920, 1080
    with Image.open(path) as im:
        return im.width, im.height

# ────────────────────────────────────────────────────────────────
#  Prompt builder
# ────────────────────────────────────────────────────────────────

def build_prompt(target: str, width: int, height: int) -> str:
    print(f"{width}×{height} screenshot")
    return (
        f"Output the coordinates of the '{target}' in this {width}×{height} screen. "
        "Return its pixel coordinates as: x:<int> y:<int> "
        "and add one short explanation (no quotation marks)."
    )

# ────────────────────────────────────────────────────────────────
#  GPT-4o Vision call (simple parsing regex x:nn y:nn)
# ────────────────────────────────────────────────────────────────

def ask_gpt4o(img_b64: str, prompt: str, api_key: str, model: str = "gpt-4o") -> tuple[int, int]:
    client = OpenAI(api_key=api_key)
    mime = "image/png"
    messages = [
        {
            "role": "system",
            "content": (
                "You are a vision assistant. Return coordinates ONLY in the format "
                "'x:<int> y:<int>' followed by a short explanation (no quotes)."
            ),
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{img_b64}"}},
            ],
        },
    ]
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=60,
        temperature=0,
    )
    print("\n=== 🔵 RAW OPENAI ANSWER ===")
    print(resp.choices[0].message.content.strip(), "\n")
    m = re.search(r"x\s*[:=]\s*(\d+).+?y\s*[:=]\s*(\d+)", resp.choices[0].message.content, re.I | re.S)
    if not m:
        raise ValueError("Could not parse x,y from the response.")
    return int(m.group(1)), int(m.group(2))

# ────────────────────────────────────────────────────────────────
#  Actions: hover + typing
# ────────────────────────────────────────────────────────────────

def hover_cursor(x: int, y: int) -> None:
    """Move the mouse to ``(x, y)``."""
    pyautogui.moveTo(x, y, duration=0.1)
    print(f"🐱  Hover at ({x}, {y})")


def show_marker(x: int, y: int, duration: float = 0.6) -> None:
    """Display a small red circle around ``(x, y)`` for visual feedback."""
    try:
        import tkinter as tk
    except Exception as exc:
        print(f"⚠️  No Tk GUI available: {exc}")
        return
    radius = 15
    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.geometry(f"{radius*2}x{radius*2}+{x - radius}+{y - radius}")
    canvas = tk.Canvas(root, width=radius*2, height=radius*2, highlightthickness=0)
    canvas.pack()
    canvas.create_oval(2, 2, radius*2-2, radius*2-2, outline="red", width=2)
    root.after(int(duration * 1000), root.destroy)
    root.mainloop()


def click_cursor(x: int, y: int) -> None:
    """Click once at ``(x, y)``."""
    pyautogui.click(x, y, duration=0.1)
    print(f"🐱  Click at ({x}, {y})")


def type_text(text: str) -> None:
    if not text.strip():
        print("⌨️  Empty text – nothing typed.")
        return
    time.sleep(0.1)
    for ch in text:
        if ch == "\n":
            pyautogui.press("enter")
        else:
            pyautogui.write(ch, interval=0.04)
    print(f"⌨️  Text typed: {repr(text)}")

# ────────────────────────────────────────────────────────────────
#  Main CLI
# ────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="GPT-4o Vision hover+type automation.")
    parser.add_argument("-t", "--target", help="UI element to locate (e.g. 'Download button').")
    parser.add_argument("-m", "--model", default="gpt-4o", help="Vision model (default: gpt-4o)")
    parser.add_argument("-k", "--api-key", default=os.getenv("OPENAI_API_KEY"), help="OpenAI key ($OPENAI_API_KEY)")
    parser.add_argument("-s", "--screenshot", type=Path, help="Use existing screenshot file instead of capturing")
    parser.add_argument("--text", default="", help="Text to type afterwards (\\n supported)")
    parser.add_argument("--no-hover", action="store_true", help="Do not move the mouse (debug only)")
    parser.add_argument("--test-firefox", action="store_true", help="Test: cherche l'ic\u00f4ne Firefox et double-clique avec un marqueur 10 s")
    args = parser.parse_args()

    if not args.api_key:
        parser.error("OpenAI key missing (use -k or set $OPENAI_API_KEY)")

    if args.test_firefox:
        args.target = "ic\u00f4ne Firefox"
        args.text = ""
        args.no_hover = False
    elif not args.target:
        parser.error("--target is required unless --test-firefox is used")

    # 1) capture / encode
    img_b64, img_path = screenshot_to_b64(args.screenshot)
    w, h = image_size(img_path)
    prompt = build_prompt(args.target, w, h)

    # 2) ask GPT-4o Vision
    try:
        x, y = ask_gpt4o(img_b64, prompt, api_key=args.api_key, model=args.model)
    except (OpenAIError, ValueError) as exc:
        print(f"❌ API/Parsing error: {exc}")
        sys.exit(1)

    print(f"✅ Coordinates: ({x}, {y})")

    # 3) actions
    if args.test_firefox:
        hover_cursor(x, y)
        pyautogui.doubleClick(x, y, duration=0.1)
        show_marker(x, y, duration=10.0)
    else:
        if not args.no_hover:
            hover_cursor(x, y)
        else:
            click_cursor(x, y)
        type_text(args.text)


if __name__ == "__main__":
    main()
