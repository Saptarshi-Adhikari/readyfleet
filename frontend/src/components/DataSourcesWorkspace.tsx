import React, { useEffect, useState } from 'react';
import { RefreshCw, Layers, Radio } from 'lucide-react';

interface SourceItem {
  source_id: string;
  name: string;
  domain: string;
  type: string;
  status: string;
  last_update: string;
  freshness: string;
  enabled: boolean;
}

export const DataSourcesWorkspace: React.FC = () => {
  const [sources, setSources] = useState<SourceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  const fetchSources = () => {
    fetch('/api/data-sources')
      .then(res => res.json())
      .then(data => {
        setSources(data.sources || []);
        setLoading(false);
      })
      .catch(err => console.error("Error fetching data sources:", err));
  };

  useEffect(() => {
    fetchSources();
  }, []);

  const triggerSyncAll = () => {
    setSyncing(true);
    fetch('/api/data-sources/sync-all', { method: 'POST' })
      .then(res => res.json())
      .then(() => {
        fetchSources();
        setSyncing(false);
      })
      .catch(() => setSyncing(false));
  };

  if (loading) {
    return (
      <div className="p-8 text-center font-mono text-slate-400">
        <div className="inline-block animate-spin w-6 h-6 border-2 border-sky-400 border-t-transparent rounded-full mb-3"></div>
        <div>LOADING MASTER DATA SOURCES REGISTRY...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6 font-mono select-none">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-xl font-bold tracking-wide text-slate-100 uppercase">DATA SOURCES // MASTER REGISTRY & LIVE STREAM STATUS</h2>
          <p className="text-xs text-slate-400">Provenance-controlled multi-stream data fabric and automatic ingestion scheduler</p>
        </div>

        <button 
          onClick={triggerSyncAll}
          disabled={syncing}
          className="flex items-center space-x-2 bg-sky-600 hover:bg-sky-500 text-slate-100 px-3.5 py-1.5 rounded text-xs font-bold transition-colors uppercase"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${syncing ? 'animate-spin' : ''}`} />
          <span>{syncing ? 'SYNCING ALL STREAMS...' : 'TRIGGER AUTO-SYNC OVERRIDE'}</span>
        </button>
      </div>

      {/* Stream Provenance Strip */}
      <div className="grid grid-cols-5 gap-3 text-xs">
        <div className="bg-[#111726] border border-[#232e47] p-3 rounded-xs">
          <span className="text-[10px] text-slate-500 block">OPERATIONS</span>
          <span className="text-emerald-400 font-bold flex items-center space-x-1.5 mt-0.5">
            <Radio className="w-3 h-3 animate-pulse text-emerald-400" />
            <span>LIVE REAL (adsb.lol)</span>
          </span>
        </div>
        <div className="bg-[#111726] border border-[#232e47] p-3 rounded-xs">
          <span className="text-[10px] text-slate-500 block">WEATHER</span>
          <span className="text-emerald-400 font-bold flex items-center space-x-1.5 mt-0.5">
            <Radio className="w-3 h-3 text-emerald-400" />
            <span>LIVE REAL (AWC)</span>
          </span>
        </div>
        <div className="bg-[#111726] border border-[#232e47] p-3 rounded-xs">
          <span className="text-[10px] text-slate-500 block">MAINTENANCE</span>
          <span className="text-amber-400 font-bold flex items-center space-x-1.5 mt-0.5">
            <span>HISTORICAL (FAA SDR)</span>
          </span>
        </div>
        <div className="bg-[#111726] border border-[#232e47] p-3 rounded-xs">
          <span className="text-[10px] text-slate-500 block">HEALTH / RUL</span>
          <span className="text-sky-400 font-bold flex items-center space-x-1.5 mt-0.5">
            <span>BENCHMARK (N-CMAPSS)</span>
          </span>
        </div>
        <div className="bg-[#111726] border border-[#232e47] p-3 rounded-xs">
          <span className="text-[10px] text-slate-500 block">LOGISTICS / CREW</span>
          <span className="text-slate-400 font-bold flex items-center space-x-1.5 mt-0.5">
            <span>SYNTHETIC FALLBACK</span>
          </span>
        </div>
      </div>

      {/* Registry Table */}
      <div className="bg-[#111726] border border-[#232e47] rounded-sm overflow-hidden text-xs">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-[#0e1422] border-b border-[#232e47] text-slate-400 font-bold uppercase text-[11px]">
              <th className="py-3 px-4">Source ID</th>
              <th className="py-3 px-4">Source Name</th>
              <th className="py-3 px-4">Domain</th>
              <th className="py-3 px-4">Type</th>
              <th className="py-3 px-4">Last Sync</th>
              <th className="py-3 px-4">Freshness</th>
              <th className="py-3 px-4 text-right">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1e293b]/60 text-slate-300">
            {sources.map((src) => (
              <tr key={src.source_id} className="hover:bg-[#162032]">
                <td className="py-3 px-4 font-bold text-slate-100">{src.source_id}</td>
                <td className="py-3 px-4 text-sky-400">{src.name}</td>
                <td className="py-3 px-4">{src.domain}</td>
                <td className="py-3 px-4 text-slate-400 text-[11px]">{src.type}</td>
                <td className="py-3 px-4 text-slate-400 text-[11px]">{src.last_update}</td>
                <td className="py-3 px-4">
                  <span className="px-2 py-0.5 rounded bg-sky-500/10 text-sky-400 font-bold text-[10px]">
                    {src.freshness}
                  </span>
                </td>
                <td className="py-3 px-4 text-right">
                  <span className="px-2.5 py-1 rounded bg-emerald-500/20 text-emerald-400 font-bold text-[10px]">
                    ● {src.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Transparent Data-Gap Panel */}
      <div className="bg-[#111726] border border-[#232e47] p-5 rounded-sm">
        <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider mb-3 flex items-center space-x-2">
          <Layers className="w-4 h-4 text-amber-400" />
          <span>Data Stream Gap Analysis & Defence Production Upgrade Path</span>
        </h3>

        <div className="grid grid-cols-2 gap-4 text-xs text-slate-300">
          <div className="p-3 bg-slate-900 border border-slate-800 rounded-xs">
            <span className="font-bold text-slate-100">HUMS / Live Military Engine Telemetry</span>
            <p className="text-[11px] text-slate-400 mt-1">No public live military HUMS stream exists. Currently using NASA N-CMAPSS benchmark degradation trajectories with synthetic fallback.</p>
          </div>
          <div className="p-3 bg-slate-900 border border-slate-800 rounded-xs">
            <span className="font-bold text-slate-100">Military Maintenance & Crew Capacity</span>
            <p className="text-[11px] text-slate-400 mt-1">Classified defence logistics metrics. Production deployment upgrades directly to IAF/MoD enterprise MRO systems (e.g. Maintenix/Ramco feeds).</p>
          </div>
        </div>
      </div>
    </div>
  );
};
