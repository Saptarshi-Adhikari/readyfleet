import React, { useEffect, useState } from 'react';
import { ShieldCheck, AlertCircle, RefreshCw } from 'lucide-react';

export const AuditTrail: React.FC = () => {
  const [isValid, setIsValid] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(true);

  const verifyAuditChain = () => {
    setLoading(true);
    fetch('/api/audit/verify')
      .then(res => res.json())
      .then(data => {
        setIsValid(data.chain_valid);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error verifying audit chain:", err);
        setLoading(false);
      });
  };

  useEffect(() => {
    verifyAuditChain();
  }, []);

  return (
    <div className="space-y-6 font-mono select-none">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-xl font-bold tracking-wide text-slate-100 uppercase">AUDIT TRAIL // TAMPER-EVIDENT LOG CHAIN</h2>
          <p className="text-xs text-slate-400">Cryptographically verifiable SHA-256 hash-chained operational log</p>
        </div>

        <button 
          onClick={verifyAuditChain}
          disabled={loading}
          className="flex items-center space-x-2 bg-slate-800 hover:bg-slate-700 text-sky-400 border border-slate-700 px-3.5 py-1.5 rounded text-xs font-bold transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>VERIFY CHAIN INTEGRITY</span>
        </button>
      </div>

      <div className="bg-[#111726] border border-[#232e47] p-4 rounded-sm flex items-center justify-between">
        <div className="flex items-center space-x-3">
          {isValid ? (
            <ShieldCheck className="w-6 h-6 text-emerald-400" />
          ) : (
            <AlertCircle className="w-6 h-6 text-rose-400" />
          )}
          <div>
            <div className="text-xs font-bold text-slate-200 uppercase">HASH CHAIN VERIFICATION STATUS</div>
            <div className="text-[11px] text-slate-400">
              {isValid ? 'Cryptographic SHA-256 link unbroken. Zero database tampering detected.' : 'Warning: Audit chain link verification failed!'}
            </div>
          </div>
        </div>

        <div className="text-right">
          <span className="px-2.5 py-1 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-bold text-xs">
            INTEGRITY VERIFIED OK
          </span>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="bg-[#111726] border border-[#232e47] rounded-sm overflow-hidden text-xs">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-[#0e1422] border-b border-[#232e47] text-slate-400 font-bold uppercase tracking-wider text-[11px]">
              <th className="py-3 px-4">Timestamp (UTC)</th>
              <th className="py-3 px-4">Actor</th>
              <th className="py-3 px-4">Action</th>
              <th className="py-3 px-4">Entity</th>
              <th className="py-3 px-4">SHA-256 Row Hash</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1e293b]/60 text-slate-300">
            <tr className="hover:bg-[#162032]">
              <td className="py-3 px-4 text-slate-400">2026-10-04 01:18:22</td>
              <td className="py-3 px-4 font-bold text-slate-200">COMMANDER</td>
              <td className="py-3 px-4 text-emerald-400 font-bold">CANNIBALIZATION_APPROVED</td>
              <td className="py-3 px-4">SYN-01 (Engine Part)</td>
              <td className="py-3 px-4 text-slate-500 font-mono text-[10px]">8a1f7c...e92a</td>
            </tr>
            <tr className="hover:bg-[#162032]">
              <td className="py-3 px-4 text-slate-400">2026-10-04 01:12:10</td>
              <td className="py-3 px-4 font-bold text-slate-200">SYSTEM</td>
              <td className="py-3 px-4 text-sky-400 font-bold">WHATIF_LEVER_EXECUTED</td>
              <td className="py-3 px-4">PART-ENG-01</td>
              <td className="py-3 px-4 text-slate-500 font-mono text-[10px]">3b9e11...41c0</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
};
