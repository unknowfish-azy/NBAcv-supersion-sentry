# C# 训练监督哨兵

目录：`E:\supervision-sentry`

这个工具把训练程序作为子进程运行。训练程序每输出一行 JSON（至少包含 `frame` 和 `answer`），哨兵就向第二个智谱视觉模型发送独立审查请求。监督模型只能返回 `pass`、`suspicious` 或 `fail`；网络错误、空响应和非法 JSON 都记录为 `unverifiable`，不会默认为通过。

## 构建

```powershell
cd E:\supervision-sentry
powershell -ExecutionPolicy Bypass -File .\build-cs.ps1
```

## 运行

```powershell
$env:ZHIPU_SUPERVISOR_ENDPOINT='https://open.bigmodel.cn/api/paas/v4/chat/completions'
$env:ZHIPU_SUPERVISOR_MODEL='glm-4v-flash'
.\sentry-hardener.cmd run python train.py --your-args
```

启动时输入 `ZHIPU_SUPERVISOR_API_KEY`。key 不写入报告、证据日志或命令行。报告写到 `reports\supervision-<UTC>.md`，可疑证据写到同目录 JSONL。

退出码：0=全部通过；2=发现可疑/失败；4=至少一条不可验证；3=配置或参数错误。

## 训练程序输出协议

```json
{"frame":"frame-001","answer":"模型答案","image":"E:\\frames\\001.jpg"}
```

普通日志行会被忽略。监督请求目前传递帧号、答案和图片路径；如需让监督模型直接看图，应在训练输出中提供可访问的图片数据 URL，并扩展 `SupervisorClient` 的 content 构造。
