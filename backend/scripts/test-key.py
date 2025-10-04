import json
import os
from pathlib import Path

from openai import OpenAI

AUDIO_PATH = Path(r"C:\Users\user\Downloads\No Role Modelz.mp3")
TRANSCRIPTION_MODEL = "gpt-4o-transcribe"
REASONING_MODEL = "gpt-4.1"


def _extract_text(response) -> str:
    blocks = getattr(response, "output", [])
    for block in blocks:
        content_items = getattr(block, "content", [])
        texts = []
        for item in content_items:
            text = getattr(item, "text", None)
            if text:
                texts.append(text)
        if texts:
            return "".join(texts).strip()
    output_text = getattr(response, "output_text", None)
    return output_text.strip() if isinstance(output_text, str) else ""


def _transcribe_audio(client: OpenAI) -> str:
    print("Transcribing audio with gpt-4o-transcribe...")
    with AUDIO_PATH.open("rb") as audio_stream:
        transcript = client.audio.transcriptions.create(
            model=TRANSCRIPTION_MODEL,
            file=audio_stream,
        )
    text = getattr(transcript, "text", None)
    if not text and isinstance(transcript, dict):
        text = transcript.get("text")
    text = (text or "").strip()
    if not text:
        raise RuntimeError("Empty transcription result")
    return text


def _identify_song(client: OpenAI, transcript: str) -> dict:
    prompt = (
        "You are an expert musicologist."
        " You receive lyrics or a vocal transcription from an unknown song."
        " Identify the most probable song title and primary artist."
        " Respond strictly as JSON with keys title (string), artist (string), confidence (0-1 number), notes (string)."
        f" Transcript: {transcript}"
    )
    print("Calling OpenAI gpt-4.1 for reasoning...")
    response = client.responses.create(
        model=REASONING_MODEL,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                ],
            }
        ],
    )
    raw_output = _extract_text(response)
    if not raw_output:
        raise RuntimeError("Empty reasoning response from OpenAI")
    try:
        return json.loads(raw_output)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Non-JSON response: {raw_output}") from exc


def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    if not AUDIO_PATH.exists():
        raise FileNotFoundError(f"Missing audio file: {AUDIO_PATH}")

    client = OpenAI(api_key=api_key)

    transcript = _transcribe_audio(client)
    data = _identify_song(client, transcript)

    print("Title  :", data.get("title", "?"))
    print("Artist :", data.get("artist", "?"))
    confidence = data.get("confidence")
    if isinstance(confidence, (int, float)):
        print("Confidence:", float(confidence))
    notes = data.get("notes")
    if notes:
        print("Notes  :", notes)


if __name__ == "__main__":
    main()
