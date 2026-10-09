# -*- coding: utf-8 -*-
"""验收脚本(GN 版): test指标 + 负样本误检率 + 小目标分层 + 报告
用法: python evaluate_acceptance.py [--weights runs/durant_full/weights/best.pt]
产出: runs/acceptance_report.md + runs/acceptance_summary.json
"""
import argparse
import json
from pathlib import Path

ROOT = Path(r"E:\杜兰特人物标注")
DS = ROOT / "durant_dataset_yolo"
CONF = 0.25          # 负样本误检判定阈值
THR = {"map50": 0.60, "map5095": 0.40, "neg_fpr": 0.02}


def imread(p):
    import numpy as np
    return __import__("cv2").imdecode(np.fromfile(str(p), dtype=np.uint8), 1)


def main():
    import cv2
    import numpy as np
    from ultralytics import YOLO
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", default=str(ROOT / "runs/durant_full/weights/best.pt"))
    args = ap.parse_args()
    model = YOLO(args.weights)

    report = {"weights": args.weights, "thresholds": THR}

    # ---- 1) test 集正式评测 ----
    m = model.val(data=str(DS / "data.yaml"), split="test", imgsz=896, device=0,
                  plots=True, verbose=False)
    map50 = float(m.box.map50)
    map5095 = float(m.box.map)
    report["test_map50"] = round(map50, 4)
    report["test_map5095"] = round(map5095, 4)
    print(f"[test] mAP50={map50:.4f} mAP50-95={map5095:.4f}", flush=True)

    # ---- 2) 小目标分层(按真值框高度) ----
    tiers = {"far(<150px)": [], "mid(150-400px)": [], "near(>400px)": []}
    lbl_dir = DS / "labels" / "test"
    for lf in lbl_dir.glob("*.txt"):
        for line in lf.read_text(encoding="utf-8").splitlines():
            parts = line.split()
            if len(parts) < 6:
                continue
            ys = [float(v) for v in parts[2::2]]
            h = (max(ys) - min(ys)) * 1080
            if h < 150:
                tiers["far(<150px)"].append(lf.stem)
            elif h <= 400:
                tiers["mid(150-400px)"].append(lf.stem)
            else:
                tiers["near(>400px)"].append(lf.stem)
    tier_map = {}
    for tname, stems in tiers.items():
        stems = sorted(set(stems))
        if not stems:
            tier_map[tname] = {"images": 0, "note": "no gt"}
            continue
        paths = [str(DS / "images/test" / (s2 + ".jpg")) for s2 in stems]
        ok = 0
        B = 12
        for bi in range(0, len(paths), B):
            rs = model.predict(source=paths[bi:bi + B], conf=CONF, imgsz=896,
                               device=0, verbose=False)
            for p, r in zip(stems[bi:bi + B], rs):
                gt = json.loads("{}")
                # 该帧真值框
                lf = lbl_dir / (p + ".txt")
                gboxes = []
                for line in lf.read_text(encoding="utf-8").splitlines():
                    q = line.split()
                    if len(q) >= 6:
                        xs = [float(v) for v in q[1::2]]
                        ys2 = [float(v) for v in q[2::2]]
                        gboxes.append([min(xs) * 1920, min(ys2) * 1080,
                                       max(xs) * 1920, max(ys2) * 1080])
                det = r.boxes.xyxy.cpu().numpy() if r.boxes is not None else []
                hit = False
                for gb in gboxes:
                    for db in det:
                        ix0, iy0 = max(gb[0], db[0]), max(gb[1], db[1])
                        ix1, iy1 = min(gb[2], db[2]), min(gb[3], db[3])
                        iw, ih = max(0, ix1 - ix0), max(0, iy1 - iy0)
                        inter = iw * ih
                        ua = (gb[2]-gb[0])*(gb[3]-gb[1]) + (db[2]-db[0])*(db[3]-db[1]) - inter
                        if ua > 0 and inter / ua >= 0.5:
                            hit = True
                ok += 1 if hit else 0
        tier_map[tname] = {"images": len(stems), "recall@0.5iou": round(ok / len(stems), 4)}
        print(f"[tier] {tname}: {tier_map[tname]}", flush=True)
    report["size_tiers"] = tier_map

    # ---- 3) 负样本误检率 ----
    neg = [str(p) for p in (DS / "images/test").glob("*.jpg")
           if (DS / "labels/test" / (p.stem + ".txt")).stat().st_size == 0]
    neg += [str(p) for p in (DS / "images/val").glob("*.jpg")
            if (DS / "labels/val" / (p.stem + ".txt")).stat().st_size == 0]
    fp = 0
    B = 12
    for bi in range(0, len(neg), B):
        rs = model.predict(source=neg[bi:bi + B], conf=CONF, imgsz=896,
                           device=0, verbose=False)
        for r in rs:
            if r.boxes is not None and len(r.boxes) > 0:
                fp += 1
    fpr = fp / max(1, len(neg))
    report["neg_images"] = len(neg)
    report["neg_false_positive_images"] = fp
    report["neg_fpr"] = round(fpr, 4)
    print(f"[neg] FPR={fpr:.4f} ({fp}/{len(neg)})", flush=True)

    # ---- 4) 判定 ----
    verdicts = {
        "map50>=0.60": map50 >= THR["map50"],
        "map50-95>=0.40": map5095 >= THR["map5095"],
        "neg_fpr<=2%": fpr <= THR["neg_fpr"],
    }
    report["verdicts"] = verdicts
    report["accepted"] = all(verdicts.values())

    out = ROOT / "runs"
    out.mkdir(exist_ok=True)
    (out / "acceptance_summary.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    lines = ["# 验收报告", "", f"权重: `{args.weights}`", "",
             "| 指标 | 实测 | 阈值 | 判定 |", "|---|---|---|---|",
             f"| test mAP50 | {map50:.4f} | >=0.60 | {'✅' if verdicts['map50>=0.60'] else '❌'} |",
             f"| test mAP50-95 | {map5095:.4f} | >=0.40 | {'✅' if verdicts['map50-95>=0.40'] else '❌'} |",
             f"| 负样本误检率 | {fpr:.2%} ({fp}/{len(neg)}) | <=2% | {'✅' if verdicts['neg_fpr<=2%'] else '❌'} |",
             "", "## 小目标分层(test, IoU0.5 召回)", "", "| 档位 | 帧数 | 召回 |", "|---|---:|---|"]
    for t, v in tier_map.items():
        lines.append(f"| {t} | {v.get('images',0)} | {v.get('recall@0.5iou','-')} |")
    lines += ["", f"## 总判定: {'✅ 验收通过' if report['accepted'] else '❌ 未通过 — 见方案第8节调整后重训'}", ""]
    (out / "acceptance_report.md").write_text("\n".join(lines), encoding="utf-8")
    print("报告:", out / "acceptance_report.md")
    print("ACCEPTED" if report["accepted"] else "NOT-ACCEPTED")


if __name__ == "__main__":
    main()
