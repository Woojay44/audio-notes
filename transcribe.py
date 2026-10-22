"""把录音转成带时间戳的 txt。在 WSL 里通过 transcribe.sh 运行。

用法：
    transcribe.sh <音频文件或目录> [...] [--terms "术语1,术语2"] [--model large-v3-turbo] [--out 输出目录] [--force]
路径可以写 Windows 形式（D:\\Downloads\\a.m4a），会自动转成 /mnt/d/...
"""
import argparse
import re
import sys
import time
from pathlib import Path

AUDIO_EXTS = {".m4a", ".mp3", ".wav", ".aac", ".flac", ".ogg", ".opus", ".mp4", ".mov", ".caf", ".amr"}
DEFAULT_OUT = Path(__file__).resolve().parent / "transcripts"
# 引导模型输出简体中文并带标点
PROMPT = "以下是普通话的课堂或学术会议录音，内容使用简体中文，并带有标点符号。"
PARA_GAP, PARA_LEN = 2.0, 60.0
# Whisper 在音乐/噪声处常编出的视频平台套话，整段丢弃
HALLUCINATIONS = ("请不吝点赞", "订阅 转发", "明镜与点点", "字幕由", "感谢观看")
NOISE = re.compile(r"[぀-ヿ가-힯ᄀ-ᇿ]+")


def to_wsl_path(p: str) -> Path:
    m = re.match(r"^([A-Za-z]):[\\/](.*)$", p)
    if m:
        return Path(f"/mnt/{m[1].lower()}/" + m[2].replace("\\", "/"))
    return Path(p)


def collect(inputs):
    files = []
    for raw in inputs:
        p = to_wsl_path(raw)
        if p.is_dir():
            files += sorted(f for f in p.iterdir() if f.suffix.lower() in AUDIO_EXTS)
        elif p.is_file():
            files.append(p)
        else:
            sys.exit(f"找不到：{raw}")
    return files


def fmt(t: float) -> str:
    t = int(t)
    return f"{t // 3600:02d}:{t % 3600 // 60:02d}:{t % 60:02d}"


def load_model(name):
    from faster_whisper import WhisperModel
    try:
        return WhisperModel(name, device="cuda", compute_type="float16")
    except Exception as e:  # GPU 不可用时退回 CPU
        print(f"GPU 不可用（{e}），改用 CPU", flush=True)
        return WhisperModel(name, device="cpu", compute_type="int8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--model", default="large-v3-turbo")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--force", action="store_true", help="已转写过的也重新转")
    ap.add_argument("--terms", default="", help="课程/课题术语，逗号分隔，提高术语识别率")
    args = ap.parse_args()

    out_dir = to_wsl_path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    todo = []
    for f in collect(args.inputs):
        txt = out_dir / (f.stem + ".txt")
        if txt.exists() and not args.force:
            print(f"跳过（已有）：{txt}")
        else:
            todo.append((f, txt))
    if not todo:
        return

    import opencc
    t2s = opencc.OpenCC("t2s")
    model = load_model(args.model)
    for f, txt in todo:
        print(f"转写：{f.name}", flush=True)
        start = time.time()
        prompt = PROMPT + (f"涉及术语：{args.terms}。" if args.terms else "")
        segments, info = model.transcribe(
            str(f), language="zh", initial_prompt=prompt, vad_filter=True, beam_size=5,
            condition_on_previous_text=False,  # 不拿上文当提示，避免陷入重复/幻觉循环
        )
        # 把碎片合并成段落：停顿超过 PARA_GAP 秒或段落满 PARA_LEN 秒就另起一段
        lines, para, para_start, last_end = [], [], 0.0, 0.0
        for s in segments:
            if para and (s.start - last_end > PARA_GAP or s.start - para_start > PARA_LEN):
                lines.append(f"[{fmt(para_start)}] " + " ".join(para))
                para = []
            if not para:
                para_start = s.start
            if any(h in s.text for h in HALLUCINATIONS):
                continue
            # 偶尔冒出的繁体转简体，韩文/日文假名乱码删掉
            para.append(NOISE.sub("", t2s.convert(s.text)).strip())
            last_end = s.end
            print(f"\r  {fmt(s.start)} / {fmt(info.duration)}", end="", flush=True)
        if para:
            lines.append(f"[{fmt(para_start)}] " + " ".join(para))
        tmp = txt.with_suffix(".part")
        tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
        tmp.replace(txt)
        print(f"\n  完成：{txt}（音频 {fmt(info.duration)}，用时 {fmt(time.time() - start)}）", flush=True)


if __name__ == "__main__":
    main()
