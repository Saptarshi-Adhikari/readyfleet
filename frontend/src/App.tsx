import { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { TopBar } from './components/TopBar';
import { CommandCenter } from './components/CommandCenter';
import { FleetBoard } from './components/FleetBoard';
import { AircraftDetail } from './components/AircraftDetail';
import { ReadinessForecast } from './components/ReadinessForecast';
import { MaintenanceControl } from './components/MaintenanceControl';
import { WhatIfSimulator } from './components/WhatIfSimulator';
import { CannibalizationAdvisor } from './components/CannibalizationAdvisor';
import { DataSourcesWorkspace } from './components/DataSourcesWorkspace';
import { AuditTrail } from './components/AuditTrail';

export function App() {
  const [activeTab, setActiveTab] = useState('command');
  const [selectedTail, setSelectedTail] = useState<string | null>(null);

  const handleSelectTail = (tailNo: string) => {
    setSelectedTail(tailNo);
    setActiveTab('aircraft');
  };

  const handleBackToFleet = () => {
    setActiveTab('fleet');
  };

  return (
    <div className="flex h-screen bg-[#090d16] text-slate-200 overflow-hidden font-sans">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      <div className="flex-1 flex flex-col min-w-0">
        <TopBar />

        <main className="flex-1 overflow-y-auto p-6 bg-[#090d16]">
          {activeTab === 'command' && <CommandCenter onSelectTail={handleSelectTail} />}
          {activeTab === 'fleet' && <FleetBoard onSelectTail={handleSelectTail} />}
          {activeTab === 'aircraft' && (
            selectedTail ? (
              <AircraftDetail tailNo={selectedTail} onBack={handleBackToFleet} />
            ) : (
              <FleetBoard onSelectTail={handleSelectTail} />
            )
          )}
          {activeTab === 'readiness' && <ReadinessForecast />}
          {activeTab === 'maintenance' && <MaintenanceControl />}
          {activeTab === 'whatif' && <WhatIfSimulator />}
          {activeTab === 'cannibalization' && <CannibalizationAdvisor />}
          {activeTab === 'datasources' && <DataSourcesWorkspace />}
          {activeTab === 'audit' && <AuditTrail />}
        </main>
      </div>
    </div>
  );
}

export default App;
