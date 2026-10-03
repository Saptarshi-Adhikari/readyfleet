import React from 'react';
import { 
  LayoutDashboard, 
  Grid, 
  Plane, 
  TrendingUp, 
  Wrench, 
  Sliders, 
  GitCompare, 
  FileCheck2, 
  Radio 
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab }) => {
  const navItems = [
    { id: 'command', label: '1. Command Center', icon: LayoutDashboard },
    { id: 'fleet', label: '2. Fleet Board', icon: Grid },
    { id: 'aircraft', label: '3. Aircraft Detail', icon: Plane },
    { id: 'readiness', label: '4. Readiness Forecast', icon: TrendingUp },
    { id: 'maintenance', label: '5. Maintenance Queue', icon: Wrench },
    { id: 'whatif', label: '6. What-If Simulator', icon: Sliders },
    { id: 'cannibalization', label: '7. Cannibalization Advisor', icon: GitCompare },
    { id: 'audit', label: '8. Audit Trail', icon: FileCheck2 },
  ];

  return (
    <aside className="w-64 bg-[#0e1422] border-r border-[#1e293b] flex flex-col justify-between select-none">
      <div>
        <div className="p-4 border-b border-[#1e293b] flex items-center space-x-3">
          <div className="p-2 bg-[#0284c7]/20 border border-[#0284c7] rounded-sm text-[#38bdf8]">
            <Radio className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-base font-bold tracking-wider text-slate-100">READYFLEET</h1>
            <p className="text-[10px] tracking-widest text-slate-400 font-mono">AV-OPS CONSOLE v1.0</p>
          </div>
        </div>

        <nav className="p-2 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-sm text-xs font-semibold tracking-wide transition-colors ${
                  isActive
                    ? 'bg-[#0284c7]/20 text-[#38bdf8] border-l-2 border-[#38bdf8]'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-[#162032]'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-[#38bdf8]' : 'text-slate-500'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      <div className="p-3 border-t border-[#1e293b] bg-[#090d16]/50 space-y-2 text-[11px] font-mono">
        <div className="flex items-center justify-between text-slate-400">
          <span className="flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            <span>SYSTEM</span>
          </span>
          <span className="text-emerald-400 font-bold">ONLINE</span>
        </div>
        <div className="flex items-center justify-between text-slate-400">
          <span>DATA MODE</span>
          <span className="text-amber-400 font-bold px-1.5 py-0.5 bg-amber-500/10 border border-amber-500/30 rounded-xs">
            SYNTHETIC
          </span>
        </div>
        <div className="pt-1 text-[10px] text-slate-500 text-center border-t border-[#1e293b]/50">
          SIH26249 — Air Power PS
        </div>
      </div>
    </aside>
  );
};
