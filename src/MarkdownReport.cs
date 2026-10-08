using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;

namespace SentryHardener {
  public static class MarkdownReport {
    public static string Write(string dir, string target, int processExit, IEnumerable<EvidenceRecord> records) {
      Directory.CreateDirectory(dir); var list=records.ToList(); var file=System.IO.Path.Combine(dir,"supervision-"+DateTime.UtcNow.ToString("yyyyMMdd-HHmmss")+".md");
      var sb=new StringBuilder(); sb.AppendLine("# 视觉训练监督报告").AppendLine(); sb.AppendLine("生成时间 (UTC): "+DateTime.UtcNow.ToString("O"));
      sb.AppendLine("监督目标: `"+target.Replace("`","")+"`").AppendLine("训练进程退出码: "+processExit).AppendLine();
      sb.AppendLine("## 统计").AppendLine().AppendLine("- 记录数: "+list.Count).AppendLine("- 可疑/失败/不可验证: "+list.Count(x=>x.Status!="pass"));
      sb.AppendLine().AppendLine("## 证据").AppendLine().AppendLine("| 时间 | 帧 | 状态 | 置信度 | 原因 | 指纹 |").AppendLine("|---|---|---|---:|---|---|");
      foreach(var x in list) sb.AppendLine($"| {x.TimestampUtc} | {Clean(x.Frame)} | **{x.Status}** | {x.Confidence:0.###} | {Clean(x.Reason)} | `{x.Fingerprint}` |");
      File.WriteAllText(file,sb.ToString(),new UTF8Encoding(false)); return file;
    }
    static string Clean(string s)=> (s??"").Replace("|","\\|").Replace("\r", " ").Replace("\n", " ");
  }
}
