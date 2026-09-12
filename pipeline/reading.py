"""
Lớp A — sinh romaji và hiragana từ câu tiếng Nhật, để không ai phải gõ tay nữa.

Chạy riêng để đọc đối chiếu trước khi tin nó:

    python3 -m pipeline.reading content/2026-08-20.json

DEC-02 chốt dùng cutlet. Nhưng cutlet trần không đủ, và đây là ba chỗ nó hụt —
đo trên chính chín câu của 2026-08-20:

1. **Không có macron.** Trong mã nguồn cutlet không có một ký tự `ō` `ū` nào;
   `ensure_ascii` chỉ lo ký tự lạ, không lo nguyên âm dài. Để nguyên là 今日 ra
   `Kyou`, tức mở lại D-5 mà BƯỚC 1 vừa đóng.
2. **Không đọc số.** `8月20日` ra `8 gatsu 20ka`. Video này ngày nào cũng đọc
   ngày tháng, nên đây không phải trường hợp hiếm.
3. **Đọc nhầm chữ nhiều nghĩa.** `一日` khi thì `tsuitachi` (mồng một) khi thì
   `ichi nichi`, tuỳ ngữ cảnh câu.

Cách vá, theo đúng thứ tự chạy:

    câu tiếng Nhật
      │  bảng đè (library/readings.json) — chữ nhiều nghĩa, đè bằng hiragana
      │  đọc số  — 8月20日 -> はちがつはつか
      ▼
    câu đã chuẩn hoá  ->  cutlet  ->  romaji thô
      │  macron    — dùng pron/kana của MeCab, không đoán mò
      │  ghép chữ  — tabe tari -> tabetari
      ▼
    romaji + hiragana

Mấu chốt của bước macron: MeCab cho hai cách đọc của mỗi từ. `pron` là cách
PHÁT ÂM, dùng `ー` cho mọi nguyên âm dài; `kana` là cách VIẾT. So hai cái là
biết chỗ nào macron mà không phải đoán:

    今日   kana=キョウ   pron=キョー   ->  ー ứng với ウ  ->  kyō
    生活   kana=セイカツ  pron=セーカツ  ->  ー ứng với イ  ->  seikatsu, không phải sēkatsu
    思う   kana=オモウ   pron=オモウ   ->  không có ー    ->  omou, giữ nguyên

Nhờ vậy `思う` không bao giờ thành `omō` — điều mà quy tắc "thấy ou thì đổi ō"
chắc chắn làm sai.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

ROOT = Path(__file__).resolve().parent.parent
READINGS_PATH = ROOT / "library" / "readings.json"


class ReadingError(RuntimeError):
    """Thiếu thư viện đọc, hoặc thư viện không khởi động được."""


def _missing(package: str, what: str = "") -> str:
    """Máy này có nhiều Python. Báo thiếu thì phải nói thiếu Ở ĐÂU, không thì
    người dùng cài đúng gói vào sai chỗ rồi vẫn hỏng y như cũ."""
    return (
        f"Thiếu {package}{' (' + what + ')' if what else ''} trong Python đang chạy:\n"
        f"    {sys.executable}\n"
        f"Chạy `make setup` để cài vào đúng chỗ này.\n"
        f"(Đừng dùng `pip install` trần — nó có thể trỏ sang một Python khác.)"
    )


@dataclass(frozen=True)
class Reading:
    romaji: str
    hira: str


#: Chữ cái đầu dòng, và chữ cái ngay sau dấu kết câu. Một dòng có thể gồm hai
#: câu — dòng mở đầu 「今日は、9月10日です。おはようございます。」 — nên chỉ viết
#: hoa chữ đầu dòng là ra `desu. ohayō`.
_SENTENCE_START = re.compile(r"(^|[.!?。！？]\s*)([^\W\d_])")


def _sentence_case(text: str) -> str:
    """Viết hoa chữ đầu mỗi câu: "desu. ohayō gozaimasu." -> "desu. Ohayō gozaimasu."."""
    return _SENTENCE_START.sub(lambda m: m.group(1) + m.group(2).upper(), text)


# ---------------------------------------------------------------------------
# Đọc số. Cutlet trả số nguyên dạng chữ số, nên phải đổi sang kana TRƯỚC khi
# đưa vào nó. Ngày và tháng tiếng Nhật đọc bất quy tắc nên phải tra bảng.
# ---------------------------------------------------------------------------

_MONTHS = {
    1: "いちがつ", 2: "にがつ", 3: "さんがつ", 4: "しがつ", 5: "ごがつ", 6: "ろくがつ",
    7: "しちがつ", 8: "はちがつ", 9: "くがつ", 10: "じゅうがつ",
    11: "じゅういちがつ", 12: "じゅうにがつ",
}

_DAYS = {
    1: "ついたち", 2: "ふつか", 3: "みっか", 4: "よっか", 5: "いつか", 6: "むいか",
    7: "なのか", 8: "ようか", 9: "ここのか", 10: "とおか",
    11: "じゅういちにち", 12: "じゅうににち", 13: "じゅうさんにち", 14: "じゅうよっか",
    15: "じゅうごにち", 16: "じゅうろくにち", 17: "じゅうしちにち", 18: "じゅうはちにち",
    19: "じゅうくにち", 20: "はつか", 21: "にじゅういちにち", 22: "にじゅうににち",
    23: "にじゅうさんにち", 24: "にじゅうよっか", 25: "にじゅうごにち",
    26: "にじゅうろくにち", 27: "にじゅうしちにち", 28: "にじゅうはちにち",
    29: "にじゅうくにち", 30: "さんじゅうにち", 31: "さんじゅういちにち",
}

_ONES = {0: "ぜろ", 1: "いち", 2: "に", 3: "さん", 4: "よん", 5: "ご",
         6: "ろく", 7: "なな", 8: "はち", 9: "きゅう"}


def _cardinal(n: int) -> str | None:
    """Số đếm trần, 0–99. Ngoài khoảng đó trả None để bên gọi còn kêu lên."""
    if n < 0 or n > 99:
        return None
    if n < 10:
        return _ONES[n]
    tens, ones = divmod(n, 10)
    head = "じゅう" if tens == 1 else _ONES[tens] + "じゅう"
    return head + (_ONES[ones] if ones else "")


def load_overrides(path: Path = READINGS_PATH) -> dict[str, str]:
    """library/readings.json — chữ nào máy đọc sai thì ghi cách đọc đúng vào đây.

    Bảng này áp cho MỌI ngày: sửa 「一日」 một lần là mọi video sau đều đúng.
    """
    if not path.exists():
        return {}
    doc = json.loads(path.read_text(encoding="utf-8"))
    return {k: v for k, v in doc.get("words", {}).items() if not k.startswith("_")}


def _number_readings(text: str) -> list[tuple[int, int, str, bool]]:
    """Tìm mọi chỗ có chữ số. Trả về (đầu, cuối, cách đọc, đọc được hay không)."""
    found = []
    for m in re.finditer(r"(\d{1,2})月", text):
        n = int(m.group(1))
        found.append((m.start(), m.end(), _MONTHS.get(n, m.group(0)), n in _MONTHS))
    for m in re.finditer(r"(\d{1,2})日", text):
        n = int(m.group(1))
        found.append((m.start(), m.end(), _DAYS.get(n, m.group(0)), n in _DAYS))
    for m in re.finditer(r"\d+", text):
        kana = _cardinal(int(m.group(0)))
        found.append((m.start(), m.end(), kana or m.group(0), kana is not None))
    return found


@dataclass(frozen=True)
class Normalized:
    """Câu đã thay chữ khó đọc bằng kana, kèm vị trí các đoạn đã thay."""

    text: str
    #: [đầu, cuối) trong `text` của từng đoạn thay. MeCab hay cắt kana thuần
    #: thành vụn (はちがつ -> はち/が/つ), nên các token nằm trong một đoạn phải
    #: được ghép lại làm một chữ.
    spans: tuple[tuple[int, int], ...]
    #: Chữ số không đọc nổi — để `make content` còn kêu lên.
    unread: tuple[str, ...]


def normalize(ja: str, overrides: dict[str, str] | None = None) -> Normalized:
    """Một lượt duy nhất: đè chữ nhiều nghĩa, rồi đọc số. Đoạn nào chồng nhau thì
    đoạn dài hơn thắng, nên 「一日」 trong bảng đè không bị 「1日」 giành mất."""
    overrides = overrides or {}
    hits: list[tuple[int, int, str, bool]] = [
        (m.start(), m.end(), value, True)
        for surface, value in overrides.items()
        for m in re.finditer(re.escape(surface), ja)
    ]
    hits += _number_readings(ja)
    # dài trước, rồi trái sang phải — để chọn được đoạn bao trùm
    hits.sort(key=lambda h: (h[0], -(h[1] - h[0])))

    out: list[str] = []
    spans: list[tuple[int, int]] = []
    unread: list[str] = []
    cursor = 0
    for lo, hi, value, ok in hits:
        if lo < cursor:      # chồng lên đoạn đã lấy
            continue
        out.append(ja[cursor:lo])
        here = sum(len(chunk) for chunk in out)
        out.append(value)
        if ok:
            spans.append((here, here + len(value)))
        else:
            unread.append(ja[lo:hi])
        cursor = hi
    out.append(ja[cursor:])

    return Normalized("".join(out), tuple(spans), tuple(unread))


# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------

class ReadingProvider(Protocol):
    """Đổi provider là đổi đúng một dòng trong `make_provider`."""

    name: str

    def read(self, ja: str) -> Reading: ...


#: Sau các từ loại này thì trợ từ dưới đây dính liền chứ không tách.
#: Cutlet chỉ ghép 助動詞; 「たり」「か」 là 助詞 nên nó tách ra thành
#: `tabe tari`, `dare ka`. Hepburn viết liền.
_GLUE_PARTICLES = {"たり", "だり", "か"}
_GLUE_AFTER = {"動詞", "形容詞", "名詞", "代名詞"}

#: Ngược lại: những 接続助詞 là từ đứng riêng, phải tách khỏi chữ trước.
_SPLIT_PARTICLES = {"けれど", "けれども", "ので", "のに", "から"}


class CutletProvider:
    """DEC-02 — bản mặc định."""

    name = "cutlet"

    def __init__(self, overrides: dict[str, str] | None = None) -> None:
        try:
            import cutlet  # noqa: PLC0415
        except ImportError as exc:
            raise ReadingError(_missing("cutlet")) from exc
        try:
            self._katsu = cutlet.Cutlet(use_foreign_spelling=False)
        except RuntimeError as exc:
            raise ReadingError(_missing("unidic-lite", "từ điển MeCab")) from exc
        # を là trợ từ thì Hepburn viết "o", không phải "wo"
        self._katsu.use_wo = False
        self.overrides = overrides or {}
        self.unread: list[str] = []

    def read(self, ja: str) -> Reading:
        """Cắt câu thành từng khúc ở ranh giới các đoạn đã chuẩn hoá.

        Đoạn kana do ta tự sinh (số, bảng đè) được romaji hoá THẲNG, không qua
        MeCab, vì hai lẽ:

        1. MeCab đọc kana thuần rất tệ: 「はつか」 (ngày 20) bị nó thấy chữ 「は」
           đứng đầu rồi coi là trợ từ, cho ra `watsuka`.
        2. MeCab không biết ranh giới đoạn nằm đâu. 「くがつとおか」 (9月10日) bị
           cắt thành くが / つと / おか — mẩu 「つと」 vắt qua hai đoạn, và bản cũ
           (khớp token vào đoạn theo vị trí) để sót nó thành `kugatsu tsuto tōka`.
           Ngày 5, 6, 8, 9, 10, 12, 30, 31 đều hỏng kiểu này; 8月20日 của video
           đầu tiên chỉ tình cờ cắt khớp.

        Nên chỉ phần chữ thường mới đưa cho MeCab, và mỗi khúc đưa riêng — không
        token nào còn vắt qua được ranh giới nữa.
        """
        norm = normalize(ja, self.overrides)
        self.unread = list(norm.unread)

        romaji: list[str] = []
        hira: list[str] = []
        cursor = 0
        end = len(norm.text)
        for lo, hi in (*norm.spans, (end, end)):
            if cursor < lo:
                words = list(self._katsu.tagger(norm.text[cursor:lo]))
                tokens = self._katsu.romaji_tokens(words)
                self._glue(words, tokens)
                self._macronize(words, tokens)
                chunk = "".join(
                    t.surface + (" " if t.space else "") for t in tokens
                ).strip()
                # Cutlet viết hoa chữ đầu mỗi lần gọi. Khúc giữa câu thì hạ
                # xuống, trừ khi đó thật là danh từ riêng.
                if romaji and words and words[0].feature.pos2 != "固有名詞":
                    chunk = chunk[:1].lower() + chunk[1:]
                romaji.append(chunk)
                hira.append(self._hira(words))
            if lo < hi:
                kana = norm.text[lo:hi]
                # Dấu cách trong bảng đè (いちご いちえ) là chỗ tách chữ romaji.
                # map_kana của cutlet sập khi gặp dấu cách, nên tách trước; còn
                # tiếng Nhật không có dấu cách nên dòng hiragana bỏ nó đi.
                romaji.append(" ".join(
                    self._collapse_all(self._katsu.map_kana(part))
                    for part in kana.split()
                ))
                hira.append(kana.replace(" ", ""))
            cursor = hi

        text = ""
        for chunk in romaji:
            if not chunk:
                continue
            # Khúc bắt đầu bằng dấu câu thì dính vào chữ trước: "hatsuka, hare".
            if text and chunk[0] not in ",.!?;:":
                text += " "
            text += chunk
        return Reading(romaji=_sentence_case(text), hira="".join(hira))

    # -- ghép chữ ----------------------------------------------------------
    @staticmethod
    def _glue(words, tokens) -> None:
        for i, word in enumerate(words[:-1]):
            nxt = words[i + 1]
            if (
                nxt.surface in _GLUE_PARTICLES
                and nxt.feature.pos1 == "助詞"
                and word.feature.pos1 in _GLUE_AFTER
            ):
                tokens[i].space = False
            # Cutlet ghép mọi 接続助詞 để 「思えば」 ra `omoeba`. Đúng với 「ば」,
            # sai với 「けれど」 — đó là một từ đứng riêng, Hepburn tách ra.
            elif nxt.surface in _SPLIT_PARTICLES:
                tokens[i].space = True

    # -- đoạn đã chuẩn hoá --------------------------------------------------
    #: Trong kana ta tự sinh, mọi nguyên âm đôi đều là nguyên âm dài thật.
    #: Trừ "ii" và "ei" — Hepburn viết nguyên hai chữ (kii, seikatsu).
    _LONG = (("ou", "ō"), ("oo", "ō"), ("uu", "ū"), ("aa", "ā"), ("ee", "ē"))

    @classmethod
    def _collapse_all(cls, roma: str) -> str:
        for pair, macron in cls._LONG:
            roma = roma.replace(pair, macron)
        return roma

    # -- macron ------------------------------------------------------------
    _MACRON = {"a": "ā", "i": "ī", "u": "ū", "e": "ē", "o": "ō"}

    @classmethod
    def _macronize(cls, words, tokens) -> None:
        for word, token in zip(words, tokens):
            pron = word.feature.pron
            kana = getattr(word.feature, "kana", None)
            if not pron or "ー" not in pron:
                continue
            # Vị trí nào trong pron là ー thì chỗ đó là nguyên âm dài; chữ tương
            # ứng trong kana cho biết viết bằng macron hay giữ hai chữ cái.
            # イ là ngoại lệ: せい viết "sei", きい viết "kii" (chuẩn Hepburn).
            keep_plain = sum(
                1 for i, ch in enumerate(pron)
                if ch == "ー" and kana and i < len(kana) and kana[i] == "イ"
            )
            longs = pron.count("ー") - keep_plain
            if longs > 0:
                token.surface = cls._collapse(token.surface, longs)

    @classmethod
    def _collapse(cls, roma: str, count: int) -> str:
        """Gộp `count` cặp nguyên âm đôi đầu tiên thành macron, từ trái sang."""
        out, i, done = [], 0, 0
        while i < len(roma):
            ch = roma[i]
            # So chữ thường: cutlet viết hoa chữ đầu câu, và 「大きく」 đứng đầu
            # câu ra "Ookiku" — so "O" với "o" thì không khớp, mất macron.
            low = ch.lower()
            # Cutlet viết nguyên âm dài hàng お thành "ou" (kyou), các hàng
            # khác thành chữ đôi (kuuki). Bắt cả hai dạng.
            twin = roma[i + 1].lower() if i + 1 < len(roma) else ""
            if done < count and low in cls._MACRON and (
                twin == low or (low == "o" and twin == "u")
            ):
                macron = cls._MACRON[low]
                out.append(macron.upper() if ch.isupper() else macron)
                i += 2
                done += 1
                continue
            out.append(ch)
            i += 1
        return "".join(out)

    # -- hiragana ----------------------------------------------------------
    @staticmethod
    def _hira(words) -> str:
        import jaconv  # noqa: PLC0415  (cutlet đã kéo sẵn jaconv về)
        out = []
        for w in words:
            kana = getattr(w.feature, "kana", None)
            out.append(jaconv.kata2hira(kana) if kana else w.surface)
        return "".join(out)


class PykakasiProvider:
    """Đường lui của DEC-02. Kém hơn hẳn — xem ghi chú ở BƯỚC 3 trong CLAUDE.md."""

    name = "pykakasi"

    def __init__(self, overrides: dict[str, str] | None = None) -> None:
        try:
            import pykakasi  # noqa: PLC0415
        except ImportError as exc:
            raise ReadingError(_missing("pykakasi")) from exc
        self._kks = pykakasi.kakasi()
        self.overrides = overrides or {}
        self.unread: list[str] = []

    def read(self, ja: str) -> Reading:
        norm = normalize(ja, self.overrides)
        self.unread = list(norm.unread)
        parts = self._kks.convert(norm.text)
        romaji = " ".join(p["hepburn"] for p in parts if p["hepburn"].strip())
        romaji = re.sub(r"\s+([,.!?、。])", r"\1", romaji)
        return Reading(
            romaji=_sentence_case(romaji),
            hira="".join(p["hira"] for p in parts),
        )


def make_provider(name: str = "cutlet", overrides: dict[str, str] | None = None):
    if overrides is None:
        overrides = load_overrides()
    if name == "cutlet":
        return CutletProvider(overrides)
    if name == "pykakasi":
        return PykakasiProvider(overrides)
    raise ReadingError(f"Không biết provider \"{name}\". Chỉ có: cutlet, pykakasi.")


# ---------------------------------------------------------------------------
# Chạy riêng để đọc đối chiếu (nghiệm thu BƯỚC 3)
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print("Ví dụ: python3 -m pipeline.reading content/2026-08-20/script.json",
              file=sys.stderr)
        return 2

    src = Path(args[0])
    if not src.exists():
        print(f"Không tìm thấy {src}", file=sys.stderr)
        return 1

    try:
        provider = make_provider(args[1] if len(args) > 1 else "cutlet")
    except ReadingError as exc:
        print(f"[lỗi] {exc}", file=sys.stderr)
        return 1
    doc = json.loads(src.read_text(encoding="utf-8"))

    # Tên file giờ là script.json ở mọi ngày, nên nhãn lấy từ `id` của kịch
    # bản (hoặc tên thư mục) — đó mới là thứ phân biệt ngày này với ngày khác.
    label = doc.get("id") or src.parent.name
    print(f"{label}  —  provider: {provider.name}\n")
    differ = 0
    for i, line in enumerate(doc["lines"], start=1):
        reading = provider.read(line["ja"])
        print(f"{i:2}. {line['ja']}")
        print(f"    {reading.romaji}")
        print(f"    {reading.hira}")
        hand = line.get("romaji")
        if hand and hand != reading.romaji:
            differ += 1
            print(f"    tay: {hand}")
        if provider.unread:
            print(f"    [!] chưa đọc được: {', '.join(provider.unread)}")
        print()

    if any("romaji" in l for l in doc["lines"]):
        print(f"Khác bản gõ tay ở {differ}/{len(doc['lines'])} câu.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
