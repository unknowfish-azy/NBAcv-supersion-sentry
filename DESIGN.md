# Supervision Sentry C# 强化引擎设计规格

## 目标
在 Windows 现场环境中，用单一 C# 工具对视觉验证目录进行独立监督，识别脚本造假、缓存冒充真实调用、日志篡改、账本重放和文件替换，并生成可复核报告。

## 运行形态
- 目录：`E:\supervision-sentry`
- 核心：`src\SentryHardener.cs`
- 构建：`build-cs.ps1`，使用现有 .NET 运行时编译，不要求 SDK。
- 入口：`sentry-hardener.cmd`
- 所有目标路径通过命令行参数提供，默认不修改被审计目录。

## 命令
- `scan <target>`：递归扫描 Python/C#/PowerShell/批处理源码中的高危模式。
- `audit-cache <jsonl>`：审计键重复、答案冲突、跨帧复用、DRY 答案、时间戳异常和解析错误。
- `verify-ledger <jsonl> --key-env VAR`：验证 HMAC-SHA256 追加哈希链，检测篡改、删插、重排和重放。
- `manifest <target>`：生成 SHA-256 文件完整性清单。
- `reverify <claims.jsonl>`：可选调用智谱 GLM-4V；密钥仅从环境变量读取，失败时明确标记 unverifiable。
- `all <target>`：执行以上可用审计并输出 JSON 与 Markdown 报告。

## 可信边界
- 工具只信任自身生成的签名账本和完整性清单。
- 未签名缓存、未绑定输入图片哈希的结果、DRY/Mock/Cache 命中结果不得判为真实 API 调用。
- API key 不写入文件、命令行、报告或日志正文。
- 实时重验失败不会降级为“通过”。

## 报告与退出码
- `reports/report-<UTC>.json`：机器可读结果。
- `reports/report-<UTC>.md`：人工审阅结果。
- 退出码：0=通过；2=发现高危或账本异常；3=输入/配置错误；4=实时重验不可验证。
- 报告记录工具版本、UTC 时间、目标根路径、文件哈希和每条发现的证据位置。

## 验证计划
1. 编译 C# 引擎并运行自检样例。
2. 对现有 `durant_vision` 目录扫描，比较 Python 报告中的 6 条已知信号。
3. 生成账本并由 C# 验证；篡改、删除、插入、重排各验证一次。
4. 修改源码后验证 manifest 检测到变化。
5. 无 API key 时确认重验返回不可验证且退出码为 4。
