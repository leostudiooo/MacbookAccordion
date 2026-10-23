import os
import shutil
import sys
import tempfile
import threading
import zipfile

import numpy as np


def _ensure_sounddevice_portaudio_filesystem():
    zip_paths = [p for p in sys.path if p and p.endswith(".zip") and os.path.basename(p).startswith("python")]
    if not zip_paths:
        return
    pyzip = zip_paths[0]
    try:
        with zipfile.ZipFile(pyzip, "r") as z:
            prefix = "_sounddevice_data/"
            want = [n for n in z.namelist() if n.startswith(prefix)]
            if not want:
                return
            outdir = os.path.join(tempfile.gettempdir(), "lidaccordion_sounddevice_data")
            if os.path.exists(outdir):
                shutil.rmtree(outdir, ignore_errors=True)
            os.makedirs(outdir, exist_ok=True)
            for n in want:
                if not n.endswith("/"):
                    z.extract(n, outdir)
            sys.path.insert(0, outdir)
    except Exception:
        pass


_ensure_sounddevice_portaudio_filesystem()

SAMPLE_RATE = 44100
BLOCK_SIZE = 256


def midi_to_freq(midi: int) -> float:
    return 440.0 * (2.0 ** ((midi - 69) / 12.0))


class PolyAccordionSynth:
    def __init__(self):
        self.voices = {}
        self.held = set()
        self.bellows = 0.0
        self.master = 0.45
        self.attack = 0.015
        self.release = 0.140
        self.detune = 0.008
        self.noise_amount = 0.010
        self._lock = threading.Lock()

    def set_bellows(self, bellows: float):
        with self._lock:
            self.bellows = float(max(0.0, min(1.0, bellows)))

    def note_on(self, voice_key: str, midi: int):
        with self._lock:
            self.held.add(voice_key)
            if voice_key not in self.voices:
                self.voices[voice_key] = {"freq": midi_to_freq(midi), "p1": 0.0, "p2": 0.0, "env": 0.0}
            else:
                self.voices[voice_key]["freq"] = midi_to_freq(midi)

    def note_off(self, voice_key: str):
        with self._lock:
            self.held.discard(voice_key)

    def retune(self, voice_key: str, midi: int):
        with self._lock:
            v = self.voices.get(voice_key)
            if v is not None:
                v["freq"] = midi_to_freq(midi)

    def generate_frames(self, frames: int) -> np.ndarray:
        out = np.zeros(frames, dtype=np.float32)
        with self._lock:
            held = set(self.held)
            bellows = self.bellows
            voices_snapshot = list(self.voices.items())
            master = self.master
            attack = self.attack
            release = self.release
            detune = self.detune
            noise_amount = self.noise_amount

        idx = np.arange(frames, dtype=np.float32)
        att_step = 1.0 / max(1e-6, attack * SAMPLE_RATE)
        rel_step = 1.0 / max(1e-6, release * SAMPLE_RATE)

        remove = []
        updated = {}
        for k, v in voices_snapshot:
            f = v["freq"]
            p1, p2, e = v["p1"], v["p2"], v["env"]

            if k in held:
                e_end = min(1.0, e + att_step * frames)
                env = np.linspace(e, e_end, frames, dtype=np.float32)
            else:
                e_end = max(0.0, e - rel_step * frames)
                env = np.linspace(e, e_end, frames, dtype=np.float32)

            if e_end <= 0.0 and k not in held:
                remove.append(k)
                continue

            f1, f2 = f * (1.0 - detune), f * (1.0 + detune)
            inc1, inc2 = f1 / SAMPLE_RATE, f2 / SAMPLE_RATE
            ph1 = (p1 + inc1 * idx) % 1.0
            ph2 = (p2 + inc2 * idx) % 1.0

            saw1 = 2.0 * ph1 - 1.0
            saw2 = 2.0 * ph2 - 1.0
            sig = 0.6 * saw1 + 0.4 * saw2
            sig = np.tanh(1.6 * sig)

            out += sig * env

            updated[k] = {
                "freq": f,
                "p1": float((p1 + inc1 * frames) % 1.0),
                "p2": float((p2 + inc2 * frames) % 1.0),
                "env": float(e_end),
            }

        with self._lock:
            for k, nv in updated.items():
                current = self.voices.get(k)
                if current is not None:
                    nv["freq"] = current.get("freq", nv["freq"])
                self.voices[k] = nv
            for k in remove:
                if k not in self.held:
                    self.voices.pop(k, None)
            bellows = self.bellows

        if bellows > 0.0 and noise_amount > 0.0:
            out += (np.random.randn(frames).astype(np.float32) * noise_amount) * (bellows * 0.7)

        out *= (master * bellows)
        return np.clip(out, -1.0, 1.0).astype(np.float32)
