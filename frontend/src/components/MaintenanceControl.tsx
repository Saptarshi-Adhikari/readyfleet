import React, { useEffect, useState } from 'react';
import { Wrench, Package, Users } from 'lucide-react';

interface QueueItem {
  tail_no: string;
  status: string;
  issue: string;
  priority: string;
  required_action: string;
  est_duration: string;
}

interface SpareItem {
  part_no: string;
  comp_class: string;
  qty_on_hand: number;
  qty_due_in: number;
  lead_time_h: number;
  expedited_lead_time_h: number;
}

interface CrewItem {
  id: number;
  name: string;
  trade: string;
  shift: string;
  available_h_per_day: number;
}

export const MaintenanceControl: React.FC = () => {
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [spares, setSpares] = useState<SpareItem[]>([]);
  const [crew, setCrew] = useState<CrewItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/maintenance/overview')
      .then(res => res.json())
      .then(data => {
        setQueue(data.queue || []);
        setSpares(data.spares || []);
        setCrew(data.crew || []);
        setLoading(false);
      })
      .catch(err => console.error("Error loading maintenance overview:", err));
  }, []);

  if (loading) {
    return (
      <div className="p-8 text-center font-mono text-slate-400">
        <div className="inline-block animate-spin w-6 h-6 border-2 border-sky-400 border-t-transparent rounded-full mb-3"></div>
        <div>LOADING MAINTENANCE WORKLOAD & RESOURCE CONSTRAINTS...</div>
      </div>
    );
  }

  // Calculate Trade-Wise Crew Capacity
  const tradeCapacity: Record<string, { day: number; night: number }> = {};
  crew.forEach(c => {
    if (!tradeCapacity[c.trade]) tradeCapacity[c.trade] = { day: 0, night: 0 };
    if (c.shift === 'day') tradeCapacity[c.trade].day += 1;
    if (c.shift === 'night') tradeCapacity[c.trade].night += 1;
  });

  return (
    <div className="space-y-6 font-mono select-none">
      {/* Header */}
      <div className="border-b border-slate-800 pb-4">
        <h2 className="text-xl font-bold tracking-wide text-slate-100 uppercase">MAINTENANCE CONTROL // WORKLOAD & RESOURCE CONSTRAINTS</h2>
        <p className="text-xs text-slate-400">Monitor maintenance queue backlog, technician trade capacity, and rotables spare inventory</p>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Maintenance Queue */}
        <div className="col-span-2 bg-[#111726] border border-[#232e47] p-5 rounded-sm">
          <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider mb-4 flex items-center space-x-2">
            <Wrench className="w-4 h-4 text-sky-400" />
            <span>Aircraft Maintenance Workload Queue ({queue.length})</span>
          </h3>

          <div className="space-y-3 text-xs">
            {queue.map((item, idx) => (
              <div key={idx} className="bg-slate-900 border border-slate-800 p-3.5 rounded-xs flex items-center justify-between">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-slate-100">{item.tail_no}</span>
                    <span className={`text-[10px] font-bold px-1.5 py-0.2 rounded ${
                      item.status === 'NMC' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40' : 'bg-amber-500/20 text-amber-400'
                    }`}>
                      {item.status} ({item.priority})
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1">{item.issue}</div>
                </div>

                <div className="text-right">
                  <div className="text-sky-400 font-bold">{item.required_action}</div>
                  <div className="text-[10px] text-slate-500 mt-0.5">EST: {item.est_duration}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Technician Trade Capacity */}
        <div className="bg-[#111726] border border-[#232e47] p-5 rounded-sm flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider mb-4 flex items-center space-x-2">
              <Users className="w-4 h-4 text-amber-400" />
              <span>Technician Capacity by Trade</span>
            </h3>

            <div className="space-y-3 text-xs">
              {['engine', 'avionics', 'hydraulics', 'airframe'].map((trade) => {
                const cap = tradeCapacity[trade] || { day: 1, night: 1 };
                return (
                  <div key={trade} className="bg-slate-900 border border-slate-800 p-3 rounded-xs">
                    <div className="font-bold text-slate-200 uppercase text-xs mb-2">{trade} Trade</div>
                    <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-400">
                      <div>DAY SHIFT: <strong className="text-emerald-400">{cap.day} AVAILABLE</strong></div>
                      <div>NIGHT SHIFT: <strong className="text-emerald-400">{cap.night} AVAILABLE</strong></div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="pt-3 border-t border-slate-800 text-[10px] text-slate-500">
            GREEDY 1-DAY CAPACITY ALLOCATION SCHEDULER
          </div>
        </div>
      </div>

      {/* Spares Inventory & Lead Times */}
      <div className="bg-[#111726] border border-[#232e47] p-5 rounded-sm">
        <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider mb-4 flex items-center space-x-2">
          <Package className="w-4 h-4 text-emerald-400" />
          <span>Rotables Spares Inventory & Lead Times</span>
        </h3>

        <div className="bg-[#0e1422] border border-[#232e47] rounded-sm overflow-hidden text-xs">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-[#111726] border-b border-[#232e47] text-slate-400 font-bold uppercase text-[11px]">
                <th className="py-2.5 px-4">Part Number</th>
                <th className="py-2.5 px-4">Component Class</th>
                <th className="py-2.5 px-4">Qty On-Hand</th>
                <th className="py-2.5 px-4">Qty Due-In</th>
                <th className="py-2.5 px-4">Standard Lead Time</th>
                <th className="py-2.5 px-4">Expedited Lead Time</th>
                <th className="py-2.5 px-4 text-right">Shortage Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1e293b]/60 text-slate-300">
              {spares.map((spare) => {
                const isShortage = spare.qty_on_hand === 0;
                return (
                  <tr key={spare.part_no} className="hover:bg-[#162032]">
                    <td className="py-3 px-4 font-bold text-slate-100">{spare.part_no}</td>
                    <td className="py-3 px-4 uppercase">{spare.comp_class}</td>
                    <td className={`py-3 px-4 font-bold ${isShortage ? 'text-rose-400' : 'text-emerald-400'}`}>
                      {spare.qty_on_hand} UNITS
                    </td>
                    <td className="py-3 px-4">{spare.qty_due_in} UNITS</td>
                    <td className="py-3 px-4">{spare.lead_time_h}h</td>
                    <td className="py-3 px-4 text-sky-400">{spare.expedited_lead_time_h}h</td>
                    <td className="py-3 px-4 text-right">
                      {isShortage ? (
                        <span className="px-2 py-0.5 rounded bg-rose-500/20 border border-rose-500/40 text-rose-400 font-bold text-[10px]">
                          SHORTAGE GROUNDING
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-bold text-[10px]">
                          STOCK READY
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
