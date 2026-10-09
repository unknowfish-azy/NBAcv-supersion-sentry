# GN 训练交接 · 三条命令跑完全流程

数据: `E:\杜兰特人物标注\durant_dataset_yolo`(v2, 按镜头划分, 勿重切)
方案: `E:\杜兰特人物标注\训练方案_GN版.md`(目标/轮次/损失/增强/验收 全说明)

## 1. 主训练(60轮早停, OOM自动降batch)

```powershell
cd E:\杜兰特人物标注\gn_training
python train_full.py
```

可选:
```powershell
python train_full.py --model yolo11s-seg.pt --batch 6   # 升级模型
python train_full.py --resume                           # 断点恢复
python train_full.py --finetune                         # 第二阶段 @1088 精调20轮
```

## 2. 验收(test 指标 + 负样本误检率 + 小目标分层, 自动出报告)

```powershell
python evaluate_acceptance.py
# 或指定权重
python evaluate_acceptance.py --weights E:\杜兰特人物标注\runs\durant_full\weights\best.pt
```

产出 `runs/acceptance_report.md`,三条全绿 = 验收通过:
- test mAP50 ≥ 0.60
- test mAP50-95 ≥ 0.40
- 负样本误检率 ≤ 2%

## 3. (可选)哨兵抽检

```powershell
$env:ZHIPU_SUPERVISOR_API_KEY='<key>'
$env:ZHIPU_SUPERVISOR_ENDPOINT='https://open.bigmodel.cn/api/paas/v4/chat/completions'
$env:ZHIPU_SUPERVISOR_MODEL='glm-4v-plus'   # 比flash更严格
E:\supervision-sentry\SentryHardener.exe run python E:\杜兰特人物标注\nbacv_tools\hou_supervise_child.py --sample 25
```

## 注意事项

1. **勿重新随机切分数据集** —— v2 已按镜头划分(消除轨迹泄漏), 自行切分会重新引入;
2. `workers` 固定为 2(本机 DataLoader 高并发曾内存崩溃), 不要调大;
3. OOM 时脚本自动把 batch 8→4→2, 不用手动干预;
4. 训练时不要同时手工改帧 JSON(会污染数据集);
5. 帧语义: 无 JSON = KD 不可见, 不是漏标。
