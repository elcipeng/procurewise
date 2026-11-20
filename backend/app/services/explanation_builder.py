"""bahan penjelasan rekomendasi: payload untuk Gemini, validasi angka, dan penjelasan template.

semua fungsi di sini murni (tanpa DB dan tanpa jaringan) supaya mudah diuji dan dijelaskan.
angka dikirim ke Gemini dalam bentuk teks yang sudah diformat (Rp, persen, hari), jadi Gemini cukup menyalin
dan tidak perlu menghitung. output yang memuat angka di luar payload dianggap mengarang.
"""

import json
import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import date

from app.schemas.explanation import ExplanationContent, VendorExplanation
from app.schemas.recommendation import RankedVendor, RecommendationResult

TOP_VENDORS = 3
# angka kecil wajar muncul di kalimat (peringkat 1, 2 vendor), jadi selalu diizinkan
ALWAYS_ALLOWED_MAX = 10
MAX_REJECTED_IN_RISK = 3
NUMBER_PATTERN = re.compile(r"\d+(?:[.,]\d+)*")

PRIORITY_LABELS = {"high": "tinggi", "normal": "normal", "low": "rendah"}
MONTHS = (
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
)


# format angka bahasa indonesia, sama dengan tampilan di frontend


def _decimal(value: float, digits: int) -> str:
    text = f"{value:.{digits}f}".rstrip("0").rstrip(".")
    return text.replace(".", ",")


def rupiah(value: float) -> str:
    # spasi tak terputus seperti format Intl di frontend, supaya "Rp" tidak terpisah dari angkanya di akhir baris
    return "Rp " + f"{round(value):,}".replace(",", ".")


def percent(rate: float) -> str:
    return f"{_decimal(rate * 100, 1)}%"


def days(value: float) -> str:
    return f"{_decimal(value, 1)} hari"


def slack(value: float) -> str:
    return f"+{days(value)}" if value > 0 else days(value)


def rating(value: float) -> str:
    return f"{_decimal(value, 2)} dari 5"


def long_date(value: date) -> str:
    return f"{value.day} {MONTHS[value.month - 1]} {value.year}"


def join_words(items: list[str]) -> str:
    if len(items) <= 2:
        return " dan ".join(items)
    return f"{', '.join(items[:-1])}, dan {items[-1]}"


def _lower_first(text: str) -> str:
    return text[:1].lower() + text[1:]


def _vendor_payload(vendor: RankedVendor) -> dict:
    return {
        "peringkat": vendor.rank,
        "vendor_id": vendor.vendor_id,
        "nama_vendor": vendor.vendor_name,
        "kota": vendor.vendor_city,
        "harga_satuan": rupiah(vendor.offer.unit_price),
        "total_biaya": rupiah(vendor.total_cost),
        "janji_lead_time": days(vendor.offer.quoted_lead_time_days),
        "sisa_waktu_setelah_lead_time": slack(vendor.slack_days),
        "tepat_waktu": percent(vendor.history.on_time_rate),
        "tingkat_cacat": percent(vendor.history.defect_rate),
        "rating_kualitas": rating(vendor.history.avg_rating),
        "jumlah_transaksi_selesai": vendor.history.n_transactions,
        # tanpa histori, metrik tepat waktu, cacat, dan rating hanya rata-rata vendor sekategori
        "punya_histori": vendor.history.has_history,
        "faktor_utama": [
            {"faktor": f.label, "arah": "menaikkan peringkat" if f.contribution >= 0 else "menurunkan peringkat"}
            for f in vendor.top_factors
        ],
    }


def build_payload(result: RecommendationResult) -> dict:
    """input JSON untuk Gemini: kebutuhan, vendor teratas dengan metrik dan faktor, serta vendor yang gugur."""
    request = result.request
    return {
        "kebutuhan": {
            "material": f"{request.material_code} - {request.material_name}",
            "jumlah": f"{request.qty} {request.material_unit}",
            "tanggal_kebutuhan_dibuat": long_date(request.request_date),
            "dibutuhkan_paling_lambat": long_date(request.needed_by),
            "prioritas": PRIORITY_LABELS[request.priority],
            "budget_maksimal": "tidak dibatasi" if request.max_budget is None else rupiah(float(request.max_budget)),
        },
        "metode_peringkat": (
            "metode cadangan weighted sum" if result.is_fallback else f"model LightGBM LambdaRank ({result.model_version})"
        ),
        "jumlah_vendor_memenuhi_syarat": len(result.ranked),
        "vendor_teratas": [_vendor_payload(v) for v in result.ranked[:TOP_VENDORS]],
        "vendor_tidak_memenuhi_syarat": [
            {"nama_vendor": v.vendor_name, "alasan": [r.message for r in v.reasons]} for v in result.rejected
        ],
    }


