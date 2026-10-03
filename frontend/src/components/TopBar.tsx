import React from 'react';
import { ShieldAlert, Clock, Database, UserCheck } from 'lucide-react';

export const TopBar: React.FC = () => {
  const currentTime = new Date().toISOString().replace('T', ' ').substring(0, 19) + ' UTC';

  return (
    <header className="h-14 bg-[#0e1422] border-b border-[#1e293b] px-6 flex items-center justify-between font-mono text-xs select-none">
      <div className="flex items-center space-x-4">
        <span className="text-slate-400 font-semibold tracking-wider">SIH26249 // AIR POWER READINESS CONSOLE</span>
        <span className="h-3 w-px bg-slate-700"></span>
        <span className="inline-flex items-center space-x-1.5 px-2 py-0.5 rounded bg-amber-500/10 border border-amber-500/30 text-amber-400 font-bold text-[11px]">
          <ShieldAlert className="w-3.5 h-3.5" />
          <span>SYNTHETIC DEMO DATA</span>
        </span>
      </div>

      <div className="flex items-center space-x-6 text-slate-400">
        <div className="flex items-center space-x-2">
          <Database className="w-3.5 h-3.5 text-slate-500" />
          <span>DB: <strong className="text-slate-200">SQLite (Seeded)</strong></span>
        </div>
        <div className="flex items-center space-x-2">
          <UserCheck className="w-3.5 h-3.5 text-slate-500" />
          <span>OPERATOR: <strong className="text-slate-200">COMMANDER_OFFICER</strong></span>
        </div>
        <div className="flex items-center space-x-2 text-slate-300">
          <Clock className="w-3.5 h-3.5 text-sky-400" />
          <span>{currentTime}</span>
        </div>
      </div>
    </header>
  );
};
