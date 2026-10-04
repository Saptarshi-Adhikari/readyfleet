import React, { useEffect, useState } from 'react';
import { AlertTriangle, ArrowUpRight, Wrench, TrendingDown, Radio, ShieldAlert } from 'lucide-react';
import { useLiveEvents } from '../hooks/useLiveEvents';

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

interface RiskSummary {
  total_components: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  avg_risk_score: number;
}

interface TopCritical {
  tail_no: string;
  comp_class: string;
  risk_score: number;
  risk_tier: string;
  contributing_factors: string[];
}

/** Provenance badge colours */
function DataClassBadge({ cls }: { cls: string }) {
  const styles: Record<string, string> = {
    'LIVE REAL': 'bg-emerald-950/60 border-emerald-800 text-emerald-400',
    'HISTORICAL REAL': 'bg-sky-950/60 border-sky-800 text-sky-400',
    'BENCHMARK': 'bg-amber-950/60 border-amber-800 text-amber-400',
    'PREDICTED': 'bg-violet-950/60 border-violet-800 text-violet-400',
    'SIMULATION': 'bg-slate-900 border-slate-700 text-slate-400',
    'SYNTHETIC': 'bg-slate-900 border-slate-700 text-slate-500',
    'N/A': 'bg-slate-900 border-slate-800 text-slate-600',
  };
  const match = Object.keys(styles).find((k) => cls.toUpperCase().includes(k)) || 'N/A';
  return (
    <span className={`px-2 py-0.5 border text-[10px] font-mono font-bold rounded uppercase ${styles[match]}`}>
      {cls}
    </span>
  );
}

