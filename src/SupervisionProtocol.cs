using System;
using System.Collections.Generic;
using System.Security.Cryptography;
using System.Text;

namespace SentryHardener {
  public sealed class TrainingResult {
    public string Frame { get; set; } = "";
    public string Answer { get; set; } = "";
    public string ImagePath { get; set; } = "";
    public string Raw { get; set; } = "";
  }
  public sealed class SupervisionRequest {
    public TrainingResult Result { get; set; } = new TrainingResult();
    public string Prompt { get; set; } = "";
  }
  public sealed class SupervisionVerdict {
    public string Status { get; set; } = "unverifiable";
    public string Reason { get; set; } = "";
    public double Confidence { get; set; }
    public string Raw { get; set; } = "";
  }
  public static class SupervisionProtocol {
    public static string Fingerprint(string frame, string answer) {
      using var sha = SHA256.Create();
      var bytes = sha.ComputeHash(Encoding.UTF8.GetBytes((frame ?? "") + "\n" + (answer ?? "")));
      return Convert.ToHexString(bytes).ToLowerInvariant();
    }
    public static SupervisionVerdict ParseVerdict(string text) {
      if (string.IsNullOrWhiteSpace(text)) return new SupervisionVerdict { Status="unverifiable", Reason="empty supervisor response" };
      try {
        var status = Extract(text,"status");
        status = status.Trim().ToLowerInvariant();
        if (status != "pass" && status != "suspicious" && status != "fail")
          return new SupervisionVerdict { Status="unverifiable", Reason="invalid verdict status", Raw=text };
        var reason = Extract(text,"reason");
        double confidence = 0; Double.TryParse(Extract(text,"confidence"), out confidence);
        return new SupervisionVerdict { Status=status, Reason=reason, Confidence=confidence, Raw=text };
      } catch (Exception ex) { return new SupervisionVerdict { Status="unverifiable", Reason="invalid JSON: " + ex.Message, Raw=text }; }
    }
    public static string Extract(string text,string key) { var marker="\""+key+"\""; var i=text.IndexOf(marker,StringComparison.OrdinalIgnoreCase); if(i<0)return ""; i=text.IndexOf(':',i); if(i<0)return ""; i++; while(i<text.Length && Char.IsWhiteSpace(text[i]))i++; if(i<text.Length&&text[i]=='\"'){i++;var j=i;while(j<text.Length){j=text.IndexOf('"',j);if(j<0)return "";if(j==i||text[j-1]!='\\')break;j++;}return j<0?"":text.Substring(i,j-i).Replace("\\\"","\"").Replace("\\n","\n");} var k=i;while(k<text.Length&&",}".IndexOf(text[k])<0)k++;return text.Substring(i,k-i).Trim(); }
  }
}
