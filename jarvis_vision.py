import base64
import json
import urllib.request
from pathlib import Path

from jarvis_screen import capture_screen

OLLAMA_URL = "http://localhost:11434/api/generate"
VISION_MODEL = "llava:7b"


def analyze_image(image_path, question="Beschreibe meinen Bildschirm."):
    image_path = Path(image_path).resolve()

    with image_path.open("rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode("ascii")

    prompt = (
        "Du bist JARVIS, ein präziser Computer-Assistent. "
        "Das Bild ist ein echter Screenshot eines Computerbildschirms. "
        "Untersuche das Bild sorgfältig. "
        "Nenne erkennbare Fenster, Programme, sichtbare Texte, "
        "Schaltflächen und Fehlermeldungen. "
        "Wenn du etwas nicht lesen kannst, sage das ausdrücklich. "
        "Erfinde keine Inhalte. "
        "Antworte auf Deutsch in kurzen, konkreten Stichpunkten.\n\n"
        "Aufgabe: " + question
    )

    payload = {
        "model": VISION_MODEL,
        "prompt": prompt,
        "images": [encoded_image],
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 250
        }
    }

    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=240) as response:
        result = json.loads(response.read().decode("utf-8"))

    return result.get("response", "").strip()


if __name__ == "__main__":
    try:
        print("Nehme einen aktuellen Screenshot auf ...")
        screenshot_path = capture_screen()
        print(f"Bild gespeichert: {screenshot_path}")
        print("\nJARVIS analysiert den Bildschirm ...\n")

        answer = analyze_image(
            screenshot_path,
            "Welche Programme und Fenster sind sichtbar? "
            "Was steht im Vordergrund? Beschreibe konkrete Details."
        )

        print("========== JARVIS ==========")
        print(answer or "Das Modell hat keine Antwort geliefert.")
        print("============================")

    except Exception as exc:
        print(f"Fehler: {type(exc).__name__}: {exc}")