import sys
import os
import asyncio
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware


# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# FFmpeg configuration
# ---------------------------------------------------------------------------

from pydub import AudioSegment

try:
    import imageio_ffmpeg

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    AudioSegment.converter = ffmpeg_exe

    ffmpeg_dir = os.path.dirname(ffmpeg_exe)
    current_path = os.environ.get("PATH", "")

    if ffmpeg_dir not in current_path.split(os.pathsep):
        os.environ["PATH"] = (
            f"{ffmpeg_dir}{os.pathsep}{current_path}"
            if current_path
            else ffmpeg_dir
        )

    print(f"[FFmpeg] Configured binary: {ffmpeg_exe}")
    print(f"[FFmpeg] Directory: {ffmpeg_dir}")

except Exception as exc:
    print(f"[FFmpeg] WARNING: Could not initialize imageio-ffmpeg: {exc}")


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ALLOWED_EXTENSIONS = {".mp3", ".wav"}
MAX_FILE_SIZE = int(4.5 * 1024 * 1024)
CHUNK_MS = 30_000


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="8D Audio Converter API",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "https://8d-audio-converter-4ls6.vercel.app",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


def _to_audio_segment_from_array(audio, sample_rate):
    """Convert numpy stereo array back into pydub AudioSegment."""
    import numpy as np

    arr = np.asarray(audio, dtype=np.float32)

    if arr.ndim == 1:
        arr = np.column_stack([arr, arr])

    if arr.shape[1] == 1:
        arr = np.column_stack([arr, arr])

    peak = float(np.max(np.abs(arr))) if arr.size else 1.0
    if peak > 1.0:
        arr = arr / peak
    arr = np.clip(arr, -1.0, 1.0)

    pcm = (arr * 32767.0).astype(np.int16)
    return AudioSegment(
        data=pcm.tobytes(),
        sample_width=2,
        frame_rate=int(sample_rate),
        channels=pcm.shape[1],
    )


def apply_bass_boost(sound, boost_db: float):
    """Simple bass boost using low-pass + gain boost. Works on AudioSegment."""
    if hasattr(sound, "low_pass_filter"):
        bass = sound.low_pass_filter(250)
        return sound + boost_db + (bass * 0.6)

    # fallback when called with a numpy array
    import numpy as np

    if isinstance(sound, np.ndarray):
        audio = np.asarray(sound, dtype=np.float32)
        peak = np.max(np.abs(audio)) if audio.size else 1.0
        if peak > 1.0:
            audio = audio / peak
        boost = 10 ** (boost_db / 20)
        return (audio * boost).astype(np.float32)

    return sound


