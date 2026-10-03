import React, { useState } from 'react';
import { GitCompare, ShieldAlert, CheckCircle2, XCircle } from 'lucide-react';

interface AdviceResult {
  approved: boolean;
  message: string;
  details: Record<string, any>;
}

export const CannibalizationAdvisor: React.FC = () => {
  const [donorTail, setDonorTail] = useState('SYN-04');
  const [recipientTail, setRecipientTail] = useState('SYN-01');
  const [compClass, setCompClass] = useState('engine');
  const [result, setResult] = useState<AdviceResult | null>(null);
  const [loading, setLoading] = useState(false);

  const evaluateProposal = () => {
    setLoading(true);
    fetch('/api/cannibalization/advice', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        donor_tail: donorTail,
        recipient_tail: recipientTail,
        comp_class: compClass
      })
    })
      .then(res => res.json())
      .then(data => {
        setResult(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error evaluating cannibalization:", err);
        setLoading(false);
      });
  };

  return (
    <div className="space-y-6 font-mono">
      <div className="border-b border-slate-800 pb-4">
        <h2 className="text-xl font-bold tracking-wide text-slate-100 uppercase">CANNIBALIZATION ADVISOR // AUTHORIZED PART TRANSFERS</h2>
        <p className="text-xs text-slate-400">Evaluate part transfers with strict operational guardrails and debt-repayment logging</p>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Input Panel */}
        <div className="bg-[#111726] border border-[#232e47] p-5 rounded-sm space-y-4">
          <h3 className="text-sm font-bold text-sky-400 uppercase flex items-center space-x-2">
            <GitCompare className="w-4 h-4 text-sky-400" />
            <span>Transfer Proposal Parameters</span>
          </h3>

          <div className="space-y-3 text-xs">
            <div>
              <label className="block text-slate-400 mb-1">Donor Tail ID (Must be NMC)</label>
              <input 
                type="text" 
                value={donorTail} 
                onChange={(e) => setDonorTail(e.target.value)}
                className="w-full bg-[#090d16] border border-[#232e47] text-slate-200 p-2 rounded focus:outline-none focus:border-sky-500 uppercase font-bold"
              />
            </div>

            <div>
              <label className="block text-slate-400 mb-1">Recipient Tail ID (Higher Priority)</label>
              <input 
                type="text" 
                value={recipientTail} 
                onChange={(e) => setRecipientTail(e.target.value)}
                className="w-full bg-[#090d16] border border-[#232e47] text-slate-200 p-2 rounded focus:outline-none focus:border-sky-500 uppercase font-bold"
              />
            </div>

            <div>
              <label className="block text-slate-400 mb-1">Target Component Class</label>
              <select 
                value={compClass} 
                onChange={(e) => setCompClass(e.target.value)}
                className="w-full bg-[#090d16] border border-[#232e47] text-slate-200 p-2 rounded focus:outline-none focus:border-sky-500"
              >
                <option value="engine">Engine Turbofan Module</option>
                <option value="avionics">Avionics Radar Unit</option>
                <option value="hydraulics">Hydraulic Actuator Pump</option>
                <option value="airframe">Airframe Structure</option>
              </select>
            </div>

            <button 
              onClick={evaluateProposal}
              disabled={loading}
              className="w-full mt-4 bg-sky-600 hover:bg-sky-500 text-slate-100 font-bold py-2.5 rounded transition-colors uppercase tracking-wider text-xs"
            >
              {loading ? 'EVALUATING GUARDRAILS...' : 'EVALUATE PROPOSAL'}
            </button>
          </div>
        </div>

        {/* Evaluation Output */}
        <div className="col-span-2 bg-[#111726] border border-[#232e47] p-5 rounded-sm flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-200 uppercase flex items-center space-x-2 mb-4">
              <ShieldAlert className="w-4 h-4 text-slate-400" />
              <span>Guardrail Evaluation & Decision Audit</span>
            </h3>

            {result ? (
              <div className="space-y-4">
                <div className={`p-4 border rounded flex items-center space-x-3 ${
                  result.approved ? 'bg-emerald-500/10 border-emerald-500/40 text-emerald-300' : 'bg-rose-500/10 border-rose-500/40 text-rose-300'
                }`}>
                  {result.approved ? <CheckCircle2 className="w-6 h-6 text-emerald-400 flex-shrink-0" /> : <XCircle className="w-6 h-6 text-rose-400 flex-shrink-0" />}
                  <div>
                    <div className="font-bold text-sm uppercase">{result.approved ? 'APPROVED WITH GUARDRAILS' : 'TRANSFER REFUSED BY GUARDRAILS'}</div>
                    <div className="text-xs text-slate-300 mt-0.5">{result.message}</div>
                  </div>
                </div>

                <div className="bg-slate-900 border border-slate-800 p-4 rounded text-xs space-y-2">
                  <div className="text-slate-400 font-bold uppercase">Hard Guardrail Check Suite:</div>
                  <div className="space-y-1 text-[11px]">
                    <div className="flex items-center space-x-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                      <span className="text-slate-300">Guardrail 1: Donor Priority strictly lower than Recipient Priority</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                      <span className="text-slate-300">Guardrail 2: Donor aircraft is already Non-Mission Capable (NMC)</span>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-slate-500 text-xs">
                Enter donor and recipient tail IDs on the left to evaluate operational cannibalization eligibility.
              </div>
            )}
          </div>

          <div className="pt-3 border-t border-slate-800 text-[10px] text-slate-500 flex justify-between">
            <span>DEBT LEDGER POSITION AUTOMATICALLY LOGGED</span>
            <span>GAO-01-693T DOCTRINAL CONTEXT</span>
          </div>
        </div>
      </div>
    </div>
  );
};
