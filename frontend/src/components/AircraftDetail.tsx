import React, { useEffect, useState } from 'react';
import { AlertOctagon, ShieldCheck, AlertTriangle, ArrowLeft, Clock, Activity } from 'lucide-react';

interface ComponentDetail {
  id: number;
  comp_class: string;
  serial_no: string;
  installed_cycles: number;
  installed_hours: number;
  predicted_rul_h: number;
  ci_low: number;
  ci_high: number;
  threshold_h: number;
  status: string;
}

interface AircraftDetailData {
  data_class: string;
  aircraft: {
    tail_no: string;
    type: string;
    base: string;
    mission_priority: number;
    status: string;
  };
  components: ComponentDetail[];
  grounding_reasons: string[];
  blocking_constraint: {
    reason: string;
    required_action: string;
    required_spare: string;
    required_trade: string;
    est_duration: string;
  };
}

interface AircraftDetailProps {
  tailNo: string;
  onBack: () => void;
}

export const AircraftDetail: React.FC<AircraftDetailProps> = ({ tailNo, onBack }) => {
  const [data, setData] = useState<AircraftDetailData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/aircraft/${tailNo}`)
      .then(res => res.json())
      .then(resData => {
        setData(resData);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error loading aircraft detail:", err);
        setLoading(false);
      });
  }, [tailNo]);

  if (loading || !data) {
    return (
      <div className="p-8 text-center font-mono text-slate-400">
        <div className="inline-block animate-spin w-6 h-6 border-2 border-sky-400 border-t-transparent rounded-full mb-3"></div>
        <div>LOADING AIRCRAFT OPERATIONAL PROFILE FOR {tailNo}...</div>
      </div>
    );
  }

  const { aircraft, components, blocking_constraint } = data;

  let statusBadge = null;
  if (aircraft.status === 'MC') {
    statusBadge = <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-bold"><ShieldCheck className="w-4 h-4"/><span>MISSION CAPABLE (MC)</span></span>;
  } else if (aircraft.status === 'PMC') {
    statusBadge = <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-amber-500/10 border border-amber-500/30 text-amber-400 font-bold"><AlertTriangle className="w-4 h-4"/><span>PARTIAL MC (PMC)</span></span>;
  } else {
    statusBadge = <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-rose-500/10 border border-rose-500/30 text-rose-400 font-bold"><AlertOctagon className="w-4 h-4"/><span>NOT MISSION CAPABLE (NMC)</span></span>;
  }

  return (
    <div className="space-y-6 font-mono select-none">
      {/* Top Header & Navigation */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center space-x-4">
          <button 
            onClick={onBack}
            className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center space-x-3">
              <h2 className="text-2xl font-bold tracking-wide text-slate-100">{aircraft.tail_no}</h2>
              {statusBadge}
            </div>
            <p className="text-xs text-slate-400 mt-0.5">TYPE: {aircraft.type} | BASE: {aircraft.base} | PRIORITY: P{aircraft.mission_priority}</p>
          </div>
        </div>

        <div className="text-right text-xs">
          <span className="text-slate-400">DATA SOURCE: </span>
          <span className="text-sky-400 font-bold">5-STREAM INTEGRATED FUSION</span>
        </div>
      </div>

      {/* Current Blocking Constraint (Primary Focus) */}
      <div className="bg-[#111726] border border-rose-500/40 p-5 rounded-sm">
        <h3 className="text-xs font-bold text-rose-400 uppercase tracking-wider mb-3 flex items-center space-x-2">
          <AlertOctagon className="w-4 h-4 text-rose-400" />
          <span>CURRENT BLOCKING CONSTRAINT (PRIMARY NMC CAUSE)</span>
        </h3>

        <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-xs space-y-3">
          <div className="text-sm font-bold text-slate-100">{blocking_constraint.reason}</div>
          
          <div className="grid grid-cols-4 gap-4 text-xs pt-2 border-t border-slate-800">
            <div>
              <span className="text-slate-500 block text-[10px]">REQUIRED ACTION</span>
              <span className="text-slate-200 font-bold">{blocking_constraint.required_action}</span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px]">REQUIRED SPARE PART</span>
              <span className="text-sky-400 font-bold">{blocking_constraint.required_spare}</span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px]">TECHNICIAN TRADE</span>
              <span className="text-amber-400 font-bold uppercase">{blocking_constraint.required_trade}</span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px]">ESTIMATED DURATION</span>
              <span className="text-slate-200 font-bold">{blocking_constraint.est_duration}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Component Health Diagnostics Grid */}
      <div className="bg-[#111726] border border-[#232e47] p-5 rounded-sm">
        <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider mb-4 flex items-center space-x-2">
          <Activity className="w-4 h-4 text-sky-400" />
          <span>Component Health & RUL Predictions</span>
        </h3>

        <div className="grid grid-cols-2 gap-4 text-xs">
          {components.map((comp) => {
            const isCrit = comp.predicted_rul_h < 24.0;
            return (
              <div 
                key={comp.id} 
                className={`p-4 bg-slate-900 border rounded-xs ${
                  isCrit ? 'border-rose-500/50 bg-rose-500/5' : 'border-slate-800'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-bold text-slate-200 uppercase text-xs">{comp.comp_class}</span>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                    isCrit ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40' : 'bg-emerald-500/20 text-emerald-400'
                  }`}>
                    {comp.status}
                  </span>
                </div>

                <div className="space-y-2">
                  <div className="flex items-baseline justify-between">
                    <span className="text-slate-400 text-[11px]">PREDICTED RUL:</span>
                    <span className={`text-base font-bold ${isCrit ? 'text-rose-400' : 'text-sky-400'}`}>
                      {comp.predicted_rul_h.toFixed(1)}h
                    </span>
                  </div>

                  <div className="flex justify-between text-[10px] text-slate-500">
                    <span>ESTIMATED ERROR RANGE (±1.5× MAE):</span>
                    <span className="font-mono text-slate-300">{comp.ci_low.toFixed(1)}h – {comp.ci_high.toFixed(1)}h</span>
                  </div>

                  <div className="flex justify-between text-[10px] text-slate-500">
                    <span>SERIAL NO: {comp.serial_no}</span>
                    <span>INSTALLED: {comp.installed_cycles} CYCLES</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Maintenance History Timeline */}
      <div className="bg-[#111726] border border-[#232e47] p-5 rounded-sm">
        <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider mb-4 flex items-center space-x-2">
          <Clock className="w-4 h-4 text-slate-400" />
          <span>Chronological Maintenance Events</span>
        </h3>

        <div className="space-y-3 text-xs">
          <div className="p-3 bg-slate-900 border border-slate-800 rounded-xs flex items-center justify-between">
            <div>
              <span className="text-slate-400 text-[10px]">2026-10-02 // SCHEDULED</span>
              <div className="font-bold text-slate-200">200-Cycle Routine Engine Inspection</div>
            </div>
            <span className="text-emerald-400 font-bold text-[11px]">COMPLETED</span>
          </div>

          <div className="p-3 bg-slate-900 border border-slate-800 rounded-xs flex items-center justify-between">
            <div>
              <span className="text-slate-400 text-[10px]">2026-09-24 // UNSCHEDULED</span>
              <div className="font-bold text-slate-200">Avionics Sensor Calibration</div>
            </div>
            <span className="text-emerald-400 font-bold text-[11px]">COMPLETED</span>
          </div>
        </div>
      </div>
    </div>
  );
};
