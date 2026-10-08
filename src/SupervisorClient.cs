using System;
using System.IO;
using System.Net.Http;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

namespace SentryHardener {
  public sealed class SupervisorClient : IDisposable {
    readonly HttpClient http; readonly string endpoint; readonly string key; readonly string model;
    public SupervisorClient(string endpoint, string key, string model, int timeoutSeconds=45) {
      this.endpoint = endpoint; this.key = key; this.model = model;
      http = new HttpClient { Timeout = TimeSpan.FromSeconds(timeoutSeconds) };
    }
    public async Task<SupervisionVerdict> ReviewAsync(SupervisionRequest request, CancellationToken ct) {
      try {
        var prompt = "你是独立监督哨兵。审查主视觉模型结果，只输出JSON：{" +
          "\"status\":\"pass|suspicious|fail\",\"reason\":\"简短证据\",\"confidence\":0到1}" +
          "。若证据不足用 suspicious。\n帧=" + request.Result.Frame + "\n主模型答案=" + request.Result.Answer +
          "\n图片路径=" + request.Result.ImagePath;
        var esc = prompt.Replace("\\","\\\\").Replace("\"","\\\"").Replace("\r", " ").Replace("\n","\\n");
        var messageContent = "[{\"type\":\"text\",\"text\":\""+esc+"\"}";
        if (File.Exists(request.Result.ImagePath)) { var b64=Convert.ToBase64String(File.ReadAllBytes(request.Result.ImagePath)); messageContent += ",{\"type\":\"image_url\",\"image_url\":{\"url\":\"data:image/jpeg;base64,"+b64+"\"}}"; }
        messageContent += "]";
        var body = "{\"model\":\""+model+"\",\"messages\":[{\"role\":\"user\",\"content\":"+messageContent+"}],\"temperature\":0}";
        using var msg = new HttpRequestMessage(HttpMethod.Post, endpoint);
        msg.Headers.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", key);
        msg.Content = new StringContent(body, Encoding.UTF8, "application/json");
        using var res = await http.SendAsync(msg, ct).ConfigureAwait(false);
        var payload = await res.Content.ReadAsStringAsync(ct).ConfigureAwait(false);
        if (!res.IsSuccessStatusCode) return new SupervisionVerdict { Status="unverifiable", Reason=$"HTTP {(int)res.StatusCode}", Raw="" };
        var content = SupervisionProtocol.Extract(payload,"content");
        return SupervisionProtocol.ParseVerdict(content);
      } catch (Exception ex) { return new SupervisionVerdict { Status="unverifiable", Reason=ex.GetType().Name + ": " + ex.Message }; }
    }
    public void Dispose() => http.Dispose();
  }
}
