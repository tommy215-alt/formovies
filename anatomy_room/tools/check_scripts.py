#!/usr/bin/env python3
"""台本（scripts/pilot_*/script.md）の機械的なチェック。

- 台本表が 6 列であること
- 時間が連続していること（前の行の終了 = 次の行の開始）
- 各セリフの必要話速（文字/秒）が上限を超えないこと
- 台本の事実確認 ID が fact_check.md に存在すること（逆に、未使用の ID も報告）
- 全体の尺が 60〜90 秒に収まること

使い方: python3 anatomy_room/tools/check_scripts.py [pilot_001 ...]
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"

COLUMNS = ["時間", "キャラクター・音声", "セリフ", "映像・CGの指示", "画面字幕", "事実確認ID"]
CHARS_PER_SEC = 5.4      # 目安（VOICEVOX 1.1〜1.15 倍速の実測から）。尺の判定は tools/measure_tts.py の実測を正とする
MAX_CHARS_PER_SEC = 7.0  # これを超えると枠に収まらない可能性が高い
MIN_SEC, MAX_SEC = 60, 90


def parse_time(s):
    m, sec = s.split(":")
    return int(m) * 60 + int(sec)


def spoken_chars(line):
    """読み上げる文字数の概算（句読点・記号・空白を除く）。"""
    return len(re.sub(r"[\s、。，．,.!?！？…「」『』（）()・ー〜~%％]", "", line))


def table_rows(text):
    head = text.split("## 3. 完全な台本", 1)
    if len(head) < 2:
        return None, ["「## 3. 完全な台本」が見つからない"]
    rows, errors = [], []
    for raw in head[1].splitlines():
        if not raw.startswith("|"):
            continue
        cells = [c.strip() for c in raw.strip().strip("|").split("|")]
        if set("".join(cells)) <= set("-: "):
            continue
        rows.append(cells)
    if not rows:
        return None, ["台本表が空"]
    if rows[0] != COLUMNS:
        errors.append(f"列見出しが違う: {rows[0]}")
    return rows[1:], errors


def check(pilot_dir):
    errors, warnings = [], []
    script = (pilot_dir / "script.md").read_text(encoding="utf-8")
    facts_path = pilot_dir / "fact_check.md"
    facts = facts_path.read_text(encoding="utf-8") if facts_path.exists() else ""
    defined = set(re.findall(r"^### (FACT-\d+)", facts, flags=re.M))

    rows, errs = table_rows(script)
    errors += errs
    if rows is None:
        return errors, warnings, {}

    used, prev_end, total_chars = set(), 0, {"M": 0, "W": 0}
    for i, cells in enumerate(rows, 1):
        if len(cells) != 6:
            errors.append(f"行 {i}: 列数が {len(cells)}（6 列であるべき）")
            continue
        time, who, line, _video, _sub, ids = cells
        m = re.fullmatch(r"(\d+:\d\d)-(\d+:\d\d)", time)
        if not m:
            errors.append(f"行 {i}: 時間の形式が不正 '{time}'")
            continue
        start, end = parse_time(m.group(1)), parse_time(m.group(2))
        if start != prev_end:
            errors.append(f"行 {i} ({time}): 前の行の終了 {prev_end}s と開始がずれている")
        if end <= start:
            errors.append(f"行 {i} ({time}): 終了が開始より前")
        prev_end = end
        if who in ("M", "W"):
            n = spoken_chars(line)
            total_chars[who] += n
            rate = n / max(end - start, 1)
            if rate > MAX_CHARS_PER_SEC:
                warnings.append(f"行 {i} ({time} {who}): {n} 文字 / {end - start} 秒 = {rate:.1f} 文字/秒（早口）")
        for fid in re.findall(r"FACT-\d+", ids):
            used.add(fid)
            if fid not in defined:
                errors.append(f"行 {i} ({time}): {fid} が fact_check.md に定義されていない")
        if not re.fullmatch(r"(—|JOKE|FACT-\d+(, FACT-\d+)*)", ids):
            errors.append(f"行 {i} ({time}): 事実確認ID の書式が不正 '{ids}'")

    for fid in sorted(defined - used):
        warnings.append(f"{fid} は fact_check.md にあるが台本で参照されていない")
    if not MIN_SEC <= prev_end <= MAX_SEC:
        warnings.append(f"尺 {prev_end} 秒が {MIN_SEC}〜{MAX_SEC} 秒の範囲外")

    stats = {
        "尺(秒)": prev_end,
        "Mの文字数": total_chars["M"],
        "Wの文字数": total_chars["W"],
        "セリフの推定所要(秒)": round(sum(total_chars.values()) / CHARS_PER_SEC, 1),
        "行数": len(rows),
        "事実ID": len(defined),
    }
    return errors, warnings, stats


def main(argv):
    targets = argv or sorted(p.name for p in SCRIPTS.glob("pilot_*") if (p / "script.md").exists())
    failed = False
    for name in targets:
        errors, warnings, stats = check(SCRIPTS / name)
        status = "NG" if errors else "OK"
        failed |= bool(errors)
        print(f"== {name}: {status}  " + "  ".join(f"{k}={v}" for k, v in stats.items()))
        for e in errors:
            print(f"  [ERROR] {e}")
        for w in warnings:
            print(f"  [WARN]  {w}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