export const CommandCenter: React.FC<{ onSelectTail: (tail: string) => void }> = ({ onSelectTail }) => {
  const [status, setStatus] = useState<FleetStatus | null>(null);
  const [forecast, setForecast] = useState<number[]>([]);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [riskSummary, setRiskSummary] = useState<RiskSummary | null>(null);
  const [topCritical, setTopCritical] = useState<TopCritical[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastSyncTime, setLastSyncTime] = useState<string>('—');

  const { isConnected } = useLiveEvents((evt) => {
    if (
      evt.event === 'operational_update' ||
      evt.event === 'weather_update' ||
      evt.event === 'source_status_update'
    ) {
      setLastSyncTime(new Date().toLocaleTimeString());
      fetch('/api/fleet/status')
        .then((r) => r.json())
        .then((data) => setStatus(data))
        .catch(() => {});
    }
  });

  useEffect(() => {
    Promise.all([
      fetch('/api/fleet/status').then((res) => res.json()),
      fetch('/api/fleet/forecast').then((res) => res.json()),
      fetch('/api/drivers').then((res) => res.json()),
      fetch('/api/predictions/summary').then((res) => res.json()),
    ])
      .then(([statusData, forecastData, driverData, riskData]) => {
        setStatus(statusData);
        setForecast(forecastData.mc_forecast || []);
        setDrivers(driverData.drivers || []);
        setRiskSummary(riskData.summary || null);
        setTopCritical(riskData.top_critical || []);
        setLoading(false);
      })
      .catch((err) => console.error('Error loading command center data:', err));
  }, []);

  if (loading || !status) {
    return (
      <div className="p-8 text-center font-mono text-slate-400">
        <div className="inline-block animate-spin w-6 h-6 border-2 border-sky-400 border-t-transparent rounded-full mb-3" />
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
          <h2 className="text-xl font-bold tracking-wide text-slate-100 font-mono">
            COMMAND CENTER // OPERATIONAL OVERVIEW
          </h2>
          <p className="text-xs text-slate-400 font-mono">
            Air Power Fleet Availability & Readiness Dashboard
          </p>
        </div>
        <div className="flex items-center space-x-3 text-xs font-mono">
          <div className="flex items-center space-x-2 bg-slate-900 px-3 py-1.5 border border-slate-800 rounded">
            <Radio
              className={`w-3.5 h-3.5 ${isConnected ? 'text-emerald-400 animate-pulse' : 'text-slate-500'}`}
            />
            <span className="text-slate-400">STREAM:</span>
            <span className={isConnected ? 'text-emerald-400 font-bold' : 'text-amber-400 font-bold'}>
              {isConnected ? 'LIVE SSE (AUTO-SYNC)' : 'RECONNECTING...'}
            </span>
          </div>
          <div className="text-slate-400 bg-slate-900 px-3 py-1.5 border border-slate-800 rounded">
            SYNCED: <span className="text-sky-300 font-bold">{lastSyncTime}</span>
          </div>
        </div>
      </div>

      {/* Provenance Strip */}
      <div className="bg-[#0b101d] border border-slate-800 p-2.5 rounded text-[11px] font-mono flex flex-wrap items-center gap-2">
        <span className="text-slate-500 font-bold uppercase mr-1">Data Provenance:</span>
        <DataClassBadge cls="LIVE REAL (adsb.lol)" />
        <DataClassBadge cls="LIVE REAL (AWC METAR)" />
        <DataClassBadge cls="HISTORICAL REAL (FAA SDRS)" />
        <DataClassBadge cls="BENCHMARK (N-CMAPSS)" />
        <DataClassBadge cls="PREDICTED (Risk Model)" />
        <DataClassBadge cls="SIMULATION (Logistics)" />
      </div>

      {/* Fleet KPIs */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-[#111726] border border-[#232e47] p-4 rounded-sm">
          <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider mb-1">
            Total Fleet Count
          </div>
          <div className="text-3xl font-bold font-mono text-slate-100">{status.total_tails}</div>
          <div className="text-[11px] text-slate-500 font-mono mt-1">Possessed Airframes</div>
          <div className="mt-2"><DataClassBadge cls="SIMULATION" /></div>
        </div>

        <div className="bg-[#111726] border border-[#232e47] p-4 rounded-sm border-l-4 border-l-emerald-500">
          <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider mb-1">
            Mission Capable (MC)
          </div>
          <div className="flex items-baseline space-x-2">
            <div className="text-3xl font-bold font-mono text-emerald-400">{status.mc_count}</div>
            <div className="text-xs font-mono text-emerald-500/80">({mcPct}%)</div>
          </div>
          <div className="text-[11px] text-slate-500 font-mono mt-1">Fully Ready Airframes</div>
          <div className="mt-2"><DataClassBadge cls="SIMULATION" /></div>
        </div>

        <div className="bg-[#111726] border border-[#232e47] p-4 rounded-sm border-l-4 border-l-amber-500">
          <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider mb-1">
            Partial MC (PMC)
          </div>
          <div className="text-3xl font-bold font-mono text-amber-400">{status.pmc_count}</div>
          <div className="text-[11px] text-slate-500 font-mono mt-1">Restricted Roles</div>
          <div className="mt-2"><DataClassBadge cls="SIMULATION" /></div>
        </div>

        <div className="bg-[#111726] border border-[#232e47] p-4 rounded-sm border-l-4 border-l-rose-500">
          <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider mb-1">
            Not Mission Capable (NMC)
          </div>
          <div className="text-3xl font-bold font-mono text-rose-400">{status.nmc_count}</div>
          <div className="text-[11px] text-slate-500 font-mono mt-1">Grounded Airframes</div>
          <div className="mt-2"><DataClassBadge cls="SIMULATION" /></div>
        </div>
      </div>

      {/* Forecast + Grounding Constraints */}
      <div className="grid grid-cols-3 gap-6">
        {/* 7-Day Forecast */}
        <div className="col-span-2 bg-[#111726] border border-[#232e47] p-5 rounded-sm flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold font-mono tracking-wide text-sky-400 uppercase flex items-center space-x-2">
              <TrendingDown className="w-4 h-4 text-sky-400" />
              <span>7-Day Readiness Projection (MC Rate)</span>
            </h3>
            <DataClassBadge cls="PREDICTED" />
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
                        val >= 0.7
                          ? 'bg-sky-500/80 border-t border-sky-300'
                          : 'bg-amber-500/80 border-t border-amber-300'
                      }`}
                    />
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
              <span className="w-2 h-2 rounded-full bg-sky-400" />
              <span>Predicted Fleet Readiness Level</span>
            </span>
            <span className="text-slate-500">Threshold: 70.0% Minimum Required</span>
          </div>
        </div>

        {/* Top Grounding Constraints */}
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

          <div className="mt-4 pt-3 border-t border-slate-800">
            <DataClassBadge cls="PREDICTED" />
          </div>
        </div>
      </div>

      {/* Risk Intelligence Panel */}
      {riskSummary && (
        <div className="bg-[#111726] border border-[#232e47] p-5 rounded-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold font-mono tracking-wide text-violet-400 uppercase flex items-center space-x-2">
              <ShieldAlert className="w-4 h-4 text-violet-400" />
              <span>Maintenance Risk Intelligence (FAA SDR Model)</span>
            </h3>
            <DataClassBadge cls="PREDICTED (FAA SDR Priors)" />
          </div>

          <div className="grid grid-cols-5 gap-3 mb-5 text-xs font-mono">
            {[
              { label: 'Components', value: riskSummary.total_components, color: 'text-slate-300' },
              { label: 'Critical', value: riskSummary.critical_count, color: 'text-rose-400' },
              { label: 'High', value: riskSummary.high_count, color: 'text-amber-400' },
              { label: 'Medium', value: riskSummary.medium_count, color: 'text-yellow-400' },
              { label: 'Low', value: riskSummary.low_count, color: 'text-emerald-400' },
            ].map(({ label, value, color }) => (
              <div key={label} className="bg-slate-900 border border-slate-800 p-3 rounded-xs text-center">
                <div className="text-[10px] text-slate-500 uppercase mb-1">{label}</div>
                <div className={`text-2xl font-bold ${color}`}>{value}</div>
              </div>
            ))}
          </div>

          {topCritical.length > 0 && (
            <div>
              <div className="text-[11px] text-slate-500 font-mono uppercase mb-2">
                Top Critical Components
              </div>
              <div className="grid grid-cols-3 gap-3">
                {topCritical.slice(0, 3).map((c, idx) => (
                  <div
                    key={idx}
                    className="bg-rose-950/20 border border-rose-900/50 p-3 rounded-xs font-mono text-xs"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-slate-200 font-bold">{c.tail_no}</span>
                      <span className="text-[10px] text-rose-400 font-bold">
                        {(c.risk_score * 100).toFixed(0)}% RISK
                      </span>
                    </div>
                    <div className="text-[10px] text-slate-400 capitalize">{c.comp_class}</div>
                    {c.contributing_factors[0] && (
                      <div className="text-[10px] text-rose-300/70 mt-1 leading-tight">
                        {c.contributing_factors[0]}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Priority Operational Actions */}
      <div className="bg-[#111726] border border-[#232e47] p-5 rounded-sm">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-bold font-mono tracking-wide text-slate-200 uppercase flex items-center space-x-2">
            <Wrench className="w-4 h-4 text-sky-400" />
            <span>Priority Operational Maintenance Actions</span>
          </h3>
          <DataClassBadge cls="SIMULATION" />
        </div>

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
