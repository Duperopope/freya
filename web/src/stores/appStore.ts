import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface SystemInfo {
  cpu_percent: number
  ram_percent: number
  disk_free_gb: number
  disk_total_gb: number
}

interface BenchProgress {
  running: boolean
  program: string
  phase: string
  role: string
  model: string
  progress_percent: number
}

interface BMADProgress {
  running: boolean
  current_agent: string | null
  agents_completed: string[]
  artifacts_generated: string[]
}

// Persisted bench results
interface BenchHistoryCache {
  'bench-fast': unknown[]
  'bench-standard': unknown[]
  'bench-advanced': unknown[]
  billboard: unknown[]
  lastUpdated: string
}

// Research mode state
interface ResearchState {
  isActive: boolean
  phase: 'idle' | 'searching' | 'analyzing' | 'briefing' | 'bmad_ready' | 'bmad'
  searchResults: unknown[]
  analysisReport: string | null
  selectedIdea: string | null
  // Auto-start BMAD pipeline
  autoStartBMAD: boolean
  bmadGoal: string | null
  bmadProjectName: string | null
}

interface AppState {
  // Connection state
  connected: boolean
  ollamaConnected: boolean
  modelsCount: number
  
  // System info
  systemInfo: SystemInfo | null
  
  // Bench state
  benchProgress: BenchProgress | null
  benchHistoryCache: BenchHistoryCache
  
  // BMAD state
  bmadProgress: BMADProgress | null
  
  // Research mode state
  researchState: ResearchState
  
  // WebSocket
  wsConnected: boolean
  
  // UI State persistence
  lastActiveTab: string
  sidebarCollapsed: boolean
  
  // Actions
  setConnected: (connected: boolean) => void
  setOllamaConnected: (connected: boolean, count?: number) => void
  setSystemInfo: (info: SystemInfo) => void
  setBenchProgress: (progress: BenchProgress | null) => void
  setBenchHistoryCache: (cache: Partial<BenchHistoryCache>) => void
  setBMADProgress: (progress: BMADProgress | null | ((prev: BMADProgress | null) => BMADProgress | null)) => void
  setResearchState: (state: Partial<ResearchState>) => void
  setWsConnected: (connected: boolean) => void
  setLastActiveTab: (tab: string) => void
  setSidebarCollapsed: (collapsed: boolean) => void
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      connected: false,
      ollamaConnected: false,
      modelsCount: 0,
      systemInfo: null,
      benchProgress: null,
      benchHistoryCache: {
        'bench-fast': [],
        'bench-standard': [],
        'bench-advanced': [],
        billboard: [],
        lastUpdated: '',
      },
      bmadProgress: null,
      researchState: {
        isActive: false,
        phase: 'idle',
        searchResults: [],
        analysisReport: null,
        selectedIdea: null,
        autoStartBMAD: false,
        bmadGoal: null,
        bmadProjectName: null,
      },
      wsConnected: false,
      lastActiveTab: 'chat',
      sidebarCollapsed: false,

      setConnected: (connected) => set({ connected }),
      
      setOllamaConnected: (connected, count = 0) => set({ 
        ollamaConnected: connected, 
        modelsCount: count 
      }),
      
      setSystemInfo: (info) => set({ systemInfo: info }),
      
      setBenchProgress: (progress) => set({ benchProgress: progress }),
      
      setBenchHistoryCache: (cache) => set((state) => ({
        benchHistoryCache: { 
          ...state.benchHistoryCache, 
          ...cache,
          lastUpdated: new Date().toISOString()
        }
      })),
      
      setBMADProgress: (progress) => set((state) => ({
        bmadProgress: typeof progress === 'function' ? progress(state.bmadProgress) : progress
      })),
      
      setResearchState: (researchUpdate) => set((state) => ({
        researchState: { ...state.researchState, ...researchUpdate }
      })),
      
      setWsConnected: (connected) => set({ wsConnected: connected }),
      
      setLastActiveTab: (tab) => set({ lastActiveTab: tab }),
      
      setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
    }),
    {
      name: 'freya-app-store',
      partialize: (state) => ({
        // Only persist non-transient data
        benchHistoryCache: state.benchHistoryCache,
        lastActiveTab: state.lastActiveTab,
        sidebarCollapsed: state.sidebarCollapsed,
        researchState: state.researchState,
      }),
    }
  )
)
