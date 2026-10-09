# -*- coding: utf-8 -*-
"""杜兰特分割 · 主训练脚本(GN 版)
- 数据: durant_dataset_yolo v2 (按镜头划分, 勿重新切分)
- 用法:
    python train_full.py                    # 基线: yolo11n-seg @896, 60轮早停
    python train_full.py --model yolo11s-seg.pt --batch 6
    python train_full.py --resume           # 从 last.pt 断点恢复
    python train_full.py --finetune         # 第二阶段: best.pt @1088 精调20轮
特性: OOM 自动降 batch; workers=2(本机 DataLoader 内存教训); 固定种子
"""
import argparse
import gc
import sys
from pathlib import Path

ROOT = Path(r"E:\杜兰特人物标注")
DATA = ROOT / "durant_dataset_yolo" / "data.yaml"


def train_once(model_path, epochs, imgsz, batch, name, lr0=None, patience=15, resume=False):
    from ultralytics import YOLO
    kwargs = dict(
        data=str(DATA),
        epochs=epochs,
        patience=patience,
        imgsz=imgsz,
        device=0,
        workers=2,              # 本机 32 worker 曾致内存崩溃, 固定 2
        project=str(ROOT / "runs"),
        name=name,
        cache=False,
        plots=True,
        seed=0,
        # ---- 损失权重 (见方案第5节) ----
        box=7.5,                # CIoU
        cls=0.5,                # BCE (单类=前景判别, 负样本帧参与负梯度压误检)
        dfl=1.5,                # Distribution Focal Loss
        # ---- 分割 ----
        overlap_mask=True,      # 同组mask合并省显存
        mask_ratio=4,           # mask 分辨率 1/4
        # ---- 增强 (见方案第6节) ----
        mosaic=1.0,
        close_mosaic=10,        # 最后10轮关mosaic
        copy_paste=0.3,         # 分割专属: 贴KD mask造难样本
        hsv_h=0.015, hsv_s=0.7, hsv_v=0.4,
        fliplr=0.5, flipud=0.0,
        scale=0.3, translate=0.1,
        erasing=0.2,
        mixup=0.0,
        # ---- 优化器 ----
        optimizer="auto",       # SGD(momentum .937) 或 AdamW, 自动
        warmup_epochs=3,
        cos_lr=True,
    )
    if lr0 is not None:
        kwargs["lr0"] = lr0
    if resume:
        model = YOLO(model_path)
        kwargs = {"resume": True, "workers": 2}
        model.train(**kwargs)
        return
    while batch >= 2:
        try:
            model = YOLO(model_path)
            print(f"[train] {model_path} imgsz={imgsz} batch={batch} epochs={epochs}", flush=True)
            model.train(batch=batch, **kwargs)
            return
        except RuntimeError as ex:
            if "out of memory" in str(ex).lower() or "OutOfMemoryError" in type(ex).__name__:
                batch = batch // 2
                gc.collect()
                try:
                    import torch
                    torch.cuda.empty_cache()
                except Exception:
                    pass
                print(f"[warn] OOM -> batch 降为 {batch}", flush=True)
            else:
                raise
    raise RuntimeError("batch 降到 2 仍 OOM, 请减小 imgsz")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="yolo11n-seg.pt", help="基线模型 (可换 yolo11s-seg.pt)")
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--patience", type=int, default=15)
    ap.add_argument("--imgsz", type=int, default=896)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--name", default="durant_full")
    ap.add_argument("--resume", action="store_true", help="从 runs/durant_full/weights/last.pt 恢复")
    ap.add_argument("--finetune", action="store_true", help="第二阶段: best.pt @1088 精调 20 轮")
    args = ap.parse_args()

    if args.resume:
        last = ROOT / "runs" / args.name / "weights" / "last.pt"
        if not last.exists():
            sys.exit(f"找不到 {last}, 无法恢复")
        train_once(str(last), 0, args.imgsz, args.batch, args.name, resume=True)
    elif args.finetune:
        best = ROOT / "runs" / args.name / "weights" / "best.pt"
        if not best.exists():
            sys.exit(f"找不到 {best}, 先跑基线训练")
        train_once(str(best), 20, 1088, max(4, args.batch // 2), args.name + "_ft", lr0=0.3 * 0.01)
    else:
        train_once(args.model, args.epochs, args.imgsz, args.batch, args.name,
                   patience=args.patience)
    print("TRAIN DONE")


if __name__ == "__main__":
    main()
