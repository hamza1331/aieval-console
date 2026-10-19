import { useEffect, useState } from 'react';
import { Navbar, type NavigationTab } from './components/Navbar';
import { OverviewPage } from './pages/OverviewPage';
import { ContractsPage } from './pages/ContractsPage';
import { ContractDetailPage } from './pages/ContractDetailPage';
import { WorkbenchPage } from './pages/WorkbenchPage';
import { RunHistoryPage } from './pages/RunHistoryPage';

export function App() {
  const getInitialState = () => {
    const hash = window.location.hash.replace('#', '');
    if (hash.startsWith('runs/')) {
      return { tab: 'runs' as NavigationTab, contractId: null, runId: hash.split('/')[1] };
    }
    if (hash.startsWith('contracts/')) {
      return { tab: 'contracts' as NavigationTab, contractId: hash.split('/')[1], runId: null };
    }
    if (['overview', 'contracts', 'workbench', 'runs'].includes(hash)) {
      return { tab: hash as NavigationTab, contractId: null, runId: null };
    }
    return { tab: 'overview' as NavigationTab, contractId: null, runId: null };
  };

  const initial = getInitialState();
  const [currentTab, setCurrentTab] = useState<NavigationTab>(initial.tab);
  const [selectedContractId, setSelectedContractId] = useState<string | null>(initial.contractId);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(initial.runId);

  // Workbench preselected target
  const [workbenchContractId, setWorkbenchContractId] = useState<string | null>(null);
  const [workbenchVersionId, setWorkbenchVersionId] = useState<string | null>(null);

  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace('#', '');
      if (hash.startsWith('runs/')) {
        setSelectedRunId(hash.split('/')[1]);
        setCurrentTab('runs');
      } else if (hash.startsWith('contracts/')) {
        setSelectedContractId(hash.split('/')[1]);
        setCurrentTab('contracts');
      } else if (['overview', 'contracts', 'workbench', 'runs'].includes(hash)) {
        setCurrentTab(hash as NavigationTab);
      }
    };
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const handleTabChange = (tab: NavigationTab) => {
    setCurrentTab(tab);
    window.location.hash = tab;
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

