import { useLocation } from 'react-router-dom'
import { 
  Search, 
  Bell, 
  Cpu,
  HardDrive,
  Activity
} from 'lucide-react'
import { useAppStore } from '../../stores/appStore'

const pageTitles: Record<string, { title: string; subtitle: string }> = {
  '/chat': { title: 'AI Chat', subtitle: 'Interact with Freya AI Assistant' },
  '/bench': { title: 'Benchmark', subtitle: 'Test and optimize LLM performance' },
  '/bmad': { title: 'BMAD Studio', subtitle: 'Business Model - Architecture - Development' },
  '/files': { title: 'File Browser', subtitle: 'Manage project artifacts' },
  '/watch': { title: 'Cyber Watch', subtitle: 'Security vulnerability monitoring' },
  '/settings': { title: 'Settings', subtitle: 'Configuration and preferences' },
}

export function Header() {
  const location = useLocation()
  const { systemInfo, connected, wsConnected } = useAppStore()
  
  const page = pageTitles[location.pathname] || { title: 'Freya', subtitle: '' }

  return (
    <header className="h-16 flex items-center justify-between px-6 bg-freya-bg-secondary border-b border-freya-border">
      {/* Page title */}
      <div>
        <h1 className="text-xl font-semibold text-freya-text-primary">{page.title}</h1>
        <p className="text-sm text-freya-text-muted">{page.subtitle}</p>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-4">
        {/* System metrics */}
        {systemInfo && (
          <div className="hidden md:flex items-center gap-4 text-sm text-freya-text-secondary">
            <div className="flex items-center gap-1.5" title="CPU Usage">
              <Cpu className="w-4 h-4" />
              <span>{systemInfo.cpu_percent.toFixed(0)}%</span>
            </div>
            <div className="flex items-center gap-1.5" title="RAM Usage">
              <Activity className="w-4 h-4" />
              <span>{systemInfo.ram_percent.toFixed(0)}%</span>
            </div>
            <div className="flex items-center gap-1.5" title="Disk Free">
              <HardDrive className="w-4 h-4" />
              <span>{systemInfo.disk_free_gb.toFixed(0)} GB</span>
            </div>
          </div>
        )}

        {/* Divider */}
        <div className="w-px h-8 bg-freya-border hidden md:block" />

        {/* Search */}
        <button className="p-2 rounded-lg hover:bg-freya-bg-tertiary transition-colors group">
          <Search className="w-5 h-5 text-freya-text-secondary group-hover:text-freya-text-primary" />
        </button>

        {/* Notifications */}
        <button className="p-2 rounded-lg hover:bg-freya-bg-tertiary transition-colors group relative">
          <Bell className="w-5 h-5 text-freya-text-secondary group-hover:text-freya-text-primary" />
          {/* Notification dot */}
          {/* <span className="absolute top-1 right-1 w-2 h-2 bg-freya-accent-red rounded-full" /> */}
        </button>

        {/* Connection status */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-freya-bg-tertiary">
          <span 
            className={`w-2 h-2 rounded-full ${
              connected && wsConnected 
                ? 'bg-freya-accent-green animate-pulse' 
                : connected 
                  ? 'bg-freya-accent-yellow' 
                  : 'bg-freya-accent-red'
            }`}
          />
          <span className="text-sm text-freya-text-secondary">
            {connected && wsConnected ? 'Live' : connected ? 'API' : 'Offline'}
          </span>
        </div>
      </div>
    </header>
  )
}