def process_audio(input_path: Path, output_path: Path, effects: dict) -> None:
    """Process audio with optional effects while keeping memory footprint low."""
    import importlib
    import settings as _settings

    original_input = _settings.inputFile
    original_output = _settings.outputFile
    _settings.inputFile = str(input_path.with_suffix(""))
    _settings.outputFile = str(output_path.with_suffix(""))

    try:
        import utils.loadSound as _loadSound
        import effects.effect8d as _effect8d
        import effects.slow as _slow
        import effects.reverb as _reverb
        import utils.saveSound as _saveSound

        importlib.reload(_loadSound)
        importlib.reload(_effect8d)
        importlib.reload(_slow)
        importlib.reload(_reverb)
        importlib.reload(_saveSound)

        from utils.loadSound import loadSound
        from effects.effect8d import effect8d
        from effects.slow import effectSlowedDown
        from effects.reverb import effectReverb
        from utils.saveSound import saveSound

        full_sound = loadSound()
        current_sample_rate = full_sound.frame_rate
        processed_chunks = []

        print(f"[PROCESS] Audio length: {len(full_sound)} ms")

        for start_ms in range(0, len(full_sound), CHUNK_MS):
            chunk = full_sound[start_ms : start_ms + CHUNK_MS]
            if len(chunk) == 0:
                continue

            working = chunk

            if effects.get("apply_8d", True):
                print("[PROCESS] Applying 8D effect to chunk...")
                working = effect8d(working)

            if effects.get("apply_slow", True):
                print("[PROCESS] Applying slow effect to chunk...")
                working = effectSlowedDown(working)

            if effects.get("apply_reverb", True):
                print("[PROCESS] Applying reverb effect to chunk...")
                working, current_sample_rate = effectReverb(working)

            if effects.get("apply_bass_boost", False):
                boost_db = float(effects.get("bass_boost_db", 5.0))
                print(f"[PROCESS] Applying bass boost ({boost_db} dB) to chunk...")
                working = apply_bass_boost(working, boost_db)

            processed_chunks.append(working)

        if not processed_chunks:
            raise RuntimeError("No audio chunks were generated.")

        final_output = processed_chunks[0]
        for chunk in processed_chunks[1:]:
            if isinstance(final_output, type(chunk)):
                final_output = final_output + chunk if hasattr(final_output, "__add__") else chunk
            else:
                final_output = _to_audio_segment_from_array(final_output, current_sample_rate) + _to_audio_segment_from_array(chunk, current_sample_rate)

        if isinstance(final_output, tuple):
            final_output = final_output[0]

        if not hasattr(final_output, "export") and not hasattr(final_output, "shape"):
            final_output = _to_audio_segment_from_array(final_output, current_sample_rate)

        print("[PROCESS] Saving audio...")
        saveSound(final_output, current_sample_rate)
        print("[PROCESS] Audio processing completed successfully!")

    finally:
        _settings.inputFile = original_input
        _settings.outputFile = original_output


@app.get("/")
async def root():
    return {
        "message": "8D Audio Converter API v2.0 is running",
        "features": ["8D effect", "Slow effect", "Reverb effect", "Bass boost"],
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/process")
async def process(
    file: UploadFile = File(...),
    apply_8d: bool = Form(True),
    apply_slow: bool = Form(True),
    apply_reverb: bool = Form(True),
    apply_bass_boost: bool = Form(False),
    bass_boost_db: float = Form(5.0),
):
    original_name = file.filename or "audio"
    ext = Path(original_name).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Tipe file '{ext}' tidak didukung. "
                "Hanya MP3 dan WAV yang diperbolehkan."
            ),
        )

    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=(
                "File terlalu besar. "
                "Maksimal ukuran file adalah 4.5 MB."
            ),
        )

    stem = Path(original_name).stem
    output_filename = f"{stem}_8d.mp3"

    effects = {
        "apply_8d": apply_8d,
        "apply_slow": apply_slow,
        "apply_reverb": apply_reverb,
        "apply_bass_boost": apply_bass_boost,
        "bass_boost_db": bass_boost_db,
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        input_path = temp_dir_path / f"input{ext}"
        output_path = temp_dir_path / f"{stem}_8d"
        input_path.write_bytes(content)

        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,
                process_audio,
                input_path,
                output_path,
                effects,
            )
        except Exception as exc:
            print(f"[PROCESS ERROR] {type(exc).__name__}: {exc}")
            raise HTTPException(
                status_code=500,
                detail=f"Pemrosesan audio gagal: {exc}",
            )

        final_mp3 = output_path.with_suffix(".mp3")
        if not final_mp3.exists():
            raise HTTPException(
                status_code=500,
                detail="Pemrosesan selesai namun file output tidak ditemukan.",
            )

        mp3_bytes = final_mp3.read_bytes()

    return Response(
        content=mp3_bytes,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": f'attachment; filename="{output_filename}"',
            "X-Filename": output_filename,
            "X-Original-Filename": original_name,
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Access-Control-Expose-Headers": "Content-Disposition, X-Filename, X-Original-Filename",
        },
    )


@app.get("/api/download/{filename}")
async def download_file(filename: str):
    return JSONResponse(
        status_code=200,
        content={
            "message": "File audio sudah di-stream langsung ke browser saat pemrosesan selesai."
        },
    )


@app.post("/api/cleanup/{filename}")
async def manual_cleanup(filename: str):
    return {"success": True, "message": f"Cleaned up {filename}"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)