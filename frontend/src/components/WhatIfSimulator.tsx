import React, { useState } from 'react';
import { Sliders, CheckCircle2, TrendingUp } from 'lucide-react';

interface WhatIfResponse {
  latency_ms: number;
  before_mc_rate: number;
  after_mc_rate: number;
  mc_forecast: number[];
  unfilled_sorties: number[];
}

export const WhatIfSimulator: React.FC = () => {
  const [leverType, setLeverType] = useState<string>('expedite_spares');
  const [partNo, setPartNo] = useState<string>('PART-ENG-01');
  const [hours, setHours] = useState<number>(4);
  const [result, setResult] = useState<WhatIfResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const runSimulation = () => {
    setLoading(true);
    let leverPayload: any = { type: leverType };
    if (leverType === 'expedite_spares') {
      leverPayload.part_no = partNo;
    } else if (leverType === 'reassign_crew') {
      leverPayload.from_trade = 'avionics';
      leverPayload.to_trade = 'engine';
      leverPayload.hours = hours;
    }

    fetch('/api/whatif', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lever: leverPayload })
    })
      .then(res => res.json())
      .then(data => {
        setResult(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error running simulation:", err);
        setLoading(false);
      });
  };

  return (
    <div className="space-y-6 font-mono">
      {/* Header */}
      <div className="border-b border-slate-800 pb-4">
        <h2 className="text-xl font-bold tracking-wide text-slate-100 uppercase">WHAT-IF SIMULATOR // SCENARIO PLANNING</h2>
        <p className="text-xs text-slate-400">Evaluate how maintenance and resource decisions affect projected fleet readiness</p>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Controls Panel */}
        <div className="bg-[#111726] border border-[#232e47] p-5 rounded-sm space-y-4">
          <h3 className="text-sm font-bold text-sky-400 uppercase flex items-center space-x-2">
            <Sliders className="w-4 h-4 text-sky-400" />
            <span>Scenario Controls</span>
          </h3>

          <div className="space-y-3 text-xs">
            <div>
              <label className="block text-slate-400 mb-1">Lever Action Type</label>
              <select 
                value={leverType}
                onChange={(e) => setLeverType(e.target.value)}
                className="w-full bg-[#090d16] border border-[#232e47] text-slate-200 p-2 rounded focus:outline-none focus:border-sky-500"
              >
                <option value="expedite_spares">Expedite Spares Inventory</option>
                <option value="reassign_crew">Reassign Maintenance Crew</option>
              </select>
            </div>

            {leverType === 'expedite_spares' && (
              <div>
                <label className="block text-slate-400 mb-1">Target Component Part</label>
                <select 
                  value={partNo}
                  onChange={(e) => setPartNo(e.target.value)}
                  className="w-full bg-[#090d16] border border-[#232e47] text-slate-200 p-2 rounded focus:outline-none focus:border-sky-500"
                >
                  <option value="PART-ENG-01">PART-ENG-01 (Turbofan Module)</option>
                  <option value="PART-AV-01">PART-AV-01 (Radar Module)</option>
                  <option value="PART-HYD-01">PART-HYD-01 (Actuator Unit)</option>
                </select>
              </div>
            )}

            {leverType === 'reassign_crew' && (
              <div>
                <label className="block text-slate-400 mb-1">Reassign Hours: {hours}h</label>
                <input 
                  type="range" 
                  min="2" 
                  max="8" 
                  value={hours} 
                  onChange={(e) => setHours(parseInt(e.target.value))}
                  className="w-full"
                />
              </div>
            )}

            <button 
              onClick={runSimulation}
              disabled={loading}
              className="w-full mt-4 bg-sky-600 hover:bg-sky-500 text-slate-100 font-bold py-2.5 rounded transition-colors uppercase tracking-wider text-xs"
            >
              {loading ? 'RUNNING SCENARIO...' : 'EXECUTE SCENARIO'}
            </button>
          </div>
        </div>

        {/* Output Delta Comparison */}
        <div className="col-span-2 bg-[#111726] border border-[#232e47] p-5 rounded-sm flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-200 uppercase flex items-center space-x-2 mb-4">
              <TrendingUp className="w-4 h-4 text-emerald-400" />
              <span>Projected Impact & Operational Delta</span>
            </h3>

            {result ? (
              <div className="space-y-5">
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div className="bg-slate-900 border border-slate-800 p-3 rounded">
                    <div className="text-[10px] text-slate-400">BEFORE MC RATE</div>
                    <div className="text-xl font-bold text-slate-300 font-mono">{(result.before_mc_rate * 100).toFixed(1)}%</div>
                  </div>
                  <div className="bg-slate-900 border border-slate-800 p-3 rounded border-l-2 border-l-emerald-400">
                    <div className="text-[10px] text-slate-400">AFTER MC RATE</div>
                    <div className="text-xl font-bold text-emerald-400 font-mono">{(result.after_mc_rate * 100).toFixed(1)}%</div>
                  </div>
                  <div className="bg-slate-900 border border-slate-800 p-3 rounded">
                    <div className="text-[10px] text-slate-400">READINESS DELTA</div>
                    <div className="text-xl font-bold text-sky-400 font-mono">
                      +{( (result.after_mc_rate - result.before_mc_rate) * 100 ).toFixed(1)}%
                    </div>
                  </div>
                </div>

                <div className="bg-slate-900/80 border border-slate-800 p-3.5 rounded text-xs space-y-1">
                  <div className="text-slate-200 font-bold flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <span>Decision Impact Summary</span>
                  </div>
                  <p className="text-slate-400 text-[11px] pt-1">
                    Applying this lever removes the binding constraint on grounded airframes. Sub-200ms latency execution: <strong className="text-slate-200">{result.latency_ms.toFixed(1)} ms</strong>.
                  </p>
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-slate-500 text-xs">
                Select a scenario lever on the left and click "EXECUTE SCENARIO" to view live readiness deltas.
              </div>
            )}
          </div>

          <div className="pt-3 border-t border-slate-800 text-[10px] text-slate-500 flex justify-between">
            <span>PURE STATE PATCHING (SNAPSHOT CLONED)</span>
            <span>NO PERMANENT MUTATION</span>
          </div>
        </div>
      </div>
    </div>
  );
};
