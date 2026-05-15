import React from 'react';
import Layout from '../components/Layout';
import { Network, ArrowRight, ShieldCheck, Cpu, Code, Database, Search } from 'lucide-react';
import { motion } from 'framer-motion';

const WorkflowTrace = () => {
  const traceNodes = [
    { 
      id: 'step-1', 
      title: 'Signal Ingestion', 
      source: 'Webhook Gateway', 
      status: 'completed', 
      timestamp: '14:20:01',
      details: 'Received raw HTTP payload from external QR scanner agent.'
    },
    { 
      id: 'step-2', 
      title: 'Payload Decryption', 
      source: 'Security Engine', 
      status: 'completed', 
      timestamp: '14:20:02',
      details: 'Validated JWT and decrypted Base64-encoded threat vector.'
    },
    { 
      id: 'step-3', 
      title: 'Heuristic Analysis', 
      source: 'AI Core v4.1', 
      status: 'completed', 
      timestamp: '14:20:04',
      details: 'Identified suspicious URL redirect pattern and high-risk domain entropy.'
    },
    { 
      id: 'step-4', 
      title: 'Sandbox Detonation', 
      source: 'QuishSandbox', 
      status: 'active', 
      timestamp: '14:20:10',
      details: 'Executing malicious payload in isolated Ubuntu 22.04 environment. Monitoring network egress.'
    },
    { 
      id: 'step-5', 
      title: 'Threat Intel Lookup', 
      source: 'VirusTotal API', 
      status: 'pending', 
      timestamp: '---',
      details: 'Cross-referencing file hashes with global reputation databases.'
    },
  ];

  return (
    <Layout title="Autonomous Workflow Trace">
      <div className="max-w-5xl mx-auto space-y-12">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-primary/20 rounded-xl flex items-center justify-center border border-primary/30">
              <Network className="w-6 h-6 text-primary" />
            </div>
            <div>
              <h2 className="text-2xl font-bold tracking-tight">Trace: TR-9210-QX</h2>
              <p className="text-sm text-on-surface-variant flex items-center gap-2">
                Started by <span className="text-primary font-mono font-bold uppercase">System-Agent</span> • 22 seconds elapsed
              </p>
            </div>
          </div>
          <div className="flex gap-3">
            <button className="px-4 py-2 border border-outline-variant text-sm font-bold rounded-lg hover:bg-surface-container-high transition-all">
              Export Logs
            </button>
            <button className="px-4 py-2 bg-error text-on-error text-sm font-bold rounded-lg hover:brightness-110 transition-all">
              Terminate Trace
            </button>
          </div>
        </div>

        <div className="relative">
          {/* Vertical Line */}
          <div className="absolute left-[23px] top-0 bottom-0 w-[2px] bg-gradient-to-b from-primary via-primary/50 to-outline-variant/20"></div>

          <div className="space-y-12">
            {traceNodes.map((node, i) => (
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.15 }}
                key={node.id}
                className="relative pl-16 group"
              >
                {/* Node Indicator */}
                <div className={`absolute left-0 top-0 w-12 h-12 rounded-full border-4 border-background z-10 flex items-center justify-center transition-all duration-300 ${
                  node.status === 'completed' ? 'bg-primary shadow-[0_0_15px_rgba(173,198,255,0.4)]' :
                  node.status === 'active' ? 'bg-surface-container-highest border-primary animate-pulse' :
                  'bg-surface-container-low border-outline-variant'
                }`}>
                  {node.status === 'completed' && <ShieldCheck className="w-5 h-5 text-on-primary" />}
                  {node.status === 'active' && <Cpu className="w-5 h-5 text-primary" />}
                  {node.status === 'pending' && <Code className="w-5 h-5 text-on-surface-variant" />}
                </div>

                <div className={`p-6 rounded-2xl border transition-all duration-300 ${
                  node.status === 'active' 
                    ? 'bg-surface-container-high border-primary/50 shadow-xl' 
                    : 'bg-surface-container border-outline-variant/20 hover:border-outline-variant/50'
                }`}>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-3">
                      <span className="font-bold text-lg">{node.title}</span>
                      <span className="text-[10px] font-bold text-on-surface-variant bg-surface-container-low px-2 py-0.5 rounded border border-outline-variant uppercase tracking-widest">
                        {node.source}
                      </span>
                    </div>
                    <span className="text-xs font-mono text-on-surface-variant">{node.timestamp}</span>
                  </div>
                  <p className="text-sm text-on-surface-variant leading-relaxed">
                    {node.details}
                  </p>
                  
                  {node.status === 'active' && (
                    <div className="mt-4 pt-4 border-t border-outline-variant/30 flex items-center justify-between">
                      <div className="flex gap-2">
                        <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                        <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                        <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                      </div>
                      <span className="text-xs text-primary font-bold italic">Processing real-time telemetry...</span>
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-8">
          <div className="bg-surface-container-low border border-outline-variant/30 rounded-2xl p-6">
            <h3 className="text-sm font-bold uppercase tracking-widest text-on-surface-variant mb-4">Resource Allocation</h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-xs text-on-surface-variant">Compute Units</span>
                <span className="text-xs font-mono">1.2 CU</span>
              </div>
              <div className="h-1.5 w-full bg-surface-container-highest rounded-full overflow-hidden">
                <div className="h-full bg-primary w-[35%] rounded-full"></div>
              </div>
            </div>
          </div>
          <div className="bg-surface-container-low border border-outline-variant/30 rounded-2xl p-6">
            <h3 className="text-sm font-bold uppercase tracking-widest text-on-surface-variant mb-4">Data Persistence</h3>
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 bg-surface-container-highest rounded-lg flex items-center justify-center">
                <Database className="w-5 h-5 text-on-surface-variant" />
              </div>
              <div>
                <p className="text-xs font-bold">PostgreSQL Cluster-04</p>
                <p className="text-[10px] text-on-surface-variant">Table: incident_events_audit</p>
              </div>
              <ShieldCheck className="w-4 h-4 text-green-400 ml-auto" />
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default WorkflowTrace;
