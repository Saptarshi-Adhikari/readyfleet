import React, { useEffect, useState } from 'react';
import { AlertTriangle, ArrowUpRight, Wrench, TrendingDown } from 'lucide-react';

interface FleetStatus {
  total_tails: number;
  mc_count: number;
  pmc_count: number;
  nmc_count: number;
  current_mc_rate: number;
  tail_states: Record<string, string>;
}

interface Driver {
  driver: string;
  impact_score: number;
  tails_grounded_count: number;
  tails_grounded: string[];
  recommendation: string;
}

export const CommandCenter: React.FC<{ onSelectTail: (tail: string) => void }> = ({ onSelectTail }) => {
  const [status, setStatus] = useState<FleetStatus | null>(null);
  const [forecast, setForecast] = useState<number[]>([]);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch('/api/fleet/status').then(res => res.json()),
      fetch('/api/fleet/forecast').then(res => res.json()),
      fetch('/api/drivers').then(res => res.json())
    ]).then(([statusData, forecastData, driverData]) => {
      setStatus(statusData);
      setForecast(forecastData.mc_forecast || []);
      setDrivers(driverData.drivers || []);
      setLoading(false);
    }).catch(err => console.error("Error loading command center data:", err));
  }, []);

  if (loading || !status) {
    return (
      <div className="p-8 text-center font-mono text-slate-400">
        <div className="inline-block animate-spin w-6 h-6 border-2 border-sky-400 border-t-transparent rounded-full mb-3"></div>
        <div>LOADING FLEET COMMAND OPERATIONAL STATE...</div>
      </div>
    );
  }

  const mcPct = (status.current_mc_rate * 100).toFixed(1);

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-xl font-bold tracking-wide text-slate-100 font-mono">COMMAND CENTER // OPERATIONAL OVERVIEW</h2>
          <p className="text-xs text-slate-400 font-mono">Air Power Fleet Availability & Readiness Dashboard</p>
        </div>
        <div className="flex items-center space-x-2 text-xs font-mono bg-slate-900 px-3 py-1.5 border border-slate-800 rounded">
          <span className="text-slate-400">STATUS:</span>
          <span className="text-emerald-400 font-bold">READY</span>
        </div>
      </div>

      {/* Operational Statistics Strip */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-[#111726] border border-[#232e47] p-4 rounded-sm">
          <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider mb-1">Total Fleet Count</div>
          <div className="text-3xl font-bold font-mono text-slate-100">{status.total_tails}</div>
          <div className="text-[11px] text-slate-500 font-mono mt-1">Possessed Airframes</div>
        </div>

        <div className="bg-[#111726] border border-[#232e47] p-4 rounded-sm border-l-4 border-l-emerald-500">
          <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider mb-1">Mission Capable (MC)</div>
          <div className="flex items-baseline space-x-2">
            <div className="text-3xl font-bold font-mono text-emerald-400">{status.mc_count}</div>
            <div className="text-xs font-mono text-emerald-500/80">({mcPct}%)</div>
          </div>
          <div className="text-[11px] text-slate-500 font-mono mt-1">Fully Ready Airframes</div>
        </div>

        <div className="bg-[#111726] border border-[#232e47] p-4 rounded-sm border-l-4 border-l-amber-500">
          <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider mb-1">Partial MC (PMC)</div>
          <div className="text-3xl font-bold font-mono text-amber-400">{status.pmc_count}</div>
          <div className="text-[11px] text-slate-500 font-mono mt-1">Restricted Roles</div>
        </div>

        <div className="bg-[#111726] border border-[#232e47] p-4 rounded-sm border-l-4 border-l-rose-500">
          <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider mb-1">Not Mission Capable (NMC)</div>
          <div className="text-3xl font-bold font-mono text-rose-400">{status.nmc_count}</div>
          <div className="text-[11px] text-slate-500 font-mono mt-1">Grounded Airframes</div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* 7-Day Readiness Projection Chart */}
        <div className="col-span-2 bg-[#111726] border border-[#232e47] p-5 rounded-sm flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold font-mono tracking-wide text-sky-400 uppercase flex items-center space-x-2">
              <TrendingDown className="w-4 h-4 text-sky-400" />
              <span>7-Day Readiness Projection (MC Rate)</span>
            </h3>
            <span className="text-[11px] font-mono text-slate-500">Target Horizon: T+7 Days</span>
          </div>

          <div className="h-44 flex items-end justify-between space-x-3 pt-6 px-2 border-b border-slate-800 pb-2">
            {forecast.map((val, idx) => {
              const heightPct = Math.max(15, val * 100);
              const pctText = (val * 100).toFixed(0);
              return (
                <div key={idx} className="flex-1 flex flex-col items-center group">
                  <div className="text-[10px] font-mono text-sky-300 font-bold opacity-80 group-hover:opacity-100 mb-1">
                    {pctText}%
                  </div>
                  <div className="w-full bg-slate-900 border border-slate-700/60 rounded-t-xs h-32 flex items-end overflow-hidden">
                    <div 
                      style={{ height: `${heightPct}%` }} 
                      className={`w-full transition-all duration-300 ${
                        val >= 0.7 ? 'bg-sky-500/80 border-t border-sky-300' : 'bg-amber-500/80 border-t border-amber-300'
                      }`}
                    ></div>
                  </div>
                  <div className="text-[10px] font-mono text-slate-400 mt-2">
                    {idx === 0 ? 'TODAY' : `T+${idx}d`}
                  </div>
                </div>
              );
            })}
          </div>

          <div className="mt-4 flex items-center justify-between text-[11px] font-mono text-slate-400">
            <span className="flex items-center space-x-1.5">
              <span className="w-2 h-2 rounded-full bg-sky-400"></span>
              <span>Predicted Fleet Readiness Level</span>
            </span>
            <span className="text-slate-500">Threshold: 70.0% Minimum Required</span>
          </div>
        </div>

        {/* Binding Constraints Summary */}
        <div className="bg-[#111726] border border-[#232e47] p-5 rounded-sm flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold font-mono tracking-wide text-rose-400 uppercase flex items-center space-x-2 mb-4">
              <AlertTriangle className="w-4 h-4 text-rose-400" />
              <span>Top Grounding Constraints</span>
            </h3>

            <div className="space-y-3">
              {drivers.slice(0, 3).map((d, i) => (
                <div key={i} className="bg-slate-900/80 border border-slate-800 p-3 rounded-xs font-mono">
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="text-slate-200 font-bold">{d.driver}</span>
                    <span className="text-rose-400 font-bold bg-rose-500/10 px-1.5 py-0.5 rounded text-[10px]">
                      {d.tails_grounded_count} TAILS
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400">{d.recommendation}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800 text-[10px] font-mono text-slate-500 flex justify-between">
            <span>IMPACT SCORE WEIGHTED</span>
            <span>RANKED BY DISRUPTION</span>
          </div>
        </div>
      </div>

      {/* Priority Operational Actions */}
      <div className="bg-[#111726] border border-[#232e47] p-5 rounded-sm">
        <h3 className="text-sm font-bold font-mono tracking-wide text-slate-200 uppercase flex items-center space-x-2 mb-4">
          <Wrench className="w-4 h-4 text-sky-400" />
          <span>Priority Operational Maintenance Actions</span>
        </h3>

        <div className="grid grid-cols-3 gap-4 font-mono text-xs">
          {Object.entries(status.tail_states)
            .filter(([_, s]) => s === 'NMC')
            .slice(0, 6)
            .map(([tail, s], _idx) => (
              <div 
                key={tail}
                onClick={() => onSelectTail(tail)}
                className="bg-slate-900 border border-slate-800 p-3 rounded-xs hover:border-sky-500/50 cursor-pointer transition-colors flex items-center justify-between"
              >
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-slate-100 font-bold">{tail}</span>
                    <span className="text-[10px] px-1.5 py-0.2 bg-rose-500/20 border border-rose-500/40 text-rose-400 rounded">
                      {s}
                    </span>
                  </div>
                  <div className="text-[10px] text-slate-400 mt-1">Critical RUL &lt; 24h Threshold</div>
                </div>
                <ArrowUpRight className="w-4 h-4 text-slate-500 group-hover:text-sky-400" />
              </div>
            ))}
        </div>
      </div>
    </div>
  );
};
