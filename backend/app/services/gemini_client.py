"""pemanggilan Gemini lewat google-genai SDK. hanya modul ini yang menyentuh API Gemini."""

import asyncio
import json

from google import genai
from google.genai import errors, types

from app.core.config import get_settings
from app.schemas.explanation import ExplanationContent

GEMINI_TEMPERATURE = 0.2
RATE_LIMIT_STATUS = 429
# batas tambahan di atas timeout HTTP, berjaga kalau SDK tidak menghentikan request tepat waktu
TIMEOUT_MARGIN_SECONDS = 5

SYSTEM_INSTRUCTION = """kamu membantu admin UMKM Firaza memahami rekomendasi vendor procurement.
peringkat vendor sudah ditentukan oleh model machine learning. tugasmu hanya menjelaskan, bukan mengubah peringkat.

aturan:
- tulis dalam bahasa Indonesia yang profesional dan ringkas.
- pakai hanya data dari input JSON. jangan menambah fakta di luar input.
- setiap angka yang kamu tulis harus disalin persis dari input (termasuk format Rp, persen, dan hari).
  jangan menghitung angka baru seperti selisih, total, atau rata-rata.
- ringkasan: 2 sampai 3 kalimat tentang vendor peringkat 1 dan alasan utamanya.
- per_vendor: satu entri untuk setiap vendor di vendor_teratas dengan vendor_id yang sama, berisi 1 sampai 3 kelebihan
  dan 1 sampai 3 kekurangan berdasarkan metrik dan faktor_utama.
- trade_off: 1 sampai 3 kalimat tentang pilihan antara harga, ketepatan waktu, dan kualitas.
- catatan_risiko: hal yang perlu diwaspadai, misalnya sisa waktu negatif, vendor tanpa histori, atau vendor yang gugur.
- kalau punya_histori bernilai false, sebutkan bahwa metrik histori vendor itu hanya rata-rata vendor sekategori.
- kalau vendor_teratas kosong, per_vendor dikosongkan dan jelaskan alasan vendor gugur.
- jangan memakai titik koma dan jangan memakai tanda pisah panjang."""


class GeminiRateLimited(Exception):
    pass


async def generate_explanation(payload: dict, correction: str | None = None) -> ExplanationContent:
    """satu percobaan ke Gemini. error API, timeout, atau JSON yang tidak sesuai schema diteruskan ke pemanggil."""
    settings = get_settings()
    client = genai.Client(
        api_key=settings.gemini_api_key,
        # retry bawaan SDK dimatikan, aturan generate ulang sekali ditangani di explanation_service
        http_options=types.HttpOptions(
            timeout=int(settings.gemini_timeout_seconds * 1000),
            retry_options=types.HttpRetryOptions(attempts=1),
        ),
    )
    prompt = json.dumps(payload, ensure_ascii=False, indent=2)
    if correction:
        prompt += f"\n\njawaban sebelumnya ditolak karena {correction}. perbaiki dan ikuti aturan dengan ketat."

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        temperature=GEMINI_TEMPERATURE,
        response_mime_type="application/json",
        response_schema=ExplanationContent,
    )
    try:
        response = await asyncio.wait_for(
            client.aio.models.generate_content(model=settings.gemini_model, contents=prompt, config=config),
            timeout=settings.gemini_timeout_seconds + TIMEOUT_MARGIN_SECONDS,
        )
    except errors.APIError as exc:
        if exc.code == RATE_LIMIT_STATUS:
            raise GeminiRateLimited(str(exc)) from exc
        raise

    if isinstance(response.parsed, ExplanationContent):
        return response.parsed
    return ExplanationContent.model_validate_json(response.text or "")
