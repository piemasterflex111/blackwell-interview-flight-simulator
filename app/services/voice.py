import json
import os
import subprocess
import tempfile
from typing import Optional

class VoiceService:
    """Voice input/output using browser Speech API, faster-whisper, and optional Riva."""

    def __init__(self):
        self.riva_available = self._check_riva()
        self.whisper_available = self._check_whisper()

    def _check_riva(self) -> bool:
        try:
            import requests
            resp = requests.get("http://localhost:50050/v2/services", timeout=2)
            return resp.status_code == 200
        except Exception:
            return False

    def _check_whisper(self) -> bool:
        try:
            import faster_whisper  # noqa: F401
            return True
        except ImportError:
            return False

    async def speech_to_text(self, audio_file: str) -> str:
        """Convert audio file to text using available STT backend."""
        if self.riva_available:
            return await self._riva_stt(audio_file)
        elif self.whisper_available:
            return self._whisper_stt(audio_file)
        else:
            return self._ffmpeg_whisper_stt(audio_file)

    async def _riva_stt(self, audio_file: str) -> str:
        """STT via NVIDIA Riva."""
        import aiohttp
        async with aiohttp.ClientSession() as session:
            with open(audio_file, "rb") as f:
                audio_data = f.read()
            async with session.post(
                "http://localhost:50050/streamingrecognize",
                data=audio_data,
                headers={"Content-Type": "audio/x-wav"}
            ) as resp:
                result = await resp.json()
                return result.get("result", [{}])[0].get("alternatives", [{}])[0].get("transcript", "")

    def _whisper_stt(self, audio_file: str) -> str:
        """STT via faster-whisper."""
        from faster_whisper import WhisperModel
        model = WhisperModel("small", device="cuda", compute_type="float16")
        segments, info = model.transcribe(audio_file, beam_size=5)
        return " ".join([segment.text for segment in segments])

    def _ffmpeg_whisper_stt(self, audio_file: str) -> str:
        """Fallback: use whisper CLI if available."""
        try:
            result = subprocess.run(
                ["whisper", audio_file, "--device", "cuda", "--output-text"],
                capture_output=True, text=True, timeout=30
            )
            return result.stdout.strip()
        except Exception:
            return ""

    async def text_to_speech(self, text: str) -> Optional[str]:
        """Convert text to speech audio file path."""
        if self.riva_available:
            return await self._riva_tts(text)
        else:
            return self._local_tts(text)

    async def _riva_tts(self, text: str) -> Optional[str]:
        """TTS via NVIDIA Riva."""
        import aiohttp
        async with aiohttp.ClientSession() as session:
            payload = {"text": text, "config": {"audioCodec": "pcm"}}
            async with session.post("http://localhost:50050/synthesize", json=payload) as resp:
                audio = await resp.read()
                path = f"/tmp/tts_{os.urandom(4).hex()}.wav"
                with open(path, "wb") as f:
                    f.write(audio)
                return path

    def _local_tts(self, text: str) -> Optional[str]:
        """TTS via edge-tts or piper if available."""
        try:
            import edge_tts
            import asyncio
            path = f"/tmp/tts_{os.urandom(4).hex()}.mp3"
            asyncio.run(self._edge_tts(text, path))
            return path
        except ImportError:
            return None

    async def _edge_tts(self, text: str, path: str):
        import edge_tts
        communicator = edge_tts.Communicate(text, "en-US-GuyNeural")
        await communicator.save(path)
