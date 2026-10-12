from pathlib import Path
from datetime import datetime

import mss
from PIL import Image


def capture_screen(output_dir="screenshots"):
    """Nimmt einen Screenshot des Hauptmonitors auf und speichert ihn."""
    folder = Path(output_dir)
    folder.mkdir(parents=True, exist_ok=True)

    filename = f"screen_{datetime.now():%Y%m%d_%H%M%S}.png"
    output_path = folder / filename

    with mss.mss() as screenshot:
        monitor = screenshot.monitors[1]
        image = screenshot.grab(monitor)
        Image.frombytes(
            "RGB",
            image.size,
            image.rgb
        ).save(output_path)

    return output_path.resolve()


if __name__ == "__main__":
    try:
        path = capture_screen()
        print(f"Screenshot erfolgreich gespeichert:\n{path}")
    except Exception as exc:
        print(f"Screenshot fehlgeschlagen: {type(exc).__name__}: {exc}")
        raise