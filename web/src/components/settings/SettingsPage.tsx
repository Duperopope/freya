/**
 * SettingsPage - Configuration & Preferences
 * 
 * Comprehensive settings interface for managing Freya configuration,
 * model routing, prompts, API integrations, and system preferences.
 */

import { useState, useEffect } from 'react'
import {
  Settings,
  Folder,
  Server,
  Brain,
  FileCode,
  Palette,
  Save,
  RefreshCw,
  ChevronRight,
  Check,
  Copy,
  ExternalLink,
  Info,
  Database,
  Cpu,
  HardDrive,
  Network,
  Key,
  Github,
  GitBranch,
  Edit3,
  FolderOpen,
  Moon,
  Sun,
  Monitor,
  Cloud,
  AlertCircle,
  CheckCircle2,
  TrendingUp
} from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { clsx } from 'clsx'
import * as api from '../../lib/api'

type SettingsTab = 'paths' | 'ollama' | 'routing' | 'providers' | 'prompts' | 'api' | 'appearance' | 'about'

interface TabDef {
  id: SettingsTab
  name: string
  icon: typeof Settings
  description: string
}

const TABS: TabDef[] = [
  { id: 'paths', name: 'Paths', icon: Folder, description: 'Configure directory paths' },
  { id: 'ollama', name: 'Ollama', icon: Server, description: 'LLM server connection' },
  { id: 'routing', name: 'Model Routing', icon: Brain, description: 'Per-role model assignment' },
  { id: 'providers', name: 'Providers', icon: Cloud, description: 'Hybrid routing & quotas' },
  { id: 'prompts', name: 'Prompts', icon: FileCode, description: 'System prompts management' },
  { id: 'api', name: 'API Keys', icon: Key, description: 'External API integrations' },
  { id: 'appearance', name: 'Appearance', icon: Palette, description: 'UI preferences' },
  { id: 'about', name: 'About', icon: Info, description: 'Version and system info' }
]

// Theme definitions
const THEMES = [
  { id: 'dark', name: 'Dark', icon: Moon, colors: { from: '#0a0e14', to: '#151b23' } },
  { id: 'light', name: 'Light', icon: Sun, colors: { from: '#ffffff', to: '#f3f4f6' } },
  { id: 'midnight', name: 'Midnight', icon: Monitor, colors: { from: '#1e1b4b', to: '#312e81' } },
  { id: 'forest', name: 'Forest', icon: Monitor, colors: { from: '#064e3b', to: '#065f46' } },
  { id: 'ocean', name: 'Ocean', icon: Monitor, colors: { from: '#0c4a6e', to: '#075985' } },
]

// Font options
const FONTS = [
  { id: 'inter', name: 'Inter', family: 'Inter, system-ui, sans-serif' },
  { id: 'jetbrains', name: 'JetBrains Mono', family: '"JetBrains Mono", monospace' },
  { id: 'fira', name: 'Fira Code', family: '"Fira Code", monospace' },
  { id: 'source', name: 'Source Sans', family: '"Source Sans Pro", sans-serif' },
]