def parse_numbers(text: str) -> list[float]:
    # format indonesia: titik pemisah ribuan, koma pemisah desimal
    return [float(token.replace(".", "").replace(",", ".")) for token in NUMBER_PATTERN.findall(text)]


def allowed_numbers(payload: dict) -> set[float]:
    numbers = parse_numbers(json.dumps(payload, ensure_ascii=False))
    return {round(n, 4) for n in numbers} | {float(n) for n in range(ALWAYS_ALLOWED_MAX + 1)}


def _texts(content: ExplanationContent) -> Iterable[str]:
    yield content.ringkasan
    yield content.trade_off
    yield from content.catatan_risiko
    for vendor in content.per_vendor:
        yield vendor.nama_vendor
        yield from vendor.kelebihan
        yield from vendor.kekurangan


def find_problems(content: ExplanationContent, allowed: set[float], expected_vendor_ids: set[int]) -> list[str]:
    """masalah di output Gemini: angka yang tidak ada di input, atau daftar vendor yang tidak sesuai."""
    problems = []
    unknown = sorted({n for text in _texts(content) for n in parse_numbers(text) if round(n, 4) not in allowed})
    if unknown:
        problems.append("angka berikut tidak ada di data input: " + ", ".join(_decimal(n, 4) for n in unknown))
    returned_ids = {v.vendor_id for v in content.per_vendor}
    if returned_ids != expected_vendor_ids:
        problems.append(f"per_vendor harus berisi tepat vendor_id {sorted(expected_vendor_ids)}")
    return problems


def sanitize(content: ExplanationContent) -> ExplanationContent:
    """aturan tulisan proyek melarang titik koma dan tanda pisah panjang di teks UI."""

    def clean(text: str) -> str:
        return text.replace(";", ",").replace("—", "-").replace("–", "-").strip()

    return ExplanationContent(
        ringkasan=clean(content.ringkasan),
        per_vendor=[
            VendorExplanation(
                vendor_id=v.vendor_id,
                nama_vendor=clean(v.nama_vendor),
                kelebihan=[clean(t) for t in v.kelebihan],
                kekurangan=[clean(t) for t in v.kekurangan],
            )
            for v in content.per_vendor
        ],
        trade_off=clean(content.trade_off),
        catatan_risiko=[clean(t) for t in content.catatan_risiko],
    )


# penjelasan template, dipakai kalau Gemini tidak tersedia atau outputnya tidak lolos validasi


@dataclass(frozen=True)
class _Metric:
    value: Callable[[RankedVendor], float]
    fmt: Callable[[float], str]
    lower_is_better: bool
    best_phrase: str
    worst_phrase: str
    from_history: bool = False


METRICS = (
    _Metric(lambda v: v.offer.unit_price, rupiah, True, "Harga satuan paling murah", "Harga satuan paling mahal"),
    _Metric(lambda v: v.total_cost, rupiah, True, "Total biaya paling rendah", "Total biaya paling tinggi"),
    _Metric(
        lambda v: v.offer.quoted_lead_time_days, days, True, "Janji lead time paling cepat", "Janji lead time paling lama"
    ),
    _Metric(lambda v: v.slack_days, slack, False, "Sisa waktu paling longgar", "Sisa waktu paling sempit"),
    _Metric(
        lambda v: v.history.on_time_rate, percent, False,
        "Tingkat tepat waktu paling tinggi", "Tingkat tepat waktu paling rendah", from_history=True,
    ),
    _Metric(
        lambda v: v.history.defect_rate, percent, True,
        "Tingkat cacat paling rendah", "Tingkat cacat paling tinggi", from_history=True,
    ),
    _Metric(
        lambda v: v.history.avg_rating, rating, False,
        "Rating kualitas paling tinggi", "Rating kualitas paling rendah", from_history=True,
    ),
)


def _compared(vendors: list[RankedVendor], metric: _Metric) -> list[RankedVendor]:
    # vendor tanpa histori hanya punya rata-rata kategori, jadi tidak ikut dibandingkan untuk metrik histori
    return [v for v in vendors if v.history.has_history] if metric.from_history else vendors


