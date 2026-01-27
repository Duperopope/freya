import { useState, useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { 
  Search, 
  Bell, 
  Cpu,
  HardDrive,
  Activity,
  X,
  MessageSquare,
  FileText,
  Settings,
  Shield,
  Zap,
  AlertCircle,
  CheckCircle2,
  Clock
} from 'lucide-react'
import { useAppStore } from '../../stores/appStore'
import { clsx } from 'clsx'

const pageTitles: Record<string, { title: string; subtitle: string }> = {
  '/chat': { title: 'AI Chat', subtitle: 'Interact with Freya AI Assistant' },
  '/bench': { title: 'Benchmark', subtitle: 'Test and optimize LLM performance' },
  '/bmad': { title: 'BMAD Studio', subtitle: 'Business Model - Architecture - Development' },
  '/files': { title: 'File Browser', subtitle: 'Manage project artifacts' },
  '/watch': { title: 'Cyber Watch', subtitle: 'Security vulnerability monitoring' },
  '/settings': { title: 'Settings', subtitle: 'Configuration and preferences' },
}

// Quick search items for command palette
const quickActions = [
  { id: 'chat', label: 'Go to Chat', icon: MessageSquare, path: '/chat', shortcut: 'C' },
  { id: 'bench', label: 'Go to Benchmark', icon: Zap, path: '/bench', shortcut: 'B' },
  { id: 'bmad', label: 'Go to BMAD Studio', icon: Settings, path: '/bmad', shortcut: 'M' },
  { id: 'files', label: 'Go to Files', icon: FileText, path: '/files', shortcut: 'F' },
  { id: 'watch', label: 'Go to Cyber Watch', icon: Shield, path: '/watch', shortcut: 'W' },
  { id: 'settings', label: 'Go to Settings', icon: Settings, path: '/settings', shortcut: 'S' },
]

interface Notification {
  id: string
  type: 'info' | 'success' | 'warning' | 'error'
  title: string
  message: string
  timestamp: Date
  read: boolean
}

export function Header() {
  const location = useLocation()
  const navigate = useNavigate()
  const { systemInfo, connected, wsConnected, benchProgress, bmadProgress } = useAppStore()
  
  const [showSearch, setShowSearch] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [showNotifications, setShowNotifications] = useState(false)
  const [notifications, setNotifications] = useState<Notification[]>([])
  
  const page = pageTitles[location.pathname] || { title: 'Freya', subtitle: '' }
  
  // Generate notifications from app state
  useEffect(() => {
    const newNotifications: Notification[] = []
    
    if (benchProgress?.running) {
      newNotifications.push({
        id: 'bench-running',
        type: 'info',
        title: 'Benchmark Running',
        message: `${benchProgress.program} - ${benchProgress.progress_percent}%`,
        timestamp: new Date(),
        read: false,
      })
    }
    
    if (bmadProgress?.running) {
      newNotifications.push({
        id: 'bmad-running',
        type: 'info',
        title: 'BMAD Pipeline Active',
        message: `Agent: ${bmadProgress.current_agent || 'Starting...'}`,
        timestamp: new Date(),
        read: false,
      })
    }
    
    if (!connected) {
      newNotifications.push({
        id: 'api-offline',
        type: 'error',
        title: 'API Offline',
        message: 'Cannot connect to Freya backend',
        timestamp: new Date(),
        read: false,
      })
    }
    
    setNotifications(newNotifications)
  }, [benchProgress, bmadProgress, connected])
  
  // Handle keyboard shortcut (Ctrl/Cmd + K)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault()
        setShowSearch(true)
      }
      if (e.key === 'Escape') {
        setShowSearch(false)
        setShowNotifications(false)
      }
    }
    
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])
  
  // Filter quick actions based on search
  const filteredActions = quickActions.filter(action =>
    action.label.toLowerCase().includes(searchQuery.toLowerCase())
  )
  
  // Handle action selection
  const handleSelectAction = (action: typeof quickActions[0]) => {
    navigate(action.path)
    setShowSearch(false)
    setSearchQuery('')
  }
  
  // Mark notification as read
  const markAsRead = (id: string) => {
    setNotifications(prev => prev.map(n => 
      n.id === id ? { ...n, read: true } : n
    ))
  }
  
  const unreadCount = notifications.filter(n => !n.read).length

  return (
    <>
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

          {/* Search - Now functional */}
          <button 
            onClick={() => setShowSearch(true)}
            className="p-2 rounded-lg hover:bg-freya-bg-tertiary transition-colors group flex items-center gap-2"
            title="Search (Ctrl+K)"
          >
            <Search className="w-5 h-5 text-freya-text-secondary group-hover:text-freya-text-primary" />
            <span className="text-xs text-freya-text-muted hidden lg:inline">Ctrl+K</span>
          </button>

          {/* Notifications - Now functional */}
          <button 
            onClick={() => setShowNotifications(!showNotifications)}
            className="p-2 rounded-lg hover:bg-freya-bg-tertiary transition-colors group relative"
            title="Notifications"
          >
            <Bell className="w-5 h-5 text-freya-text-secondary group-hover:text-freya-text-primary" />
            {/* Notification badge */}
            {unreadCount > 0 && (
              <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-freya-accent-red rounded-full text-white text-xs flex items-center justify-center">
                {unreadCount}
              </span>
            )}
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
      
      {/* Search Modal / Command Palette */}
      {showSearch && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-start justify-center pt-24">
          <div className="bg-freya-bg-secondary rounded-xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden border border-freya-border animate-fade-in">
            {/* Search input */}
            <div className="flex items-center gap-3 p-4 border-b border-freya-border">
              <Search className="w-5 h-5 text-freya-text-muted" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search or type a command..."
                className="flex-1 bg-transparent text-freya-text-primary placeholder-freya-text-muted focus:outline-none"
                autoFocus
              />
              <button
                onClick={() => setShowSearch(false)}
                className="p-1 rounded hover:bg-freya-bg-tertiary"
              >
                <X className="w-4 h-4 text-freya-text-muted" />
              </button>
            </div>
            
            {/* Results */}
            <div className="max-h-80 overflow-y-auto p-2">
              {filteredActions.length > 0 ? (
                <div className="space-y-1">
                  <div className="px-3 py-1 text-xs text-freya-text-muted font-medium">Quick Actions</div>
                  {filteredActions.map((action) => {
                    const Icon = action.icon
                    return (
                      <button
                        key={action.id}
                        onClick={() => handleSelectAction(action)}
                        className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-freya-bg-tertiary transition-colors"
                      >
                        <Icon className="w-5 h-5 text-freya-accent-blue" />
                        <span className="flex-1 text-left text-freya-text-primary">{action.label}</span>
                        <kbd className="px-2 py-0.5 text-xs bg-freya-bg-primary rounded text-freya-text-muted">
                          {action.shortcut}
                        </kbd>
                      </button>
                    )
                  })}
                </div>
              ) : (
                <div className="text-center py-8 text-freya-text-muted">
                  No results found for "{searchQuery}"
                </div>
              )}
            </div>
            
            {/* Footer */}
            <div className="px-4 py-2 border-t border-freya-border text-xs text-freya-text-muted flex items-center gap-4">
              <span>↑↓ to navigate</span>
              <span>↵ to select</span>
              <span>esc to close</span>
            </div>
          </div>
        </div>
      )}
      
      {/* Notifications Panel */}
      {showNotifications && (
        <div className="fixed right-6 top-20 w-80 bg-freya-bg-secondary rounded-lg shadow-xl border border-freya-border z-50 animate-fade-in">
          <div className="flex items-center justify-between p-4 border-b border-freya-border">
            <h3 className="font-medium text-freya-text-primary flex items-center gap-2">
              <Bell className="w-4 h-4" />
              Notifications
            </h3>
            {unreadCount > 0 && (
              <button
                onClick={() => setNotifications(prev => prev.map(n => ({ ...n, read: true })))}
                className="text-xs text-freya-accent-blue hover:underline"
              >
                Mark all read
              </button>
            )}
          </div>
          
          <div className="max-h-80 overflow-y-auto">
            {notifications.length > 0 ? (
              notifications.map((notification) => (
                <div
                  key={notification.id}
                  onClick={() => markAsRead(notification.id)}
                  className={clsx(
                    'p-3 border-b border-freya-border last:border-b-0 cursor-pointer hover:bg-freya-bg-tertiary transition-colors',
                    !notification.read && 'bg-freya-accent-blue/5'
                  )}
                >
                  <div className="flex items-start gap-3">
                    <div className={clsx(
                      'w-8 h-8 rounded-full flex items-center justify-center',
                      notification.type === 'info' && 'bg-freya-accent-blue/20',
                      notification.type === 'success' && 'bg-freya-accent-green/20',
                      notification.type === 'warning' && 'bg-freya-accent-yellow/20',
                      notification.type === 'error' && 'bg-freya-accent-red/20'
                    )}>
                      {notification.type === 'info' && <Clock className="w-4 h-4 text-freya-accent-blue" />}
                      {notification.type === 'success' && <CheckCircle2 className="w-4 h-4 text-freya-accent-green" />}
                      {notification.type === 'warning' && <AlertCircle className="w-4 h-4 text-freya-accent-yellow" />}
                      {notification.type === 'error' && <AlertCircle className="w-4 h-4 text-freya-accent-red" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-freya-text-primary text-sm">{notification.title}</span>
                        {!notification.read && (
                          <span className="w-2 h-2 rounded-full bg-freya-accent-blue" />
                        )}
                      </div>
                      <p className="text-xs text-freya-text-muted mt-0.5">{notification.message}</p>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-freya-text-muted">
                <Bell className="w-8 h-8 mx-auto mb-2 opacity-30" />
                <p className="text-sm">No notifications</p>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  )
}
