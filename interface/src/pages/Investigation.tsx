import React from 'react';
import Layout from '../components/Layout';
import { Search, ShieldAlert, Binary, Network, ExternalLink, Download, FileText, Share2 } from 'lucide-react';

const Investigation = () => {
  return (
    <Layout title="Incident Investigation Deep-Dive">
      <div className="grid grid-cols-1 xl:grid-cols-4 gap-8">
        {/* Left Sidebar: Incident Summary */}
        <div className="xl:col-span-1 space-y-6">
          <div className="bg-surface-container border border-outline-variant/30 rounded-2xl p-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-error/20 rounded-xl flex items-center justify-center text-error border border-error/30">
                <ShieldAlert className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold">INC-2024-42</h3>
                <span className="text-[10px] font-bold text-error uppercase">Critical Priority</span>
              </div>
            </div>
            
            <div className="space-y-4">
              <div className="space-y-1">
                <span className="text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">Target Asset</span>
                <p className="text-sm font-medium">FIN-NODE-PROXY-01</p>
              </div>
              <div className="space-y-1">
                <span className="text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">Attacker IP</span>
                <p className="text-sm font-mono text-primary">185.221.4.112</p>
              </div>
              <div className="space-y-1">
                <span className="text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">First Observed</span>
                <p className="text-sm">2026-05-15 14:12:04</p>
              </div>
            </div>

            <button className="w-full mt-8 py-3 bg-surface-container-high border border-outline-variant/30 text-xs font-bold rounded-xl hover:bg-surface-container-highest transition-all flex items-center justify-center gap-2">
              <Share2 className="w-3 h-3" /> Assign to Team
            </button>
          </div>

          <div className="bg-surface-container border border-outline-variant/30 rounded-2xl p-6">
            <h3 className="text-sm font-bold mb-4">Threat Intelligence</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-surface-container-low rounded-lg border border-outline-variant/10">
                <span className="text-xs">VirusTotal</span>
                <span className="text-xs font-bold text-error">42/72 Positives</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-surface-container-low rounded-lg border border-outline-variant/10">
                <span className="text-xs">AbuseIPDB</span>
                <span className="text-xs font-bold text-orange-400">Malicious (100%)</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-surface-container-low rounded-lg border border-outline-variant/10">
                <span className="text-xs">Cisco Talos</span>
                <span className="text-xs font-bold text-error">Blacklisted</span>
              </div>
            </div>
          </div>
        </div>

        {/* Center: Main Analysis */}
        <div className="xl:col-span-3 space-y-8">
          <div className="bg-surface-container border border-outline-variant/30 rounded-2xl flex flex-col min-h-[500px]">
            <div className="p-4 border-b border-outline-variant/30 flex items-center justify-between bg-surface-container-low/50">
              <div className="flex gap-4">
                <button className="text-xs font-bold px-4 py-2 bg-primary/10 text-primary rounded-lg border border-primary/20">Binary Analysis</button>
                <button className="text-xs font-bold px-4 py-2 text-on-surface-variant hover:text-on-surface transition-colors">Network Traffic</button>
                <button className="text-xs font-bold px-4 py-2 text-on-surface-variant hover:text-on-surface transition-colors">Process Tree</button>
              </div>
              <div className="flex gap-2">
                <button className="p-2 text-on-surface-variant hover:bg-surface-container-high rounded-lg"><Download className="w-4 h-4" /></button>
                <button className="p-2 text-on-surface-variant hover:bg-surface-container-high rounded-lg"><ExternalLink className="w-4 h-4" /></button>
              </div>
            </div>
            
            <div className="p-6 flex-1 font-mono text-xs overflow-auto bg-surface-container-lowest/50">
              <div className="space-y-2 opacity-80">
                <div className="flex gap-8">
                  <span className="text-outline">00000000</span>
                  <span className="text-on-surface-variant">4D 5A 90 00 03 00 00 00 04 00 00 00 FF FF 00 00</span>
                  <span className="text-primary/50">MZ..............</span>
                </div>
                <div className="flex gap-8">
                  <span className="text-outline">00000010</span>
                  <span className="text-on-surface-variant">B8 00 00 00 00 00 00 00 40 00 00 00 00 00 00 00</span>
                  <span className="text-primary/50">........@.......</span>
                </div>
                <div className="flex gap-8 bg-error/10 border-y border-error/20 py-1">
                  <span className="text-outline">00000020</span>
                  <span className="text-error font-bold">EB 0F 68 74 74 70 3A 2F 2F 6D 61 6C 2E 78 79 7A</span>
                  <span className="text-error font-bold">..http://mal.xyz</span>
                </div>
                <div className="flex gap-8">
                  <span className="text-outline">00000030</span>
                  <span className="text-on-surface-variant">00 00 00 00 00 00 00 00 00 00 00 00 D8 00 00 00</span>
                  <span className="text-primary/50">................</span>
                </div>
                <div className="pt-8 text-on-surface-variant italic font-sans">
                  {"// Heuristic flags triggered:"} <br/>
                  {"// [!] Found hardcoded URL in data section"} <br/>
                  {"// [!] High entropy detected in .rdata section (possible encryption)"} <br/>
                  {"// [!] Import calls for WinHTTP.dll and Advapi32.dll"}
                </div>
              </div>
            </div>

            <div className="p-6 bg-surface-container-high/30 border-t border-outline-variant/30">
              <h4 className="text-xs font-bold text-primary uppercase mb-3 flex items-center gap-2">
                <FileText className="w-3 h-3" /> Automated Conclusions
              </h4>
              <p className="text-sm leading-relaxed text-on-surface-variant">
                The analyzed sample is a <span className="text-on-surface font-bold">multi-stage dropper</span>. It attempts to establish persistence by creating a scheduled task named \"SystemUpdateSvc\" and subsequently beacons to <span className="text-primary underline">http://mal.xyz/gate.php</span> every 300 seconds. Recommendation: Revoke endpoint credentials and initiate full partition wipe on FIN-NODE-PROXY-01.
              </p>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default Investigation;
