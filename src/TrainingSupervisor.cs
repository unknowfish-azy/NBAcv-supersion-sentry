using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Threading;
using System.Threading.Tasks;

namespace SentryHardener {
  public sealed class TrainingSupervisor {
    readonly SupervisorClient client; readonly EvidenceStore store; readonly List<EvidenceRecord> records=new();
    public IReadOnlyList<EvidenceRecord> Records => records;
    public TrainingSupervisor(SupervisorClient c, EvidenceStore s){client=c;store=s;}
    public async Task<int> RunAsync(string file,string args,CancellationToken ct=default) {
      var psi=new ProcessStartInfo(file,args){UseShellExecute=false,RedirectStandardOutput=true,RedirectStandardError=true,CreateNoWindow=true};
      using var p=Process.Start(psi)!; var errors=new List<Task>();
      while(!p.StandardOutput.EndOfStream){ var line=await p.StandardOutput.ReadLineAsync(); if(string.IsNullOrWhiteSpace(line)) continue; TrainingResult r=null; try{ r=new TrainingResult{Frame=SupervisionProtocol.Extract(line,"frame"),Answer=SupervisionProtocol.Extract(line,"answer"),ImagePath=SupervisionProtocol.Extract(line,"image"),Raw=line}; if(String.IsNullOrEmpty(r.Frame)&&String.IsNullOrEmpty(r.Answer)) continue; }catch{} if(r==null) continue; var v=await client.ReviewAsync(new SupervisionRequest{Result=r},ct); var e=new EvidenceRecord{Frame=r.Frame,Fingerprint=SupervisionProtocol.Fingerprint(r.Frame,r.Answer),Status=v.Status,Reason=v.Reason,Confidence=v.Confidence}; records.Add(e); if(v.Status!="pass") store.Append(r,v); }
      await p.WaitForExitAsync(ct); return p.ExitCode;
    }
  }
}
