using System;
using System.IO;
using System.Threading.Tasks;

namespace SentryHardener {
  public static class Program {
    public static async Task<int> Main(string[] args) {
      if(args.Length<2 || args[0]!="run"){Console.Error.WriteLine("用法: sentry-hardener run <训练程序> [参数]");return 3;}
      var key=Environment.GetEnvironmentVariable("ZHIPU_SUPERVISOR_API_KEY"); if(string.IsNullOrWhiteSpace(key)){Console.Write("输入监督模型 API key（不会写入磁盘）: "); key=ReadSecret();}
      if(string.IsNullOrWhiteSpace(key)){Console.Error.WriteLine("未提供监督模型 key，拒绝启动");return 3;}
      var endpoint=Environment.GetEnvironmentVariable("ZHIPU_SUPERVISOR_ENDPOINT")??"https://open.bigmodel.cn/api/paas/v4/chat/completions";
      var model=Environment.GetEnvironmentVariable("ZHIPU_SUPERVISOR_MODEL")??"glm-4v-flash";
      var reports=Path.Combine("E:\\supervision-sentry","reports"); var evidence=Path.Combine(reports,"evidence-"+DateTime.UtcNow.ToString("yyyyMMdd-HHmmss")+".jsonl");
      using var client=new SupervisorClient(endpoint,key,model); var sup=new TrainingSupervisor(client,new EvidenceStore(evidence));
      var code=await sup.RunAsync(args[1],string.Join(" ",args,2,args.Length-2)); var report=MarkdownReport.Write(reports,args[1],code,sup.Records); Console.WriteLine("监督报告: "+report); Console.WriteLine("证据日志: "+evidence);
      foreach(var x in sup.Records) if(x.Status=="unverifiable") return 4; foreach(var x in sup.Records) if(x.Status=="suspicious"||x.Status=="fail") return 2; return code==0?0:code;
    }
    static string ReadSecret(){return Console.ReadLine()??"";}
  }
}
