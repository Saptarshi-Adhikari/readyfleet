import React, { useEffect, useState } from 'react';
import { Search, ShieldCheck, AlertOctagon, AlertTriangle } from 'lucide-react';

interface FleetBoardProps {
  onSelectTail: (tailNo: string) => void;
}

export const FleetBoard: React.FC<FleetBoardProps> = ({ onSelectTail }) => {
  const [tailStates, setTailStates] = useState<Record<string, string>>({});
  const [filter, setFilter] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/fleet/status')
      .then(res => res.json())
      .then(data => {
        setTailStates(data.tail_states || {});
        setLoading(false);
      })
      .catch(err => console.error("Error loading fleet board:", err));
  }, []);

  if (loading) {
    return (
      <div className="p-8 text-center font-mono text-slate-400">
        <div className="inline-block animate-spin w-6 h-6 border-2 border-sky-400 border-t-transparent rounded-full mb-3"></div>
        <div>LOADING FLEET BOARD OPERATIONAL DATA...</div>
      </div>
    );
  }

  const tails = Object.keys(tailStates).filter(tail => {
    const status = tailStates[tail];
    const matchesFilter = filter === 'ALL' || status === filter;
    const matchesSearch = tail.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4 select-none">
        <div>
          <h2 className="text-xl font-bold tracking-wide text-slate-100 font-mono">FLEET BOARD // OPERATIONAL AIRFRAME STATUS</h2>
          <p className="text-xs text-slate-400 font-mono">Real-time status monitoring for 40 fleet airframes</p>
        </div>

        {/* Filter & Search Bar */}
        <div className="flex items-center space-x-3 font-mono text-xs">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-500" />
            <input 
              type="text" 
              placeholder="Search Tail ID..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-[#111726] border border-[#232e47] text-slate-200 pl-8 pr-3 py-1.5 rounded-sm focus:outline-none focus:border-sky-500 w-44"
            />
          </div>

          <div className="flex border border-[#232e47] rounded-sm bg-[#111726] p-0.5">
            {['ALL', 'MC', 'PMC', 'NMC'].map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1 rounded-2xs font-bold ${
                  filter === f 
                    ? 'bg-sky-500/20 text-sky-400 border border-sky-500/40' 
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Structured Operational Table */}
      <div className="bg-[#111726] border border-[#232e47] rounded-sm overflow-hidden select-none font-mono">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="bg-[#0e1422] border-b border-[#232e47] text-slate-400 font-bold uppercase tracking-wider text-[11px]">
              <th className="py-3 px-4">Aircraft Tail ID</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4">Assigned Base</th>
              <th className="py-3 px-4">Mission Priority</th>
              <th className="py-3 px-4">Engine RUL</th>
              <th className="py-3 px-4">Avionics RUL</th>
              <th className="py-3 px-4">Hydraulics RUL</th>
              <th className="py-3 px-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1e293b]/60">
            {tails.map((tail, idx) => {
              const status = tailStates[tail];
              let statusBadge = null;
              if (status === 'MC') {
                statusBadge = <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-bold"><ShieldCheck className="w-3 h-3"/><span>MC</span></span>;
              } else if (status === 'PMC') {
                statusBadge = <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded bg-amber-500/10 border border-amber-500/30 text-amber-400 font-bold"><AlertTriangle className="w-3 h-3"/><span>PMC</span></span>;
              } else {
                statusBadge = <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded bg-rose-500/10 border border-rose-500/30 text-rose-400 font-bold"><AlertOctagon className="w-3 h-3"/><span>NMC</span></span>;
              }

              const prio = (idx % 3) + 1;
              const engRul = Math.max(12, 120 - (idx * 2.8)).toFixed(0);
              const avRul = Math.max(24, 140 - (idx * 2.1)).toFixed(0);
              const hydRul = Math.max(18, 110 - (idx * 2.3)).toFixed(0);

              return (
                <tr 
                  key={tail}
                  onClick={() => onSelectTail(tail)}
                  className="hover:bg-[#162032] cursor-pointer transition-colors"
                >
                  <td className="py-3 px-4 font-bold text-slate-100">{tail}</td>
                  <td className="py-3 px-4">{statusBadge}</td>
                  <td className="py-3 px-4 text-slate-300">Base-Alpha</td>
                  <td className="py-3 px-4 text-slate-300">P{prio}</td>
                  <td className={`py-3 px-4 ${parseInt(engRul) < 24 ? 'text-rose-400 font-bold' : 'text-slate-300'}`}>{engRul}h</td>
                  <td className="py-3 px-4 text-slate-300">{avRul}h</td>
                  <td className="py-3 px-4 text-slate-300">{hydRul}h</td>
                  <td className="py-3 px-4 text-right">
                    <button className="px-2.5 py-1 bg-sky-500/10 border border-sky-500/30 text-sky-400 rounded hover:bg-sky-500/20 text-[11px] font-bold">
                      INSPECT PROFILE
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
