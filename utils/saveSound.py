import os
import subprocess
from os import remove as removeFile
from os.path import isfile
import soundfile as sf
from pydub import AudioSegment
import settings

try:
    import imageio_ffmpeg
    FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG_EXE = "ffmpeg"


def saveSound(sound, sampleRate):
    """
    Save the sound in MP3 format.
    Supports both numpy arrays and pydub AudioSegment objects.
    Uses FFmpeg directly to avoid ffprobe requirement.
    """
    wav_path = settings.outputFile + ".wav"
    mp3_path = settings.outputFile + ".mp3"

    try:
        if hasattr(sound, "export"):
            sound.export(wav_path, format="wav")
        elif hasattr(sound, "shape"):
            arr = sound
            channels = 1 if len(arr.shape) == 1 else arr.shape[1]
            with sf.SoundFile(
                wav_path,
                "w",
                samplerate=int(sampleRate),
                channels=channels,
            ) as f:
                f.write(arr)
        else:
            raise TypeError(f"Unsupported sound type for saveSound(): {type(sound)}")

        # Convert WAV to MP3 using FFmpeg directly (no ffprobe dependency)
        command = [
            FFMPEG_EXE,
            "-y",
            "-i",
            str(wav_path),
            "-vn",
            "-acodec",
            "libmp3lame",
            "-b:a",
            "192k",
            str(mp3_path),
        ]

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if result.returncode != 0:
            # Fallback to AudioSegment export if ffmpeg command had issues
            AudioSegment.from_file(wav_path, format="wav").export(mp3_path, format="mp3")

    finally:
        if isfile(wav_path):
            try:
                removeFile(wav_path)
            except Exception:
                pass
