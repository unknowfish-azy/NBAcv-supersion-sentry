# NBA 数据适配与哨兵

nba_data_guard.py 把 ESPN roster 的 JSON/CSV 统一成 nba.player_profile.v2，并生成给视觉模型使用的弱特征卡：

- team、jersey_number、player_id
- 身高/体重的数值化字段
- position_group、height_band、weight_band
- 来源和 as_of

这些字段用于候选排序、跨帧一致性和人工复核提示，不是单帧强身份证据。球衣号码和球队仍需结合 OCR、轨迹、多帧证据或真人确证。

## 运行

    python nba_data_guard.py --players "E:\\...\\火箭独行侠_球员特征.json" --schedule "E:\\...\\火箭独行侠_2025-26赛程.json" --out player_profile_manifest.json

也可以把两个输入都换成 CSV。JSON 和 CSV 运行应得到相同的球员/比赛数量和键集合。

## 哨兵状态

- PASS：没有发现阻断或告警。
- WARN：数据可继续使用，但需要人工复核，例如 roster 过期或赛程队伍不完整。
- BLOCK：禁止把结果当作训练输入，例如同一球队球衣号码重复。

当前哨兵检查：

- 球队内球衣号码重复；
- roster as_of 超过 180 天；
- 赛程是否覆盖预期球队；
- 帧时间戳与比赛日期、两队是否唯一匹配。
- 封闭集空帧与 COCO person 信号的区分。
- 颜色指标是否有足够的独立人工 ground truth。
- bootstrap 框底部中心点是否落在球场多边形内。
- 训练前内存和路径预检。

哨兵不做模型准确率估计，也不把外观特征变成身份结论。

颜色结果在独立人工样本少于 20 张时固定输出 `unverified`，不会采信伪标签自洽率。封闭集检测器没有检测结果时，必须结合 person/场景信号决定是 `valid_empty_closed_set`、`suspicious` 还是 `unverifiable`。
