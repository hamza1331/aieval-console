import { useState } from 'react';
import { Navbar, type NavigationTab } from './components/Navbar';
import { OverviewPage } from './pages/OverviewPage';
import { ContractsPage } from './pages/ContractsPage';
import { ContractDetailPage } from './pages/ContractDetailPage';
import { WorkbenchPage } from './pages/WorkbenchPage';
import { RunHistoryPage } from './pages/RunHistoryPage';

export function App() {
  const [currentTab, setCurrentTab] = useState<NavigationTab>('overview');
  const [selectedContractId, setSelectedContractId] = useState<string | null>(null);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);

  // Workbench preselected target
  const [workbenchContractId, setWorkbenchContractId] = useState<string | null>(null);
  const [workbenchVersionId, setWorkbenchVersionId] = useState<string | null>(null);

  const handleTabChange = (tab: NavigationTab) => {
    setCurrentTab(tab);
    if (tab !== 'contracts') {
      setSelectedContractId(null);
    }
    if (tab !== 'runs') {
      setSelectedRunId(null);
    }
  };

  const handleOverviewNavigate = (
    tab: 'overview' | 'contracts' | 'workbench' | 'runs',
    targetId?: string
  ) => {
    setCurrentTab(tab);
    if (tab === 'runs' && targetId) {
      setSelectedRunId(targetId);
    } else if (tab === 'contracts' && targetId) {
      setSelectedContractId(targetId);
    }
  };

  const handleNavigateToWorkbench = (contractId: string, versionId?: string) => {
    setWorkbenchContractId(contractId);
    setWorkbenchVersionId(versionId || null);
    setCurrentTab('workbench');
  };

  const handleNavigateToRun = (runId: string) => {
    setSelectedRunId(runId);
    setCurrentTab('runs');
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <Navbar
        currentTab={currentTab}
        onTabChange={handleTabChange}
        selectedContractId={selectedContractId}
        selectedRunId={selectedRunId}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {currentTab === 'overview' && (
          <OverviewPage onNavigate={handleOverviewNavigate} />
        )}

        {currentTab === 'contracts' && (
          <>
            {selectedContractId ? (
              <ContractDetailPage
                contractId={selectedContractId}
                onBack={() => setSelectedContractId(null)}
                onNavigateToWorkbench={handleNavigateToWorkbench}
              />
            ) : (
              <ContractsPage
                onSelectContract={(id) => setSelectedContractId(id)}
                onNavigateToWorkbench={(id) => handleNavigateToWorkbench(id)}
              />
            )}
          </>
        )}

        {currentTab === 'workbench' && (
          <WorkbenchPage
            key={`${workbenchContractId}-${workbenchVersionId}`}
            initialContractId={workbenchContractId}
            initialVersionId={workbenchVersionId}
            onNavigateToRun={handleNavigateToRun}
          />
        )}

        {currentTab === 'runs' && (
          <RunHistoryPage
            initialRunId={selectedRunId}
            onRunSelected={(id) => setSelectedRunId(id)}
          />
        )}
      </main>

      <footer className="border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-500">
        <p>
          aieval-console &bull; Declarative Validation Engine &bull; Zero Code Execution Sandbox
        </p>
      </footer>
    </div>
  );
}

export default App;

