# Basketball pipeline v1

这组工具把篮球轨迹质量、球场几何和投篮事件分开，所有缺证据情况都返回 unknown 或 REVIEW。

## 组件

- `basketball_track_guard.py`：按时间戳审计球轨迹速度、断档、时间倒序和插值点。
- `court_geometry.py`：用球员框底部中心点过滤球场外样本，保留 rejection reason。
- `shot_event_fsm.py`：`idle -> possession -> flight -> made/miss`；必须有篮球和篮筐平面证据。

## 输入约定

篮球框为 `[x, y, width, height]`，轨迹行至少包含 `timestamp`、`track_id` 和 `bbox`。插值点必须显式写 `interpolated=true`，不会被当成真实检测。

投篮状态机不使用“落点在篮筐框内就算命中”。它需要持球距离、篮球向下穿越篮筐平面和横向篮筐范围；缺任一证据就保持 `unknown`。

## 当前边界

这是可测试的规则层，不是完整模型。还需要接入真实 YOLO/ByteTrack 输出、篮筐标定、球场透视变换和人工投篮事件验证集后，才能报告事件 precision/recall/F1。
