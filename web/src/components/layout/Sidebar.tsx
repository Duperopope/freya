import { NavLink } from 'react-router-dom'
import { 
  MessageSquare, 
  BarChart3, 
  Workflow, 
  Settings, 
  FolderOpen, 
  Shield,
  ChevronLeft,
  ChevronRight,
  Zap,
  Rocket
} from 'lucide-react'
import { clsx } from 'clsx'
import { useAppStore } from '../../stores/appStore'

interface SidebarProps {
  collapsed: boolean
  onToggle: () => void
}

const navItems = [
  { path: '/chat', icon: MessageSquare, label: 'Chat', description: 'AI Assistant' },
  { path: '/bench', icon: BarChart3, label: 'Benchmark', description: 'Model Testing' },
  { path: '/bmad', icon: Workflow, label: 'BMAD Studio', description: 'Workflow' },
  { path: '/files', icon: FolderOpen, label: 'Files', description: 'File Browser' },
  { path: '/watch', icon: Shield, label: 'Cyber Watch', description: 'Security Feed' },
  { path: '/launcher', icon: Rocket, label: 'Launcher', description: 'Update & Launch' },
  { path: '/settings', icon: Settings, label: 'Settings', description: 'Configuration' },
]

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const { connected, benchProgress, bmadProgress } = useAppStore()

  return (
    <aside
      className={clsx(
        'flex flex-col bg-freya-bg-secondary border-r border-freya-border transition-all duration-300',
        collapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Logo */}
      <div className="flex items-center h-16 px-4 border-b border-freya-border">
        <div className="flex items-center gap-3">
          <div className="relative">
            <Zap className="w-8 h-8 text-freya-accent-blue" />
            {connected && (
              <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 bg-freya-accent-green rounded-full border-2 border-freya-bg-secondary" />
            )}
          </div>
          {!collapsed && (
            <div className="animate-fade-in">
              <h1 className="text-lg font-bold text-freya-text-primary">Freya</h1>
              <p className="text-xs text-freya-text-muted">BMAD Orchestrator</p>
            </div>
          )}
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 overflow-y-auto">
        <ul className="space-y-1 px-2">
          {navItems.map((item) => (
            <li key={item.path}>
              <NavLink
                to={item.path}
                className={({ isActive }) =>
                  clsx(
                    'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200',
                    'hover:bg-freya-bg-tertiary group relative',
                    isActive
                      ? 'bg-freya-bg-tertiary text-freya-accent-blue'
                      : 'text-freya-text-secondary hover:text-freya-text-primary'
                  )
                }
              >
                <item.icon className={clsx('w-5 h-5 flex-shrink-0', collapsed && 'mx-auto')} />
                
                {!collapsed && (
                  <div className="flex-1 min-w-0 animate-fade-in">
                    <div className="flex items-center justify-between">
                      <span className="font-medium">{item.label}</span>
                      {/* Activity indicators */}
                      {item.path === '/bench' && benchProgress?.running && (
                        <span className="w-2 h-2 bg-freya-accent-blue rounded-full animate-pulse" />
                      )}
                      {item.path === '/bmad' && bmadProgress?.running && (
                        <span className="w-2 h-2 bg-freya-accent-purple rounded-full animate-pulse" />
                      )}
                    </div>
                    <span className="text-xs text-freya-text-muted">{item.description}</span>
                  </div>
                )}

                {/* Tooltip for collapsed state */}
                {collapsed && (
                  <div className="absolute left-full ml-2 px-2 py-1 bg-freya-bg-elevated rounded-md shadow-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 whitespace-nowrap">
                    <span className="text-sm font-medium text-freya-text-primary">{item.label}</span>
                  </div>
                )}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* Status indicators */}
      {!collapsed && (
        <div className="px-4 py-3 border-t border-freya-border animate-fade-in">
          <div className="space-y-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-freya-text-muted">Ollama</span>
              <span className={clsx(
                'flex items-center gap-1.5',
                connected ? 'text-freya-accent-green' : 'text-freya-accent-red'
              )}>
                <span className={clsx(
                  'w-1.5 h-1.5 rounded-full',
                  connected ? 'bg-freya-accent-green' : 'bg-freya-accent-red'
                )} />
                {connected ? 'Connected' : 'Offline'}
              </span>
            </div>
            {benchProgress?.running && (
              <div className="flex items-center justify-between text-freya-accent-blue">
                <span>Benchmark</span>
                <span>{Math.round(benchProgress.progress_percent)}%</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Collapse toggle */}
      <button
        onClick={onToggle}
        className="flex items-center justify-center h-12 border-t border-freya-border hover:bg-freya-bg-tertiary transition-colors"
      >
        {collapsed ? (
          <ChevronRight className="w-5 h-5 text-freya-text-secondary" />
        ) : (
          <ChevronLeft className="w-5 h-5 text-freya-text-secondary" />
        )}
      </button>
    </aside>
  )
}
