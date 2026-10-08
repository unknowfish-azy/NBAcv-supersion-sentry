using System;
using System.IO;

namespace SentryHardener {
  public sealed class EvidenceRecord {
    public string TimestampUtc { get; set; } = DateTime.UtcNow.ToString("O");
    public string Frame { get; set; } = ""; public string Fingerprint { get; set; } = "";
    public string Status { get; set; } = ""; public string Reason { get; set; } = "";
    public double Confidence { get; set; }
  }
  public sealed class EvidenceStore {
    readonly string path;
    public EvidenceStore(string path) { this.path=path; Directory.CreateDirectory(System.IO.Path.GetDirectoryName(path)); }
    public void Append(TrainingResult result, SupervisionVerdict verdict) {
      var rec = new EvidenceRecord { Frame=result.Frame, Fingerprint=SupervisionProtocol.Fingerprint(result.Frame,result.Answer), Status=verdict.Status, Reason=verdict.Reason, Confidence=verdict.Confidence };
      File.AppendAllText(path, "{\"timestamp\":\""+rec.TimestampUtc+"\",\"frame\":\""+rec.Frame.Replace("\"","'")+"\",\"fingerprint\":\""+rec.Fingerprint+"\",\"status\":\""+rec.Status+"\",\"reason\":\""+rec.Reason.Replace("\"","'")+"\",\"confidence\":"+rec.Confidence.ToString(System.Globalization.CultureInfo.InvariantCulture)+"}" + Environment.NewLine);
    }
    public string Path => path;
  }
}