export function SettingsPage() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<SettingsTab>('paths')
  const [copiedPath, setCopiedPath] = useState<string | null>(null)
  const [selectedPrompt, setSelectedPrompt] = useState<string | null>(null)
  const [promptContent, setPromptContent] = useState('')
  
  // Editable paths state
  const [editingPath, setEditingPath] = useState<string | null>(null)
  const [editedPaths, setEditedPaths] = useState<Record<string, string>>({})
  
  // API keys state
  const [apiKeys, setApiKeys] = useState({
    github_token: '',
    gitlab_token: '',
    gitlab_url: '',
    brave_api_key: '',
    nvd_api_key: '',
    searxng_url: '',
  })
  const [showApiKeys, setShowApiKeys] = useState<Record<string, boolean>>({})
  
  // Appearance state
  const [selectedTheme, setSelectedTheme] = useState('dark')
  const [selectedFont, setSelectedFont] = useState('inter')
  const [fontSize, setFontSize] = useState(14)

  // Fetch paths
  const { data: paths } = useQuery({
    queryKey: ['paths'],
    queryFn: api.getPaths,
  })

  // Fetch routing
  const { data: routing } = useQuery({
    queryKey: ['routing'],
    queryFn: api.getRouting,
  })

  // Fetch models
  const { data: models } = useQuery({
    queryKey: ['models'],
    queryFn: api.getModels,
  })

  // Fetch prompts
  const { data: prompts } = useQuery({
    queryKey: ['prompts'],
    queryFn: api.getPrompts,
  })

  // Fetch version
  const { data: version } = useQuery({
    queryKey: ['version'],
    queryFn: api.getVersion,
  })

  // Fetch health for system info
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: api.getHealth,
  })

  // Fetch system info
  const { data: systemInfo } = useQuery({
    queryKey: ['systemInfo'],
    queryFn: api.getSystemInfo,
  })
  
  // Fetch hybrid routing config (v2.2)
  const { data: hybridConfig } = useQuery({
    queryKey: ['hybridRouting'],
    queryFn: api.getHybridRoutingConfig,
  })
  
  // Fetch providers (v2.2)
  const { data: providers, refetch: refetchProviders } = useQuery({
    queryKey: ['providers'],
    queryFn: api.getProviders,
  })
  
  // Fetch usage stats (v2.2)
  const { data: usageStats, refetch: refetchUsageStats } = useQuery({
    queryKey: ['usageStats'],
    queryFn: api.getUsageStats,
  })
  
  // Fetch local runtimes (v2.2)
  const { data: localRuntimes, refetch: refetchLocalRuntimes } = useQuery({
    queryKey: ['localRuntimes'],
    queryFn: api.getLocalRuntimes,
  })
  
  // Provider key state
  const [providerKeys, setProviderKeys] = useState<Record<string, string>>({})
  const [showProviderKey, setShowProviderKey] = useState<Record<string, boolean>>({})
  
  // Update provider key mutation
  const updateProviderKeyMutation = useMutation({
    mutationFn: ({ provider, apiKey }: { provider: string; apiKey: string }) => 
      api.updateProviderKey(provider, apiKey),
    onSuccess: () => {
      refetchProviders()
    },
  })
  
  // Detect runtimes mutation
  const detectRuntimesMutation = useMutation({
    mutationFn: api.detectLocalRuntimes,
    onSuccess: () => {
      refetchLocalRuntimes()
    },
  })

  // Initialize edited paths when paths data loads
  useEffect(() => {
    if (paths && Object.keys(editedPaths).length === 0) {
      setEditedPaths(paths as unknown as Record<string, string>)
    }
  }, [paths, editedPaths])

  // Apply font in real-time
  useEffect(() => {
    const font = FONTS.find(f => f.id === selectedFont)
    if (font) {
      document.documentElement.style.fontFamily = font.family
    }
  }, [selectedFont])

  // Apply font size in real-time
  useEffect(() => {
    document.documentElement.style.fontSize = `${fontSize}px`
  }, [fontSize])

  // Copy to clipboard
  const copyToClipboard = async (text: string, key: string) => {
    await navigator.clipboard.writeText(text)
    setCopiedPath(key)
    setTimeout(() => setCopiedPath(null), 2000)
  }

  // Load prompt content
  const loadPrompt = async (name: string) => {
    try {
      const data = await api.getPrompt(name)
      setSelectedPrompt(name)
      setPromptContent(data.content)
    } catch {
      setPromptContent('Error loading prompt')
    }
  }

  // Save prompt mutation
  const savePromptMutation = useMutation({
    mutationFn: () => api.savePrompt(selectedPrompt!, promptContent),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompts'] })
    },
  })

  // Save routing mutation
  const saveRoutingMutation = useMutation({
    mutationFn: (configs: api.RoutingConfig[]) => api.setRouting(configs),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['routing'] })
    },
  })

  // Save path handler (would need backend endpoint)
  const savePath = async (key: string, value: string) => {
    // TODO: Implement backend endpoint for updating paths
    setEditedPaths(prev => ({ ...prev, [key]: value }))
    setEditingPath(null)
    // Show success feedback
    setCopiedPath(key)
    setTimeout(() => setCopiedPath(null), 2000)
  }

  // Save API keys handler
  const saveApiKeys = async () => {
    // TODO: Implement backend endpoint for saving API keys
    // For now, store in localStorage
    localStorage.setItem('freya_api_keys', JSON.stringify(apiKeys))
    alert('API keys saved locally')
  }

  // Load API keys from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('freya_api_keys')
    if (saved) {
      try {
        setApiKeys(JSON.parse(saved))
      } catch {
        // Ignore parsing errors
      }
    }
  }, [])

  return (
    <div className="h-full flex overflow-hidden">
      {/* Sidebar */}
      <div className="w-64 border-r border-freya-border bg-freya-bg-secondary p-4">
        <h2 className="text-lg font-semibold text-freya-text-primary mb-4 flex items-center gap-2">
          <Settings className="w-5 h-5" />
          Settings
        </h2>

        <nav className="space-y-1">
          {TABS.map((tab) => {
            const Icon = tab.icon
            const isActive = activeTab === tab.id
            
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={clsx(
                  'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all text-left',
                  isActive
                    ? 'bg-freya-bg-tertiary text-freya-accent-blue border-l-2 border-freya-accent-blue'
                    : 'text-freya-text-secondary hover:text-freya-text-primary hover:bg-freya-bg-tertiary/50'
                )}
              >
                <Icon className={clsx('w-5 h-5', isActive && 'text-freya-accent-blue')} />
                <div className="flex-1 min-w-0">
                  <div className="font-medium">{tab.name}</div>
                  <div className="text-xs text-freya-text-muted truncate">{tab.description}</div>
                </div>
                {isActive && <ChevronRight className="w-4 h-4" />}
              </button>
            )
          })}
        </nav>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-3xl mx-auto">
          {/* Paths Tab */}
          {activeTab === 'paths' && (
            <div className="space-y-6 animate-fade-in">
              <div>
                <h3 className="text-xl font-semibold text-freya-text-primary mb-2">Directory Paths</h3>
                <p className="text-freya-text-muted">
                  Configure where Freya stores its data, artifacts, and cache files. Click edit to customize.
                </p>
              </div>

              <div className="space-y-4">
                {Object.entries(editedPaths).map(([key, value]) => (
                  <div
                    key={key}
                    className="p-4 bg-freya-bg-secondary rounded-lg border border-freya-border"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="text-sm font-medium text-freya-text-secondary capitalize flex items-center gap-2">
                        <FolderOpen className="w-4 h-4" />
                        {key.replace(/_/g, ' ')}
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => copyToClipboard(value, key)}
                          className="p-1.5 rounded hover:bg-freya-bg-tertiary transition-colors"
                          title="Copy path"
                        >
                          {copiedPath === key ? (
                            <Check className="w-4 h-4 text-freya-accent-green" />
                          ) : (
                            <Copy className="w-4 h-4 text-freya-text-muted" />
                          )}
                        </button>
                        <button
                          onClick={() => setEditingPath(editingPath === key ? null : key)}
                          className={clsx(
                            'p-1.5 rounded hover:bg-freya-bg-tertiary transition-colors',
                            editingPath === key && 'bg-freya-accent-blue/20'
                          )}
                          title="Edit path"
                        >
                          <Edit3 className="w-4 h-4 text-freya-text-muted" />
                        </button>
                      </div>
                    </div>
                    
                    {editingPath === key ? (
                      <div className="flex items-center gap-2">
                        <input
                          type="text"
                          value={value}
                          onChange={(e) => setEditedPaths(prev => ({ ...prev, [key]: e.target.value }))}
                          className="input flex-1 font-mono text-sm"
                          autoFocus
                        />
                        <button
                          onClick={() => savePath(key, value)}
                          className="btn-primary px-3 py-2"
                        >
                          <Save className="w-4 h-4" />
                        </button>
                      </div>
                    ) : (
                      <div className="font-mono text-sm text-freya-text-primary truncate">
                        {value}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              <div className="p-4 bg-freya-bg-tertiary rounded-lg border border-freya-border">
                <div className="flex items-start gap-3">
                  <Info className="w-5 h-5 text-freya-accent-blue mt-0.5" />
                  <div className="text-sm text-freya-text-secondary">
                    <p className="font-medium text-freya-text-primary mb-1">Environment Variables</p>
                    <p>
                      These paths can also be set using environment variables:{' '}
                      <code className="text-freya-accent-cyan">FREYA_MANAGED_ROOT</code>,{' '}
                      <code className="text-freya-accent-cyan">FREYA_CACHE_ROOT</code>,{' '}
                      <code className="text-freya-accent-cyan">FREYA_WORKSPACE_ROOT</code>
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Ollama Tab */}
          {activeTab === 'ollama' && (
            <div className="space-y-6 animate-fade-in">
              <div>
                <h3 className="text-xl font-semibold text-freya-text-primary mb-2">Ollama Connection</h3>
                <p className="text-freya-text-muted">
                  Configure the connection to your local Ollama server.
                </p>
              </div>

              {/* Connection Status */}
              <div className="p-4 bg-freya-bg-secondary rounded-lg border border-freya-border">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className={clsx(
                      'w-3 h-3 rounded-full',
                      health?.ollama?.connected ? 'bg-freya-accent-green animate-pulse' : 'bg-freya-accent-red'
                    )} />
                    <span className="font-medium text-freya-text-primary">
                      {health?.ollama?.connected ? 'Connected' : 'Disconnected'}
                    </span>
                  </div>
                  <span className="text-sm text-freya-text-muted">
                    {health?.ollama?.models_count ?? 0} models available
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-freya-text-secondary mb-2">Base URL</label>
                    <div className="input bg-freya-bg-primary flex items-center gap-2">
                      <Network className="w-4 h-4 text-freya-text-muted" />
                      <span className="text-freya-text-primary">
                        {health?.ollama?.base_url || 'http://localhost:11434'}
                      </span>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm text-freya-text-secondary mb-2">Timeout</label>
                    <div className="input bg-freya-bg-primary flex items-center gap-2">
                      <RefreshCw className="w-4 h-4 text-freya-text-muted" />
                      <span className="text-freya-text-primary">120s</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Models List */}
              {models && models.length > 0 && (
                <div className="p-4 bg-freya-bg-secondary rounded-lg border border-freya-border">
                  <h4 className="font-medium text-freya-text-primary mb-3">Installed Models</h4>
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {models.map((model) => (
                      <div
                        key={model.name}
                        className="flex items-center justify-between p-3 bg-freya-bg-primary rounded-lg"
                      >
                        <div className="flex items-center gap-3">
                          <Brain className="w-4 h-4 text-freya-accent-purple" />
                          <span className="font-mono text-sm text-freya-text-primary">
                            {model.name}
                          </span>
                        </div>
                        <div className="flex items-center gap-3 text-sm">
                          {model.size_gb && (
                            <span className="text-freya-text-muted">
                              {model.size_gb.toFixed(1)} GB
                            </span>
                          )}
                          {model.is_freya_pulled && (
                            <span className="badge badge-blue">Freya</span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Routing Tab */}
          {activeTab === 'routing' && (
            <div className="space-y-6 animate-fade-in">
              <div>
                <h3 className="text-xl font-semibold text-freya-text-primary mb-2">Model Routing</h3>
                <p className="text-freya-text-muted">
                  Configure which model to use for each BMAD role. You can manually override recommendations.
                </p>
              </div>

              <div className="space-y-3">
                {['analyst', 'pm', 'architect', 'po', 'sm', 'dev', 'qa'].map((role) => {
                  const config = routing?.find(r => r.role === role)
                  
                  return (
                    <div
                      key={role}
                      className="flex items-center justify-between p-4 bg-freya-bg-secondary rounded-lg border border-freya-border"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-freya-bg-tertiary flex items-center justify-center">
                          <Brain className="w-5 h-5 text-freya-accent-blue" />
                        </div>
                        <div>
                          <div className="font-medium text-freya-text-primary capitalize">{role}</div>
                          <div className="text-sm text-freya-text-muted">
                            {config?.model || 'Not configured'}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <select
                          value={config?.model || ''}
                          onChange={(e) => {
                            const newRouting = [...(routing || [])]
                            const idx = newRouting.findIndex(r => r.role === role)
                            if (idx >= 0) {
                              newRouting[idx] = { ...newRouting[idx], model: e.target.value }
                            } else {
                              newRouting.push({ role, model: e.target.value, options: {} })
                            }
                            saveRoutingMutation.mutate(newRouting)
                          }}
                          className="input w-56"
                        >
                          <option value="">Auto (Recommended)</option>
                          {models?.map((m) => (
                            <option key={m.name} value={m.name}>{m.name}</option>
                          ))}
                        </select>
                        {config?.model && (
                          <button
                            onClick={() => {
                              const newRouting = (routing || []).filter(r => r.role !== role)
                              saveRoutingMutation.mutate(newRouting)
                            }}
                            className="p-2 rounded hover:bg-freya-bg-tertiary text-freya-text-muted"
                            title="Reset to auto"
                          >
                            <RefreshCw className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Providers Tab (v2.2 Hybrid Routing) */}
          {activeTab === 'providers' && (
            <div className="space-y-6 animate-fade-in">
              <div>
                <h3 className="text-xl font-semibold text-freya-text-primary mb-2">Hybrid Routing & Providers</h3>
                <p className="text-freya-text-muted">
                  Configure local/remote LLM routing with multi-provider support and quota management.
                </p>
              </div>

              {/* Hybrid Routing Status */}
              <div className="p-4 bg-freya-bg-secondary rounded-lg border border-freya-border">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className={clsx(
                      'w-3 h-3 rounded-full',
                      hybridConfig?.enabled ? 'bg-freya-accent-green animate-pulse' : 'bg-freya-text-muted'
                    )} />
                    <h4 className="font-medium text-freya-text-primary">Hybrid Routing</h4>
                  </div>
                  <span className={clsx(
                    'badge',
                    hybridConfig?.enabled ? 'badge-green' : 'badge-yellow'
                  )}>
                    {hybridConfig?.enabled ? 'Enabled' : 'Disabled'}
                  </span>
                </div>
                
                {hybridConfig && (
                  <div className="grid grid-cols-4 gap-4 text-sm">
                    <div className="p-3 bg-freya-bg-primary rounded-lg">
                      <div className="text-freya-text-muted mb-1">Threshold</div>
                      <div className="font-medium text-freya-text-primary">
                        {((hybridConfig.percent_threshold - 1) * 100).toFixed(0)}% better
                      </div>
                    </div>
                    <div className="p-3 bg-freya-bg-primary rounded-lg">
                      <div className="text-freya-text-muted mb-1">Local Min Score</div>
                      <div className="font-medium text-freya-text-primary">{hybridConfig.local_min_score}</div>
                    </div>
                    <div className="p-3 bg-freya-bg-primary rounded-lg">
                      <div className="text-freya-text-muted mb-1">Fallback Chain</div>
                      <div className="font-medium text-freya-accent-cyan text-xs">
                        {hybridConfig.fallback_chain.join(' → ')}
                      </div>
                    </div>
                    <div className="p-3 bg-freya-bg-primary rounded-lg">
                      <div className="text-freya-text-muted mb-1">Max Retries</div>
                      <div className="font-medium text-freya-text-primary">{hybridConfig.max_retries}</div>
                    </div>
                  </div>
                )}
              </div>

              {/* Local Runtimes */}
              <div className="p-4 bg-freya-bg-secondary rounded-lg border border-freya-border">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="font-medium text-freya-text-primary flex items-center gap-2">
                    <Server className="w-5 h-5 text-freya-accent-blue" />
                    Local Runtimes
                  </h4>
                  <button
                    onClick={() => detectRuntimesMutation.mutate()}
                    disabled={detectRuntimesMutation.isPending}
                    className="btn-secondary text-sm flex items-center gap-2"
                  >
                    <RefreshCw className={clsx('w-4 h-4', detectRuntimesMutation.isPending && 'animate-spin')} />
                    Detect
                  </button>
                </div>
                
                <div className="grid grid-cols-2 gap-3">
                  {localRuntimes && Object.entries(localRuntimes).map(([id, runtime]) => (
                    <div key={id} className="flex items-center justify-between p-3 bg-freya-bg-primary rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className={clsx(
                          'w-2 h-2 rounded-full',
                          runtime.is_running ? 'bg-freya-accent-green' : 'bg-freya-accent-red'
                        )} />
                        <div>
                          <div className="font-medium text-freya-text-primary">{runtime.name}</div>
                          <div className="text-xs text-freya-text-muted">Port {runtime.port}</div>
                        </div>
                      </div>
                      <div className="text-right">
                        {runtime.is_running ? (
                          <span className="text-sm text-freya-accent-green">{runtime.models_count} models</span>
                        ) : (
                          <span className="text-sm text-freya-text-muted">Offline</span>
                        )}
                      </div>
                    </div>
                  ))}
                  {(!localRuntimes || Object.keys(localRuntimes).length === 0) && (
                    <div className="col-span-2 text-center py-4 text-freya-text-muted">
                      Click "Detect" to scan for local LLM runtimes
                    </div>
                  )}
                </div>
              </div>

              {/* Remote Providers */}
              <div className="p-4 bg-freya-bg-secondary rounded-lg border border-freya-border">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="font-medium text-freya-text-primary flex items-center gap-2">
                    <Cloud className="w-5 h-5 text-freya-accent-purple" />
                    Remote Providers
                  </h4>
                  <button
                    onClick={() => refetchProviders()}
                    className="btn-ghost text-sm"
                  >
                    <RefreshCw className="w-4 h-4" />
                  </button>
                </div>
                
                <div className="space-y-3">
                  {providers && Object.entries(providers).map(([id, provider]) => (
                    <div key={id} className="p-4 bg-freya-bg-primary rounded-lg border border-freya-border">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div className={clsx(
                            'w-10 h-10 rounded-lg flex items-center justify-center',
                            provider.enabled && provider.has_api_key 
                              ? 'bg-freya-accent-green/20' 
                              : 'bg-freya-bg-tertiary'
                          )}>
                            {provider.has_api_key ? (
                              <CheckCircle2 className="w-5 h-5 text-freya-accent-green" />
                            ) : (
                              <AlertCircle className="w-5 h-5 text-freya-text-muted" />
                            )}
                          </div>
                          <div>
                            <div className="font-medium text-freya-text-primary">{provider.name}</div>
                            <div className="text-xs text-freya-text-muted">Priority: {provider.priority}</div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {provider.free_tier?.credits_usd && (
                            <span className="badge badge-green">
                              ${provider.free_tier.credits_usd} free
                            </span>
                          )}
                          <span className={clsx(
                            'badge',
                            provider.enabled ? 'badge-blue' : 'badge-yellow'
                          )}>
                            {provider.enabled ? 'Enabled' : 'Disabled'}
                          </span>
                        </div>
                      </div>
                      
                      {/* API Key Input */}
                      <div className="flex items-center gap-2 mb-3">
                        <input
                          type={showProviderKey[id] ? 'text' : 'password'}
                          value={providerKeys[id] || ''}
                          onChange={(e) => setProviderKeys(prev => ({ ...prev, [id]: e.target.value }))}
                          placeholder={provider.has_api_key ? '••••••••••••••••' : 'Enter API key...'}
                          className="input flex-1 font-mono text-sm"
                        />
                        <button
                          onClick={() => setShowProviderKey(prev => ({ ...prev, [id]: !prev[id] }))}
                          className="btn-ghost px-2"
                        >
                          {showProviderKey[id] ? 'Hide' : 'Show'}
                        </button>
                        <button
                          onClick={() => {
                            if (providerKeys[id]) {
                              updateProviderKeyMutation.mutate({ provider: id, apiKey: providerKeys[id] })
                              setProviderKeys(prev => ({ ...prev, [id]: '' }))
                            }
                          }}
                          disabled={!providerKeys[id] || updateProviderKeyMutation.isPending}
                          className="btn-primary px-3"
                        >
                          <Save className="w-4 h-4" />
                        </button>
                      </div>
                      
                      {/* Rate Limits */}
                      {provider.rate_limits && (
                        <div className="flex flex-wrap gap-2 text-xs">
                          {provider.rate_limits.rpm && (
                            <span className="px-2 py-1 bg-freya-bg-tertiary rounded text-freya-text-muted">
                              {provider.rate_limits.rpm} RPM
                            </span>
                          )}
                          {provider.rate_limits.tpm && (
                            <span className="px-2 py-1 bg-freya-bg-tertiary rounded text-freya-text-muted">
                              {(provider.rate_limits.tpm / 1000).toFixed(0)}K TPM
                            </span>
                          )}
                          {provider.rate_limits.rpd && (
                            <span className="px-2 py-1 bg-freya-bg-tertiary rounded text-freya-text-muted">
                              {(provider.rate_limits.rpd / 1000).toFixed(1)}K RPD
                            </span>
                          )}
                        </div>
                      )}
                      
                      {/* Available Models */}
                      {provider.models && provider.models.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-freya-border">
                          <div className="text-xs text-freya-text-muted mb-2">Available Models:</div>
                          <div className="flex flex-wrap gap-1">
                            {provider.models.slice(0, 5).map(model => (
                              <span key={model} className="badge badge-blue text-xs">{model}</span>
                            ))}
                            {provider.models.length > 5 && (
                              <span className="badge badge-purple text-xs">+{provider.models.length - 5} more</span>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Usage Statistics */}
              {usageStats && (
                <div className="p-4 bg-freya-bg-secondary rounded-lg border border-freya-border">
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="font-medium text-freya-text-primary flex items-center gap-2">
                      <TrendingUp className="w-5 h-5 text-freya-accent-cyan" />
                      Usage Statistics
                    </h4>
                    <button onClick={() => refetchUsageStats()} className="btn-ghost text-sm">
                      <RefreshCw className="w-4 h-4" />
                    </button>
                  </div>
                  
                  <div className="grid grid-cols-3 gap-4 mb-4">
                    <div className="p-3 bg-freya-bg-primary rounded-lg text-center">
                      <div className="text-2xl font-bold text-freya-text-primary">{usageStats.total_requests}</div>
                      <div className="text-xs text-freya-text-muted">Total Requests</div>
                    </div>
                    <div className="p-3 bg-freya-bg-primary rounded-lg text-center">
                      <div className="text-2xl font-bold text-freya-accent-green">{usageStats.local_requests}</div>
                      <div className="text-xs text-freya-text-muted">Local</div>
                    </div>
                    <div className="p-3 bg-freya-bg-primary rounded-lg text-center">
                      <div className="text-2xl font-bold text-freya-accent-purple">{usageStats.remote_requests}</div>
                      <div className="text-xs text-freya-text-muted">Remote</div>
                    </div>
                  </div>
                  
                  {/* Per-provider breakdown */}
                  {usageStats.by_provider && Object.keys(usageStats.by_provider).length > 0 && (
                    <div className="space-y-2">
                      {Object.entries(usageStats.by_provider).map(([provider, stats]) => (
                        <div key={provider} className="flex items-center justify-between p-2 bg-freya-bg-primary rounded">
                          <span className="text-sm text-freya-text-primary capitalize">{provider}</span>
                          <div className="flex items-center gap-4 text-xs text-freya-text-muted">
                            <span>{stats.requests} requests</span>
                            <span>{(stats.tokens_used / 1000).toFixed(1)}K tokens</span>
                            {stats.estimated_cost > 0 && (
                              <span className="text-freya-accent-yellow">
                                ${stats.estimated_cost.toFixed(4)}
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Info Box */}
              <div className="p-4 bg-freya-bg-tertiary rounded-lg border border-freya-border">
                <div className="flex items-start gap-3">
                  <Info className="w-5 h-5 text-freya-accent-blue mt-0.5" />
                  <div className="text-sm text-freya-text-secondary">
                    <p className="font-medium text-freya-text-primary mb-1">Hybrid Routing Logic</p>
                    <p>
                      Freya routes requests to the best available provider: 1) Check local availability and score;
                      2) If local score ≥ {hybridConfig?.local_min_score || 70}, use local; 3) Otherwise, try remote providers
                      in fallback order if they're {((hybridConfig?.percent_threshold || 1.2) - 1) * 100}%+ better;
                      4) Respect quotas and rate limits automatically.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Prompts Tab */}
          {activeTab === 'prompts' && (
            <div className="space-y-6 animate-fade-in">
              <div>
                <h3 className="text-xl font-semibold text-freya-text-primary mb-2">System Prompts</h3>
                <p className="text-freya-text-muted">
                  Manage system prompts used by Freya agents.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                {/* Prompts List */}
                <div className="bg-freya-bg-secondary rounded-lg border border-freya-border p-4">
                  <h4 className="font-medium text-freya-text-primary mb-3">Available Prompts</h4>
                  <div className="space-y-2 max-h-96 overflow-y-auto">
                    {prompts?.map((prompt) => (
                      <button
                        key={prompt.name}
                        onClick={() => loadPrompt(prompt.name)}
                        className={clsx(
                          'w-full text-left p-3 rounded-lg transition-all',
                          selectedPrompt === prompt.name
                            ? 'bg-freya-accent-blue/10 border border-freya-accent-blue/30'
                            : 'bg-freya-bg-primary border border-transparent hover:border-freya-border'
                        )}
                      >
                        <div className="flex items-center gap-2">
                          <FileCode className="w-4 h-4 text-freya-text-muted" />
                          <span className="font-mono text-sm text-freya-text-primary">
                            {prompt.name}
                          </span>
                        </div>
                        {prompt.preview && (
                          <p className="text-xs text-freya-text-muted mt-1 truncate">
                            {prompt.preview}
                          </p>
                        )}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Prompt Editor */}
                <div className="bg-freya-bg-secondary rounded-lg border border-freya-border p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-medium text-freya-text-primary">
                      {selectedPrompt || 'Select a prompt'}
                    </h4>
                    {selectedPrompt && (
                      <button
                        onClick={() => savePromptMutation.mutate()}
                        disabled={savePromptMutation.isPending}
                        className="btn-primary text-sm flex items-center gap-2"
                      >
                        <Save className="w-4 h-4" />
                        Save
                      </button>
                    )}
                  </div>
                  <textarea
                    value={promptContent}
                    onChange={(e) => setPromptContent(e.target.value)}
                    placeholder="Select a prompt to edit..."
                    className="textarea h-80 font-mono text-sm"
                    disabled={!selectedPrompt}
                  />
                </div>
              </div>
            </div>
          )}

          {/* API Keys Tab */}
          {activeTab === 'api' && (
            <div className="space-y-6 animate-fade-in">
              <div>
                <h3 className="text-xl font-semibold text-freya-text-primary mb-2">API Integrations</h3>
                <p className="text-freya-text-muted">
                  Configure API keys for external services. Keys are stored locally and encrypted.
                </p>
              </div>

              {/* GitHub Integration */}
              <div className="p-4 bg-freya-bg-secondary rounded-lg border border-freya-border">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-lg bg-freya-bg-tertiary flex items-center justify-center">
                    <Github className="w-5 h-5 text-freya-text-primary" />
                  </div>
                  <div>
                    <h4 className="font-medium text-freya-text-primary">GitHub</h4>
                    <p className="text-sm text-freya-text-muted">Access repositories and security advisories</p>
                  </div>
                </div>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm text-freya-text-secondary mb-2">Personal Access Token</label>
                    <div className="flex items-center gap-2">
                      <input
                        type={showApiKeys.github ? 'text' : 'password'}
                        value={apiKeys.github_token}
                        onChange={(e) => setApiKeys(prev => ({ ...prev, github_token: e.target.value }))}
                        placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
                        className="input flex-1 font-mono"
                      />
                      <button
                        onClick={() => setShowApiKeys(prev => ({ ...prev, github: !prev.github }))}
                        className="btn-secondary px-3"
                      >
                        {showApiKeys.github ? 'Hide' : 'Show'}
                      </button>
                    </div>
                    <p className="text-xs text-freya-text-muted mt-1">
                      Required scopes: repo, read:org, read:user
                    </p>
                  </div>
                </div>
              </div>

              {/* GitLab Integration */}
              <div className="p-4 bg-freya-bg-secondary rounded-lg border border-freya-border">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-lg bg-freya-bg-tertiary flex items-center justify-center">
                    <GitBranch className="w-5 h-5 text-freya-accent-orange" />
                  </div>
                  <div>
                    <h4 className="font-medium text-freya-text-primary">GitLab</h4>
                    <p className="text-sm text-freya-text-muted">Access GitLab repositories</p>
                  </div>
                </div>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm text-freya-text-secondary mb-2">GitLab URL</label>
                    <input
                      type="text"
                      value={apiKeys.gitlab_url}
                      onChange={(e) => setApiKeys(prev => ({ ...prev, gitlab_url: e.target.value }))}
                      placeholder="https://gitlab.com"
                      className="input font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-freya-text-secondary mb-2">Personal Access Token</label>
                    <div className="flex items-center gap-2">
                      <input
                        type={showApiKeys.gitlab ? 'text' : 'password'}
                        value={apiKeys.gitlab_token}
                        onChange={(e) => setApiKeys(prev => ({ ...prev, gitlab_token: e.target.value }))}
                        placeholder="glpat-xxxxxxxxxxxxxxxxxxxx"
                        className="input flex-1 font-mono"
                      />
                      <button
                        onClick={() => setShowApiKeys(prev => ({ ...prev, gitlab: !prev.gitlab }))}
                        className="btn-secondary px-3"
                      >
                        {showApiKeys.gitlab ? 'Hide' : 'Show'}
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Search APIs */}
              <div className="p-4 bg-freya-bg-secondary rounded-lg border border-freya-border">
                <h4 className="font-medium text-freya-text-primary mb-4">Search & Security APIs</h4>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm text-freya-text-secondary mb-2">Brave Search API Key (Optional)</label>
                    <input
                      type={showApiKeys.brave ? 'text' : 'password'}
                      value={apiKeys.brave_api_key}
                      onChange={(e) => setApiKeys(prev => ({ ...prev, brave_api_key: e.target.value }))}
                      placeholder="BSAxxxxxxxxxxxxxxxxxx"
                      className="input font-mono"
                    />
                    <p className="text-xs text-freya-text-muted mt-1">
                      Optional. DuckDuckGo is used by default (free, unlimited).
                    </p>
                  </div>
                  <div>
                    <label className="block text-sm text-freya-text-secondary mb-2">NVD API Key (Optional)</label>
                    <input
                      type={showApiKeys.nvd ? 'text' : 'password'}
                      value={apiKeys.nvd_api_key}
                      onChange={(e) => setApiKeys(prev => ({ ...prev, nvd_api_key: e.target.value }))}
                      placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                      className="input font-mono"
                    />
                    <p className="text-xs text-freya-text-muted mt-1">
                      Higher rate limits for CVE lookups. Get one at nvd.nist.gov
                    </p>
                  </div>
                  <div>
                    <label className="block text-sm text-freya-text-secondary mb-2">SearXNG Instance URL (Optional)</label>
                    <input
                      type="text"
                      value={apiKeys.searxng_url}
                      onChange={(e) => setApiKeys(prev => ({ ...prev, searxng_url: e.target.value }))}
                      placeholder="https://searx.example.com"
                      className="input font-mono"
                    />
                    <p className="text-xs text-freya-text-muted mt-1">
                      Self-hosted SearXNG instance for privacy-focused search.
                    </p>
                  </div>
                </div>
              </div>

              <button onClick={saveApiKeys} className="btn-primary flex items-center gap-2">
                <Save className="w-4 h-4" />
                Save API Keys
              </button>
            </div>
          )}

          {/* Appearance Tab */}
          {activeTab === 'appearance' && (
            <div className="space-y-6 animate-fade-in">
              <div>
                <h3 className="text-xl font-semibold text-freya-text-primary mb-2">Appearance</h3>
                <p className="text-freya-text-muted">
                  Customize the visual appearance of Freya. Changes apply in real-time.
                </p>
              </div>

              {/* Theme Selection */}
              <div className="p-4 bg-freya-bg-secondary rounded-lg border border-freya-border">
                <h4 className="font-medium text-freya-text-primary mb-4">Theme</h4>
                <div className="grid grid-cols-5 gap-3">
                  {THEMES.map((theme) => {
                    const Icon = theme.icon
                    const isSelected = selectedTheme === theme.id
                    
                    return (
                      <button
                        key={theme.id}
                        onClick={() => setSelectedTheme(theme.id)}
                        className={clsx(
                          'p-3 rounded-lg border-2 transition-all',
                          isSelected
                            ? 'border-freya-accent-blue bg-freya-bg-primary'
                            : 'border-freya-border bg-freya-bg-primary hover:border-freya-border-light'
                        )}
                      >
                        <div
                          className="w-full h-12 rounded mb-2"
                          style={{
                            background: `linear-gradient(135deg, ${theme.colors.from}, ${theme.colors.to})`
                          }}
                        />
                        <div className="flex items-center justify-center gap-1">
                          <Icon className="w-3 h-3" />
                          <span className="text-xs font-medium">{theme.name}</span>
                        </div>
                        {isSelected && (
                          <Check className="w-4 h-4 text-freya-accent-blue mx-auto mt-1" />
                        )}
                      </button>
                    )
                  })}
                </div>
              </div>

              {/* Font Selection */}
              <div className="p-4 bg-freya-bg-secondary rounded-lg border border-freya-border">
                <h4 className="font-medium text-freya-text-primary mb-4">Font Family</h4>
                <div className="grid grid-cols-2 gap-3">
                  {FONTS.map((font) => {
                    const isSelected = selectedFont === font.id
                    
                    return (
                      <button
                        key={font.id}
                        onClick={() => setSelectedFont(font.id)}
                        className={clsx(
                          'p-4 rounded-lg border-2 text-left transition-all',
                          isSelected
                            ? 'border-freya-accent-blue bg-freya-bg-primary'
                            : 'border-freya-border bg-freya-bg-primary hover:border-freya-border-light'
                        )}
                        style={{ fontFamily: font.family }}
                      >
                        <div className="text-lg mb-1">{font.name}</div>
                        <div className="text-sm text-freya-text-muted">
                          The quick brown fox jumps over the lazy dog
                        </div>
                        {isSelected && (
                          <Check className="w-4 h-4 text-freya-accent-blue mt-2" />
                        )}
                      </button>
                    )
                  })}
                </div>
              </div>

              {/* Font Size */}
              <div className="p-4 bg-freya-bg-secondary rounded-lg border border-freya-border">
                <h4 className="font-medium text-freya-text-primary mb-4">Font Size</h4>
                <div className="flex items-center gap-4">
                  <span className="text-sm text-freya-text-muted">12px</span>
                  <input
                    type="range"
                    min="12"
                    max="20"
                    value={fontSize}
                    onChange={(e) => setFontSize(parseInt(e.target.value))}
                    className="flex-1"
                  />
                  <span className="text-sm text-freya-text-muted">20px</span>
                  <span className="badge badge-blue">{fontSize}px</span>
                </div>
                <p className="text-sm text-freya-text-muted mt-2" style={{ fontSize: `${fontSize}px` }}>
                  Preview: This is how text will appear at {fontSize}px
                </p>
              </div>
            </div>
          )}

          {/* About Tab */}
          {activeTab === 'about' && (
            <div className="space-y-6 animate-fade-in">
              <div>
                <h3 className="text-xl font-semibold text-freya-text-primary mb-2">About Freya</h3>
                <p className="text-freya-text-muted">
                  BMAD-aligned multi-agent orchestrator for local LLMs.
                </p>
              </div>

              {/* Version Info */}
              <div className="p-6 bg-freya-bg-secondary rounded-lg border border-freya-border text-center">
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-freya-accent-blue to-freya-accent-purple mx-auto mb-4 flex items-center justify-center">
                  <Cpu className="w-8 h-8 text-white" />
                </div>
                <h4 className="text-2xl font-bold text-freya-text-primary mb-1">Freya</h4>
                <p className="text-freya-text-secondary mb-4">
                  Version {version?.version || '2.0.0'}
                </p>
                <div className="flex items-center justify-center gap-4 text-sm">
                  <span className="badge badge-blue">API v{version?.api_version || '2.0'}</span>
                  <span className="badge badge-purple">BMAD Method</span>
                </div>
              </div>

              {/* System Info */}
              {systemInfo && (
                <div className="p-4 bg-freya-bg-secondary rounded-lg border border-freya-border">
                  <h4 className="font-medium text-freya-text-primary mb-4">System Resources</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 bg-freya-bg-primary rounded-lg">
                      <div className="flex items-center gap-2 text-freya-text-muted mb-1">
                        <Cpu className="w-4 h-4" />
                        <span className="text-sm">CPU</span>
                      </div>
                      <div className="text-xl font-bold text-freya-text-primary">
                        {systemInfo.cpu_percent.toFixed(0)}%
                      </div>
                    </div>
                    <div className="p-3 bg-freya-bg-primary rounded-lg">
                      <div className="flex items-center gap-2 text-freya-text-muted mb-1">
                        <Database className="w-4 h-4" />
                        <span className="text-sm">RAM</span>
                      </div>
                      <div className="text-xl font-bold text-freya-text-primary">
                        {systemInfo.ram_percent.toFixed(0)}%
                      </div>
                    </div>
                    <div className="p-3 bg-freya-bg-primary rounded-lg col-span-2">
                      <div className="flex items-center gap-2 text-freya-text-muted mb-1">
                        <HardDrive className="w-4 h-4" />
                        <span className="text-sm">Disk</span>
                      </div>
                      <div className="text-xl font-bold text-freya-text-primary">
                        {systemInfo.disk_free_gb.toFixed(0)} GB free / {systemInfo.disk_total_gb.toFixed(0)} GB
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Links */}
              <div className="flex items-center justify-center gap-4 text-sm">
                <a href="#" className="flex items-center gap-1 text-freya-accent-blue hover:underline">
                  Documentation <ExternalLink className="w-3 h-3" />
                </a>
                <a href="https://github.com/Duperopope/Freya" target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-freya-accent-blue hover:underline">
                  GitHub <ExternalLink className="w-3 h-3" />
                </a>
                <a href="https://github.com/Duperopope/Freya/issues" target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-freya-accent-blue hover:underline">
                  Report Issue <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
