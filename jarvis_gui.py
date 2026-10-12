import asyncio
import threading
import tempfile
import os
import time
import tkinter as tk
from tkinter import scrolledtext, messagebox
from datetime import datetime

from ai_core.config import get_settings
from ai_core.conversation.manager import ConversationManager
from ai_core.conversation.models import MessageRole
from ai_core.models.factory import LLMFactory
from ai_core.models.schemas import Message


class JarvisGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("JARVIS | Desktop Assistant")
        self.root.geometry("1050x600+80+40")
        self.root.minsize(760, 520)
        self.root.configure(bg="#10141c")

        self.manager = ConversationManager()
        self.session_id = self.manager.create_session("Neue Unterhaltung")
        self.manager.set_active_session(self.session_id)

        self.busy = False
        self.closing = False
        self.voice_enabled = True

        self.build_ui()
        self.check_status()

        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def build_ui(self):
        header = tk.Frame(self.root, bg="#171e2b", height=75)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="J.A.R.V.I.S.",
            font=("Segoe UI", 21, "bold"),
            fg="#67d9ff",
            bg="#171e2b",
        ).pack(side="left", padx=24)

        self.status = tk.Label(
            header,
            text="Verbinde mit Ollama ...",
            font=("Segoe UI", 10),
            fg="#b7c3d8",
            bg="#171e2b",
        )
        self.status.pack(side="right", padx=24)

        self.chat = scrolledtext.ScrolledText(
            self.root,
            wrap="word",
            font=("Segoe UI", 12),
            bg="#10141c",
            fg="#e6edf7",
            insertbackground="white",
            selectbackground="#294968",
            relief="flat",
            padx=22,
            pady=20,
            spacing1=4,
            spacing3=12,
            state="disabled",
        )
        self.chat.pack(fill="both", expand=True, padx=12, pady=(12, 6))

        self.chat.tag_config("user", foreground="#67d9ff",
                             font=("Segoe UI", 11, "bold"))
        self.chat.tag_config("assistant", foreground="#a6f0c6",
                             font=("Segoe UI", 11, "bold"))
        self.chat.tag_config("body", foreground="#e6edf7")
        self.chat.tag_config("system", foreground="#f0bd75")

        footer = tk.Frame(self.root, bg="#171e2b")
        footer.pack(fill="x", padx=12, pady=(6, 12), side="bottom", before=self.chat)

        self.entry = tk.Text(
            footer,
            height=3,
            wrap="word",
            font=("Segoe UI", 12),
            bg="#222b3a",
            fg="white",
            insertbackground="white",
            relief="flat",
            padx=12,
            pady=10,
        )
        self.entry.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        self.entry.bind("<Return>", self.enter_pressed)

        self.send_button = tk.Button(
            footer,
            text="Senden",
            command=self.send_message,
            font=("Segoe UI", 11, "bold"),
            bg="#087ea4",
            fg="white",
            activebackground="#109bc5",
            activeforeground="white",
            relief="flat",
            padx=20,
            pady=12,
            cursor="hand2",
        )
        self.send_button.pack(side="right", padx=(0, 10), pady=10)

        self.voice_button = tk.Button(
            footer,
            text="Stimme: AN",
            command=self.toggle_voice,
            font=("Segoe UI", 10),
            bg="#087ea4",
            fg="white",
            activebackground="#109bc5",
            activeforeground="white",
            relief="flat",
            padx=10,
            pady=10,
            cursor="hand2",
        )
        self.voice_button.pack(side="right", padx=(0, 8), pady=10)

        self.new_button = tk.Button(
            footer,
            text="Neuer Chat",
            command=self.new_chat,
            font=("Segoe UI", 10),
            bg="#303b4e",
            fg="white",
            activebackground="#41516a",
            activeforeground="white",
            relief="flat",
            padx=12,
            pady=10,
            cursor="hand2",
        )
        self.new_button.pack(side="right", padx=(0, 8), pady=10)

        self.write_message(
            "JARVIS",
            "System bereit. Ich verwende dein lokales Ollama-Modell. "
            "Wie kann ich dir helfen?",
            "assistant",
        )

    def write_message(self, sender, content, tag):
        self.chat.configure(state="normal")
        timestamp = datetime.now().strftime("%H:%M")

        self.chat.insert("end", f"{sender}  ·  {timestamp}\n", tag)
        self.chat.insert("end", content.strip() + "\n\n", "body")
        self.chat.configure(state="disabled")
        self.chat.see("end")

    def enter_pressed(self, event):
        if event.state & 0x0001:
            return None

        self.send_message()
        return "break"

    def send_message(self):
        if self.busy:
            return

        text = self.entry.get("1.0", "end").strip()
        if not text:
            return

        screen_commands = (
            "was siehst du auf meinem bildschirm",
            "was siehst du gerade",
            "bildschirm analysieren",
            "analysiere meinen bildschirm",
            "schau auf meinen bildschirm",
            "was ist auf meinem bildschirm zu sehen",
        )

        if any(command in text.casefold() for command in screen_commands):
            self.entry.delete("1.0", "end")
            self.write_message("DU", text, "user")
            self.manager.add_message(
                MessageRole.USER, text, session_id=self.session_id
            )
            self.busy = True
            self.send_button.configure(state="disabled")
            self.status.configure(text="Bildschirm wird analysiert ...", fg="#f0bd75")
            threading.Thread(
                target=self.analyze_screen_request,
                args=(text,),
                daemon=True,
            ).start()
            return

        self.entry.delete("1.0", "end")
        self.write_message("DU", text, "user")

        self.manager.add_message(
            MessageRole.USER, text, session_id=self.session_id
        )

        history = [
            Message(role=msg.role.value, content=msg.content)
            for msg in self.manager.get_messages(self.session_id)
        ]

        self.busy = True
        self.send_button.configure(state="disabled")
        self.status.configure(text="Jarvis denkt nach ...", fg="#f0bd75")

        threading.Thread(
            target=self.generate_reply,
            args=(history,),
            daemon=True,
        ).start()

    def analyze_screen_request(self, question):
        answer = None
        error_text = None

        try:
            from jarvis_screen import capture_screen
            from jarvis_vision import analyze_image

            screenshot_path = capture_screen()
            answer = analyze_image(
                screenshot_path,
                "Analysiere diesen aktuellen Desktop-Screenshot. "
                "Beschreibe erkennbare Programme, Fenster und Texte. "
                "Erfinde keine Details. Benutzerfrage: " + question
            )

            if not answer:
                answer = "Das Vision-Modell hat keine Beschreibung geliefert."

        except Exception as exc:
            error_text = f"{type(exc).__name__}: {exc}"

        if not self.closing:
            self.root.after(
                0,
                lambda: self.finish_screen_analysis(answer, error_text)
            )

    def finish_screen_analysis(self, answer, error_text):
        self.busy = False
        self.send_button.configure(state="normal")

        if error_text:
            self.write_message(
                "FEHLER",
                "Die Bildschirm-Analyse ist fehlgeschlagen:\n" + error_text,
                "system",
            )
            self.status.configure(text="Bildschirm-Analyse fehlgeschlagen", fg="#ff9b9b")
            self.entry.focus_set()
            return

        self.manager.add_message(
            MessageRole.ASSISTANT,
            answer,
            session_id=self.session_id,
        )
        self.write_message("JARVIS · BILDSCHIRM", answer, "assistant")

        if self.voice_enabled:
            threading.Thread(
                target=self.speak_reply,
                args=(answer,),
                daemon=True,
            ).start()

        self.status.configure(text="Bereit · Bildschirm analysiert", fg="#a6f0c6")
        self.entry.focus_set()
    def generate_reply(self, history):
        response_text = ""
        error_text = None
        provider = None
        streaming_started = False

        system_prompt = (
            "Du bist JARVIS, ein hilfreicher, intelligenter "
            "Desktop-Assistent. Antworte auf Deutsch, wenn der "
            "Benutzer Deutsch schreibt. Sei klar und hilfreich. "
            "Behaupte nicht, dass du den Computer steuern kannst, "
            "wenn dafür kein Werkzeug verfügbar ist."
        )

        async def run_request():
            nonlocal provider, response_text, streaming_started

            provider = LLMFactory.create()
            try:
                stream_method = getattr(provider, "generate_stream", None)

                if callable(stream_method):
                    self.root.after(
                        0, lambda: self.begin_stream_display()
                    )

                    async for chunk in stream_method(
                        messages=history,
                        system_prompt=system_prompt,
                    ):
                        if not chunk:
                            continue

                        response_text += chunk
                        streaming_started = True
                        self.root.after(
                            0,
                            lambda part=chunk: self.append_stream_text(part),
                        )

                    return response_text

                response = await provider.generate(
                    messages=history,
                    system_prompt=system_prompt,
                )
                response_text = response.text
                return response_text
            finally:
                await provider.close()

        try:
            response_text = asyncio.run(run_request())
            if not response_text.strip():
                error_text = "Ollama hat eine leere Antwort zurückgegeben."
        except Exception as exc:
            error_text = f"{type(exc).__name__}: {exc}"

        if not self.closing:
            self.root.after(
                0,
                lambda: self.finish_reply(
                    response_text, error_text, streaming_started
                ),
            )

    def begin_stream_display(self):
        if self.closing:
            return

        self.chat.configure(state="normal")
        timestamp = datetime.now().strftime("%H:%M")
        self.chat.insert("end", f"JARVIS  ·  {timestamp}\n", "assistant")
        self.chat.insert("end", "", "body")
        self.chat.configure(state="disabled")
        self.chat.see("end")

    def append_stream_text(self, chunk):
        if self.closing:
            return

        self.chat.configure(state="normal")
        self.chat.insert("end", chunk, "body")
        self.chat.configure(state="disabled")
        self.chat.see("end")

    def finish_reply(self, response_text, error_text, streaming_started=False):
        self.busy = False
        self.send_button.configure(state="normal")

        if error_text:
            if streaming_started:
                self.write_message(
                    "SYSTEM",
                    "\nDie Antwort wurde wegen eines Fehlers möglicherweise "
                    "unvollständig übertragen.\n" + error_text,
                    "system",
                )
            else:
                self.write_message(
                    "FEHLER",
                    "Ich konnte keine Antwort abrufen.\n\n"
                    + error_text
                    + "\n\nPrüfe, ob Ollama läuft und das Modell "
                      "llama3.1:8b installiert ist.",
                    "system",
                )

            self.status.configure(text="Verbindung prüfen", fg="#ff9b9b")
            return

        self.manager.add_message(
            MessageRole.ASSISTANT,
            response_text,
            session_id=self.session_id,
        )

        if not streaming_started:
            self.write_message("JARVIS", response_text, "assistant")

        if self.voice_enabled:
            threading.Thread(
                target=self.speak_reply,
                args=(response_text,),
                daemon=True,
            ).start()

        self.status.configure(text="Bereit · llama3.1:8b", fg="#a6f0c6")
        self.entry.focus_set()
    def check_status(self):
        if self.closing:
            return

        def worker():
            import urllib.request
            import json

            result = "Ollama nicht erreichbar"
            color = "#ff9b9b"

            try:
                request = urllib.request.Request(
                    "http://localhost:11434/api/tags"
                )
                with urllib.request.urlopen(request, timeout=3) as response:
                    data = json.loads(response.read().decode("utf-8"))

                models = [
                    item.get("name", "")
                    for item in data.get("models", [])
                ]

                if any(name.startswith("llama3.1:8b") for name in models):
                    result = "Ollama verbunden · llama3.1:8b"
                    color = "#a6f0c6"
                else:
                    result = "Ollama läuft · Modell prüfen"
                    color = "#f0bd75"
            except Exception:
                pass

            if not self.closing:
                self.root.after(
                    0, lambda: self.status.configure(
                        text=result, fg=color
                    )
                )

        threading.Thread(target=worker, daemon=True).start()
        self.root.after(15000, self.check_status)

    def new_chat(self):
        if self.busy:
            return

        self.session_id = self.manager.create_session("Neue Unterhaltung")
        self.manager.set_active_session(self.session_id)

        self.chat.configure(state="normal")
        self.chat.delete("1.0", "end")
        self.chat.configure(state="disabled")

        self.write_message(
            "JARVIS",
            "Neue Unterhaltung gestartet. Was möchtest du tun?",
            "assistant",
        )

    def toggle_voice(self):
        self.voice_enabled = not self.voice_enabled

        if self.voice_enabled:
            self.voice_button.configure(
                text="Stimme: AN", bg="#087ea4"
            )
        else:
            self.voice_button.configure(
                text="Stimme: AUS", bg="#6b3540"
            )
            try:
                import pygame
                if pygame.mixer.get_init():
                    pygame.mixer.music.stop()
            except Exception:
                pass

    def speak_reply(self, text):
        audio_path = None
        try:
            import edge_tts
            import pygame

            with tempfile.NamedTemporaryFile(
                suffix=".mp3", delete=False
            ) as audio_file:
                audio_path = audio_file.name

            async def create_audio():
                communicate = edge_tts.Communicate(
                    text,
                    voice="de-DE-FlorianMultilingualNeural",
                    rate="-8%",
                    pitch="-15Hz",
                )
                await communicate.save(audio_path)

            asyncio.run(create_audio())

            if self.closing or not self.voice_enabled:
                return

            if not pygame.mixer.get_init():
                pygame.mixer.init()

            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                if self.closing or not self.voice_enabled:
                    pygame.mixer.music.stop()
                    break
                time.sleep(0.1)

            pygame.mixer.music.unload()

        except Exception as exc:
            if not self.closing:
                print(f"Florian-Sprachausgabe fehlgeschlagen: {exc}")

        finally:
            if audio_path and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except OSError:
                    pass

    def close(self):
        self.closing = True

        try:
            import pygame
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
                pygame.mixer.quit()
        except Exception:
            pass

        self.root.destroy()


def main():
    root = tk.Tk()
    JarvisGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()