def _vendor_explanation(vendor: RankedVendor, top: list[RankedVendor]) -> VendorExplanation:
    strengths, weaknesses = [], []
    for metric in METRICS:
        compared = _compared(top, metric)
        values = [metric.value(v) for v in compared]
        if len(compared) < 2 or min(values) == max(values) or vendor not in compared:
            continue
        best, worst = (min(values), max(values)) if metric.lower_is_better else (max(values), min(values))
        value = metric.value(vendor)
        if value == best:
            strengths.append(f"{metric.best_phrase} di antara vendor teratas ({metric.fmt(value)})")
        elif value == worst:
            weaknesses.append(f"{metric.worst_phrase} di antara vendor teratas ({metric.fmt(value)})")

    raising = [_lower_first(f.label) for f in vendor.top_factors if f.contribution >= 0]
    lowering = [_lower_first(f.label) for f in vendor.top_factors if f.contribution < 0]
    if raising:
        strengths.append(f"Faktor model yang menaikkan peringkat: {join_words(raising)}")
    if lowering:
        weaknesses.append(f"Faktor model yang menurunkan peringkat: {join_words(lowering)}")
    if vendor.slack_days < 0:
        weaknesses.append(f"Janji lead time melewati tanggal dibutuhkan ({slack(vendor.slack_days)})")
    if not vendor.history.has_history:
        weaknesses.append("Belum punya transaksi selesai, metrik histori memakai rata-rata vendor sekategori")

    return VendorExplanation(
        vendor_id=vendor.vendor_id,
        nama_vendor=vendor.vendor_name,
        kelebihan=strengths or ["Tidak ada keunggulan yang menonjol dibanding vendor teratas lain"],
        kekurangan=weaknesses or ["Tidak ada kelemahan yang menonjol dibanding vendor teratas lain"],
    )


def _trade_off(ranked: list[RankedVendor]) -> str:
    first = ranked[0]
    if len(ranked) == 1:
        return "Hanya satu vendor yang memenuhi syarat, jadi belum ada pilihan lain untuk dibandingkan."
    parts = []
    cheapest = min(ranked, key=lambda v: v.total_cost)
    if cheapest.vendor_id == first.vendor_id:
        parts.append("Vendor peringkat 1 sekaligus pilihan dengan total biaya paling rendah.")
    else:
        parts.append(
            f"{cheapest.vendor_name} lebih murah ({rupiah(cheapest.total_cost)}) dibanding peringkat 1 "
            f"({rupiah(first.total_cost)}), tetapi berada di peringkat {cheapest.rank}."
        )
    with_history = [v for v in ranked if v.history.has_history]
    if with_history:
        reliable = max(with_history, key=lambda v: v.history.on_time_rate)
        if reliable.vendor_id != first.vendor_id:
            parts.append(
                f"{reliable.vendor_name} paling sering tepat waktu ({percent(reliable.history.on_time_rate)}), "
                f"dibanding peringkat 1 ({percent(first.history.on_time_rate)})."
            )
    return " ".join(parts)


def _risks(result: RecommendationResult, top: list[RankedVendor]) -> list[str]:
    risks = []
    if result.is_fallback:
        risks.append("Peringkat disusun dengan metode cadangan weighted sum karena model LightGBM tidak dapat dimuat.")
    late = [v.vendor_name for v in top if v.slack_days < 0]
    if late:
        risks.append(f"Janji lead time {join_words(late)} melewati tanggal dibutuhkan.")
    limited = [v.vendor_name for v in top if not v.history.has_history]
    if limited:
        risks.append(f"{join_words(limited)} belum punya histori transaksi, kinerjanya belum terbukti.")
    for vendor in result.rejected[:MAX_REJECTED_IN_RISK]:
        risks.append(f"{vendor.vendor_name} tidak memenuhi syarat: {_lower_first(vendor.reasons[0].message)}.")
    hidden = len(result.rejected) - MAX_REJECTED_IN_RISK
    if hidden > 0:
        risks.append(f"Ada {hidden} vendor lain yang juga tidak memenuhi syarat.")
    return risks or ["Tidak ada risiko yang menonjol dari data yang tersedia."]


def build_template(result: RecommendationResult) -> ExplanationContent:
    """penjelasan berbasis aturan dari data peringkat, tanpa angka selain yang ada di hasil rekomendasi."""
    request = result.request
    need = f"{request.qty} {request.material_unit} {request.material_name}"
    top = result.ranked[:TOP_VENDORS]
    if not top:
        return ExplanationContent(
            ringkasan=(
                f"Belum ada vendor yang memenuhi syarat untuk {need}. Semua {len(result.rejected)} vendor yang "
                "menawarkan material ini gugur di pengecekan awal."
            ),
            per_vendor=[],
            trade_off="Tidak ada vendor yang bisa dibandingkan untuk kebutuhan ini.",
            catatan_risiko=_risks(result, top),
        )

    first = top[0]
    return ExplanationContent(
        ringkasan=(
            f"{first.vendor_name} berada di peringkat 1 dari {len(result.ranked)} vendor yang memenuhi syarat untuk "
            f"{need}. Total biayanya {rupiah(first.total_cost)} dengan janji lead time "
            f"{days(first.offer.quoted_lead_time_days)} dan sisa waktu {slack(first.slack_days)} sebelum tanggal dibutuhkan."
        ),
        per_vendor=[_vendor_explanation(v, top) for v in top],
        trade_off=_trade_off(result.ranked),
        catatan_risiko=_risks(result, top),
    )
