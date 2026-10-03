import React, { useEffect, useState } from 'react';
import { TrendingUp, Layers } from 'lucide-react';

export const ReadinessForecast: React.FC = () => {
  const [forecast, setForecast] = useState<number[]>([]);
  const [unfilled, setUnfilled] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/fleet/forecast')
      .then(res => res.json())
      .then(data => {
        setForecast(data.mc_forecast || []);
        setUnfilled(data.unfilled_sorties || []);
        setLoading(false);
      })
      .catch(err => console.error("Error loading forecast:", err));
  }, []);

  if (loading) {
    return (
      <div className="p-8 text-center font-mono text-slate-400">
        <div className="inline-block animate-spin w-6 h-6 border-2 border-sky-400 border-t-transparent rounded-full mb-3"></div>
        <div>LOADING 7-DAY READINESS ANALYTICS PROJECTION...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6 font-mono select-none">
      {/* Header */}
      <div className="border-b border-slate-800 pb-4">
        <h2 className="text-xl font-bold tracking-wide text-slate-100 uppercase">READINESS FORECAST // 7-DAY OPERATIONAL ANALYSIS</h2>
        <p className="text-xs text-slate-400">Detailed projected fleet availability and unfilled sortie gap metrics</p>
      </div>

      {/* Main Readiness Projection Visualization */}
      <div className="bg-[#111726] border border-[#232e47] p-6 rounded-sm space-y-6">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-sky-400 uppercase tracking-wider flex items-center space-x-2">
            <TrendingUp className="w-4 h-4 text-sky-400" />
            <span>7-Day Mission Capable Forecast (Day 0 → Day 6)</span>
          </h3>
          <span className="text-xs text-slate-400">MIN REQUIRED THRESHOLD: 70.0%</span>
        </div>

        <div className="grid grid-cols-7 gap-3">
          {forecast.map((val, idx) => {
            const mcPct = (val * 100).toFixed(1);
            const isBelow = val < 0.7;
            const un = unfilled[idx] || 0;

            return (
              <div key={idx} className="bg-slate-900 border border-slate-800 p-4 rounded-xs text-center space-y-3">
                <div className="text-xs font-bold text-slate-300">
                  {idx === 0 ? 'DAY 0 (TODAY)' : `DAY ${idx}`}
                </div>

                <div className="py-2 bg-[#090d16] rounded border border-slate-800">
                  <div className={`text-xl font-bold ${isBelow ? 'text-amber-400' : 'text-emerald-400'}`}>
                    {mcPct}%
                  </div>
                  <div className="text-[10px] text-slate-500 mt-0.5">MC RATE</div>
                </div>

                <div className="text-[11px] space-y-1 text-slate-400 pt-1 border-t border-slate-800/80">
                  <div className="flex justify-between">
                    <span>UNFILLED:</span>
                    <span className={`font-bold ${un > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>{un} SORTIES</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Forecast Drivers Breakdown */}
      <div className="bg-[#111726] border border-[#232e47] p-5 rounded-sm">
        <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider mb-4 flex items-center space-x-2">
          <Layers className="w-4 h-4 text-amber-400" />
          <span>Operational Forecast Drivers & Degradation Causes</span>
        </h3>

        <div className="space-y-3 text-xs">
          <div className="p-3 bg-slate-900 border border-slate-800 rounded-xs flex items-center justify-between">
            <div>
              <span className="font-bold text-slate-200">DAY 2 → DAY 4: Cumulative Engine RUL Degradation</span>
              <p className="text-slate-400 text-[11px] mt-0.5">Turbofan module operational hours reaching the 24h critical threshold on 4 airframes.</p>
            </div>
            <span className="text-amber-400 font-bold px-2 py-0.5 bg-amber-500/10 border border-amber-500/30 rounded text-[10px]">HIGH IMPACT</span>
          </div>

          <div className="p-3 bg-slate-900 border border-slate-800 rounded-xs flex items-center justify-between">
            <div>
              <span className="font-bold text-slate-200">DAY 5: Rotables Spare Shortage Bottleneck</span>
              <p className="text-slate-400 text-[11px] mt-0.5">Zero on-hand stock for PART-ENG-01 creating extended grounding windows.</p>
            </div>
            <span className="text-rose-400 font-bold px-2 py-0.5 bg-rose-500/10 border border-rose-500/40 rounded text-[10px]">CRITICAL BOTTLENECK</span>
          </div>
        </div>
      </div>
    </div>
  );
};
