import React from 'react';
import Layout from '../components/Layout';
import { ShieldAlert, Zap, Globe, Activity, ArrowUpRight, TrendingUp, AlertTriangle } from 'lucide-react';
import { motion } from 'framer-motion';

const Dashboard = () => {
  const stats = [
    { label: 'Active Threats', value: '12', trend: '+2', color: 'text-error', icon: ShieldAlert },
    { label: 'Signals Processed', value: '1.2M', trend: '15%', color: 'text-primary', icon: Zap },
    { label: 'Global Coverage', value: '98.2%', trend: '0.4%', color: 'text-green-400', icon: Globe },
    { label: 'System Load', value: '14%', trend: '-2%', color: 'text-on-surface-variant', icon: Activity },
  ];

  const alerts = [
    { id: 'AL-908', type: 'Critical', source: '192.168.1.45', event: 'Credential Spraying', time: '2m ago' },
    { id: 'AL-907', type: 'High', source: '8.8.8.8', event: 'Unknown QR Scan', time: '14m ago' },
    { id: 'AL-906', type: 'Medium', source: 'AWS-East-1', event: 'Sandbox Timeout', time: '1h ago' },
    { id: 'AL-905', type: 'Low', source: 'Local-Node', event: 'Config Change', time: '3h ago' },
  ];

  return (
    <Layout title="Autonomous SOC Dashboard">
      <div className="space-y-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {stats.map((stat, i) => (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              key={stat.label}
              className="bg-surface-container border border-outline-variant/30 p-6 rounded-2xl hover:border-primary/30 transition-all group"
            >
              <div className="flex justify-between items-start mb-4">
                <div className={`p-2 rounded-lg bg-surface-container-high ${stat.color} group-hover:scale-110 transition-transform`}>
                  <stat.icon className="w-5 h-5" />
                </div>
                <div className="flex items-center gap-1 text-[10px] font-bold text-green-400 bg-green-400/10 px-2 py-0.5 rounded-full">
                  <TrendingUp className="w-3 h-3" />
                  {stat.trend}
                </div>
              </div>
              <div className="flex flex-col">
                <span className="text-3xl font-bold tracking-tighter">{stat.value}</span>
                <span className="text-xs text-on-surface-variant font-medium mt-1">{stat.label}</span>
              </div>
            </motion.div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Active Alerts Table */}
          <div className="lg:col-span-2 bg-surface-container border border-outline-variant/30 rounded-2xl overflow-hidden flex flex-col">
            <div className="p-6 border-b border-outline-variant/30 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-2 h-6 bg-primary rounded-full"></div>
                <h2 className="font-bold tracking-tight">Active Incident Queue</h2>
              </div>
              <button className="text-xs text-primary font-bold hover:underline flex items-center gap-1">
                View Full Queue <ArrowUpRight className="w-3 h-3" />
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-surface-container-low/50">
                    <th className="px-6 py-4 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">ID</th>
                    <th className="px-6 py-4 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">Severity</th>
                    <th className="px-6 py-4 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">Source</th>
                    <th className="px-6 py-4 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">Event Type</th>
                    <th className="px-6 py-4 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest text-right">Age</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-outline-variant/10">
                  {alerts.map((alert) => (
                    <tr key={alert.id} className="hover:bg-surface-container-high/50 transition-colors cursor-pointer group">
                      <td className="px-6 py-4 text-xs font-mono text-primary">{alert.id}</td>
                      <td className="px-6 py-4">
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                          alert.type === 'Critical' ? 'bg-error/10 border-error text-error' :
                          alert.type === 'High' ? 'bg-orange-400/10 border-orange-400 text-orange-400' :
                          'bg-on-surface-variant/10 border-on-surface-variant text-on-surface-variant'
                        }`}>
                          {alert.type}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm font-medium">{alert.source}</td>
                      <td className="px-6 py-4 text-sm text-on-surface-variant">{alert.event}</td>
                      <td className="px-6 py-4 text-xs text-right text-on-surface-variant font-mono">{alert.time}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* AI Insights Panel */}
          <div className="bg-surface-container border border-outline-variant/30 rounded-2xl p-6 relative overflow-hidden flex flex-col">
            <div className="absolute top-0 right-0 p-4 opacity-10">
              <Zap className="w-24 h-24 text-primary" />
            </div>
            <div className="flex items-center gap-3 mb-6">
              <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center text-primary">
                <TrendingUp className="w-4 h-4" />
              </div>
              <h2 className="font-bold">Autonomous Insights</h2>
            </div>
            <div className="space-y-6 flex-1">
              <div className="p-4 bg-surface-container-high rounded-xl border-l-4 border-primary space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold text-primary uppercase">Recommendation</span>
                  <span className="text-[10px] text-on-surface-variant">Conf: 94%</span>
                </div>
                <p className="text-sm leading-relaxed">
                  Detected pattern of <span className="text-primary font-bold">lateral movement</span> on Segment-B. Suggesting isolation of Node-45 immediately.
                </p>
                <button className="w-full mt-2 py-2 bg-primary text-on-primary text-xs font-bold rounded-lg hover:brightness-110 transition-all shadow-lg shadow-primary/20">
                  Execute Isolation
                </button>
              </div>

              <div className="p-4 bg-surface-container-low border border-outline-variant/30 rounded-xl space-y-2">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-3 h-3 text-tertiary" />
                  <span className="text-[10px] font-bold text-tertiary uppercase">Anomaly Alert</span>
                </div>
                <p className="text-sm text-on-surface-variant">
                  QR scan from <span className="font-bold text-on-surface">External-12</span> redirected to a known phishing domain. Automated sandbox confirmed malicious payload.
                </p>
              </div>
            </div>
            <div className="mt-8 pt-6 border-t border-outline-variant/30">
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-medium text-on-surface-variant">Automation Status</span>
                <span className="text-xs font-bold">84% Efficiency</span>
              </div>
              <div className="h-1.5 w-full bg-surface-container-highest rounded-full overflow-hidden">
                <div className="h-full bg-primary w-[84%] rounded-full shadow-[0_0_10px_rgba(173,198,255,0.5)]"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default Dashboard;
