import json
import queue
import threading
import time
import sounddevice as sd
import pyttsx3
from vosk import Model, KaldiRecognizer

MODEL_PATH = "models/vosk-model-small-de-0.15"
MICROPHONE = 2
SAMPLE_RATE = 16000

audio_queue = queue.Queue()

def audio_callback(indata, frames, time_info, status):
    if status:
        print("Audiohinweis:", status)
    audio_queue.put(bytes(indata))

def speak_test():
    engine = pyttsx3.init()
    engine.setProperty("rate", 175)

    for voice in engine.getProperty("voices"):
        if "HEDDA" in voice.id.upper() or "GERMAN" in voice.name.upper():
            engine.setProperty("voice", voice.id)
            break

    engine.say("Hallo! Hier ist Jarvis. Der Sprachtest beginnt jetzt.")
    engine.runAndWait()
    engine.stop()

def main():
    print("Lade deutsches Sprachmodell ...")
    model = Model(MODEL_PATH)
    recognizer = KaldiRecognizer(model, SAMPLE_RATE)

    print("\nTeste die deutsche Sprachausgabe ...")
    speak_test()

    print("\nMikrofontest startet für 15 Sekunden.")
    print("Sprich jetzt beispielsweise: Hallo Jarvis, wie geht es dir?")
    print("")

    start = time.time()

    try:
        with sd.RawInputStream(
            device=MICROPHONE,
            samplerate=SAMPLE_RATE,
            blocksize=4000,
            dtype="int16",
            channels=1,
            callback=audio_callback,
        ):
            while time.time() - start < 15:
                try:
                    data = audio_queue.get(timeout=1)

                    if recognizer.AcceptWaveform(data):
                        result = json.loads(recognizer.Result())
                        text = result.get("text", "")
                        if text:
                            print("ERKANNT:", text)
                    else:
                        result = json.loads(recognizer.PartialResult())
                        text = result.get("partial", "")
                        if text:
                            print("Erkennung:", text, end="\r", flush=True)

                except queue.Empty:
                    continue

            result = json.loads(recognizer.FinalResult())
            if result.get("text"):
                print("\nERKANNT:", result["text"])

    except Exception as exc:
        print("\nFEHLER beim Mikrofontest:")
        print(type(exc).__name__ + ":", exc)
        print("\nPrüfe, ob das HyperX-Mikrofon verfügbar ist.")

    print("\nSprachtest beendet.")

if __name__ == "__main__":
    main()
