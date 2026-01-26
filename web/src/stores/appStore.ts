import { create } from 'zustand'

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

interface AppState {
  // Connection state
  connected: boolean
  ollamaConnected: boolean
  modelsCount: number
  
  // System info
  systemInfo: SystemInfo | null
  
  // Bench state
  benchProgress: BenchProgress | null
  
  // BMAD state
  bmadProgress: BMADProgress | null
  
  // WebSocket
  wsConnected: boolean
  
  // Actions
  setConnected: (connected: boolean) => void
  setOllamaConnected: (connected: boolean, count?: number) => void
  setSystemInfo: (info: SystemInfo) => void
  setBenchProgress: (progress: BenchProgress | null) => void
  setBMADProgress: (progress: BMADProgress | null | ((prev: BMADProgress | null) => BMADProgress | null)) => void
  setWsConnected: (connected: boolean) => void
}

export const useAppStore = create<AppState>((set) => ({
  connected: false,
  ollamaConnected: false,
  modelsCount: 0,
  systemInfo: null,
  benchProgress: null,
  bmadProgress: null,
  wsConnected: false,

  setConnected: (connected) => set({ connected }),
  
  setOllamaConnected: (connected, count = 0) => set({ 
    ollamaConnected: connected, 
    modelsCount: count 
  }),
  
  setSystemInfo: (info) => set({ systemInfo: info }),
  
  setBenchProgress: (progress) => set({ benchProgress: progress }),
  
  setBMADProgress: (progress) => set((state) => ({
    bmadProgress: typeof progress === 'function' ? progress(state.bmadProgress) : progress
  })),
  
  setWsConnected: (connected) => set({ wsConnected: connected }),
}))
