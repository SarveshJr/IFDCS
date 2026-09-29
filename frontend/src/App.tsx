import { Sidebar } from './components/Sidebar';
import { AlertsPanel } from './components/AlertsPanel';
import { MapView } from './components/Map';
import { FacilityModal } from './components/FacilityModal';
import { useStore } from './store/useStore';

function App() {
  const selectedAlert = useStore((state: any) => state.selectedAlert);

  return (
    <div className="flex h-screen w-full bg-[#121212] text-gray-100 overflow-hidden font-sans">
      <Sidebar />
      
      <main className="flex-1 relative flex flex-col">
        <header className="h-14 bg-[#1a1a1a] border-b border-gray-800 flex items-center px-6 shrink-0 z-20 shadow-md">
          <h1 className="text-lg font-semibold tracking-wide text-gray-200">
            IFDCS <span className="text-gray-500 font-normal ml-2">| Industrial Fire Detection & Classification System</span>
          </h1>
        </header>
        
        <div className="flex-1 relative">
          <MapView />
        </div>
      </main>

      <AlertsPanel />
      
      {selectedAlert && <FacilityModal />}
    </div>
  );
}

export default App;
