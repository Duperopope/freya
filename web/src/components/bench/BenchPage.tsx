/**
 * BenchPage - LLM Benchmarking Dashboard v2.2
 * 
 * Modern, professional interface for running and analyzing LLM benchmarks.
 * Features:
 * - Real-time progress tracking
 * - Expandable detailed results per model
 * - Continuous mode (Fast → Standard → Advanced → Fine-tuning)
 * - Manual model selection override
 * - Import external benchmarks (MMLU, HellaSwag formats)
 * - Export results in multiple formats
 */

import { useState, useEffect, useRef } from 'react'
import { 
  Play, 
  Square, 
  RefreshCw, 
  ChevronDown,
  ChevronUp,
  Zap,
  Target,
  Award,
  Clock,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  TrendingUp,
  Settings2,
  Upload,
  Repeat,
  Edit3,
  Timer,
  Cpu,
  Activity,
  FileJson,
  FileSpreadsheet,
  ArrowRight,
  Pause,
  SkipForward,
  Sliders,
  Info,
  Eye,
  EyeOff,
  Trash2,
  RotateCcw,
  Star
} from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { clsx } from 'clsx'
import * as api from '../../lib/api'
import { useAppStore } from '../../stores/appStore'

// Benchmark program types
type BenchProgram = 'bench-fast' | 'bench-standard' | 'bench-advanced'

interface ProgramInfo {
  id: BenchProgram
  name: string
  description: string
  icon: typeof Zap
  duration: string
  trials: number
  color: string
  order: number
}

const PROGRAMS: ProgramInfo[] = [
  {
    id: 'bench-fast',
    name: 'Fast Scan',
    description: 'Quick evaluation with single trial per model',
    icon: Zap,
    duration: '~5 min',
    trials: 1,
    color: 'text-freya-accent-green',
    order: 1
  },
  {
    id: 'bench-standard',
    name: 'Standard',
    description: 'Balanced benchmark with multiple trials',
    icon: Target,
    duration: '~20 min',
    trials: 5,
    color: 'text-freya-accent-blue',
    order: 2
  },
  {
    id: 'bench-advanced',
    name: 'Advanced',
    description: 'Comprehensive multi-phase benchmark',
    icon: Award,
    duration: '~60 min',
    trials: 5,
    color: 'text-freya-accent-purple',
    order: 3
  }
]

const ROLES = ['analyst', 'pm', 'architect', 'po', 'sm', 'dev', 'qa']

const ROLE_DESCRIPTIONS: Record<string, string> = {
  analyst: 'Requirements analysis, stakeholder identification',
  pm: 'Product requirements, feature planning',
  architect: 'System design, technical architecture',
  po: 'Epic breakdown, feature prioritization',
  sm: 'User stories, sprint planning',
  dev: 'Code implementation, clean code practices',
  qa: 'Quality assurance, test coverage'
}

interface ModelOverride {
  role: string
  model: string
  isManual: boolean
}

interface ImportedBenchmark {
  name: string
  format: string
  models: number
  imported_at: string
}

export function BenchPage() {
  const queryClient = useQueryClient()
  const { benchProgress, setBenchProgress } = useAppStore()
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  // Prevent double-start (fixes 409 Conflict errors)
  const isStartingRef = useRef(false)
  
  // Core state
  const [selectedProgram, setSelectedProgram] = useState<BenchProgram>('bench-fast')
  const [expandedRole, setExpandedRole] = useState<string | null>(null)
  const [expandedModel, setExpandedModel] = useState<string | null>(null)
  const [showSettings, setShowSettings] = useState(false)
  
  // Continuous mode state - Default ON as requested
  const [continuousMode, setContinuousMode] = useState(true) // Default ON
  const [continuousPhase, setContinuousPhase] = useState<BenchProgram | 'fine-tuning' | null>(null)
  const [autoAdvance, setAutoAdvance] = useState(true) // Auto-switch intelligent ON by default
  
  // Configurable trials per category
  const [trialsConfig, setTrialsConfig] = useState<Record<BenchProgram, number>>({
    'bench-fast': 1,
    'bench-standard': 5,
    'bench-advanced': 5
  })
  
  // Current best model (real-time)
  const [currentBestModel, setCurrentBestModel] = useState<{ role: string; model: string; score: number } | null>(null)
  
  // Time estimation state
  const [phaseStartTime, setPhaseStartTime] = useState<Date | null>(null)
  const [estimatedTimeRemaining, setEstimatedTimeRemaining] = useState<string | null>(null)
  
  // Manual model selection
  const [modelOverrides, setModelOverrides] = useState<ModelOverride[]>([])
  const [editingRole, setEditingRole] = useState<string | null>(null)
  
  // Import state
  const [importedBenchmarks, setImportedBenchmarks] = useState<ImportedBenchmark[]>([])
  const [showImportDialog, setShowImportDialog] = useState(false)
  
  // Show/hide detailed metrics
  const [showDetailedMetrics, setShowDetailedMetrics] = useState(true)

  // Fetch current bench status
  const { data: status, refetch: refetchStatus } = useQuery({
    queryKey: ['benchStatus'],
    queryFn: api.getBenchStatus,
    refetchInterval: benchProgress?.running ? 1000 : 5000,
  })

  // Fetch billboard (best scores)
  const { data: billboard } = useQuery({
    queryKey: ['billboard'],
    queryFn: api.getBillboard,
  })

  // Fetch history
  const { data: history, isLoading: historyLoading, error: historyError } = useQuery({
    queryKey: ['benchHistory', selectedProgram],
    queryFn: () => api.getBenchHistory(selectedProgram, 100),
  })
  
  // Debug: log history state
  useEffect(() => {
    console.log('[Bench] History data:', { 
      program: selectedProgram,
      historyLength: history?.length || 0,
      historyLoading,
      historyError: historyError?.message
    })
  }, [history, selectedProgram, historyLoading, historyError])

  // Fetch models for manual selection
  const { data: models } = useQuery({
    queryKey: ['models'],
    queryFn: api.getModels,
  })

  // Update store when status changes
  useEffect(() => {
    if (status) {
      // Cap progress at 100% to fix the 101% bug
      const cappedProgress = Math.min(100, status.progress_percent)
      
      setBenchProgress(status.running ? {
        running: status.running,
        program: status.program,
        phase: status.phase,
        role: status.role,
        model: status.model,
        progress_percent: cappedProgress,
      } : null)
      
      // Track phase start time for estimation
      if (status.running && !phaseStartTime) {
        setPhaseStartTime(new Date())
      }
      
      // Calculate time estimation
      if (status.running && phaseStartTime && cappedProgress > 0 && cappedProgress < 100) {
        const elapsed = (new Date().getTime() - phaseStartTime.getTime()) / 1000
        const estimatedTotal = elapsed / (cappedProgress / 100)
        const remaining = estimatedTotal - elapsed
        
        if (remaining > 0) {
          const mins = Math.floor(remaining / 60)
          const secs = Math.floor(remaining % 60)
          setEstimatedTimeRemaining(`~${mins}m ${secs}s remaining`)
        } else {
          setEstimatedTimeRemaining('Completing...')
        }
      } else if (cappedProgress >= 100) {
        setEstimatedTimeRemaining('Finalizing...')
      }
      
      // Handle continuous mode progression - trigger when bench completes
      // Only trigger if we were running before and now stopped
      if (continuousMode && !status.running && continuousPhase && autoAdvance && !startMutation.isPending) {
        // Reset time tracking for next phase
        setPhaseStartTime(null)
        setEstimatedTimeRemaining(null)
        // Use setTimeout to prevent multiple rapid calls
        setTimeout(() => {
          if (!startMutation.isPending) {
            handleContinuousProgression()
          }
        }, 500)
      }
      
      // Reset time tracking when stopped
      if (!status.running) {
        setPhaseStartTime(null)
      }
    }
  }, [status, setBenchProgress, continuousMode, continuousPhase, autoAdvance, phaseStartTime])
  
  // Update current best model in real-time from billboard
  useEffect(() => {
    if (billboard && billboard.length > 0 && status?.running) {
      // Find the best scoring model across all roles
      const best = billboard.reduce((acc, entry) => {
        if (!acc || entry.score > acc.score) {
          return { role: entry.role, model: entry.model, score: entry.score }
        }
        return acc
      }, null as { role: string; model: string; score: number } | null)
      setCurrentBestModel(best)
    }
  }, [billboard, status?.running])

  // Start benchmark mutation with guard against double-start
  const startMutation = useMutation({
    mutationFn: async (program: string) => {
      // Guard: prevent multiple concurrent start calls
      if (isStartingRef.current || status?.running) {
        console.log('[Bench] Start blocked: already starting or running')
        return Promise.resolve({ status: 'already_running' })
      }
      isStartingRef.current = true
      try {
        return await api.startBench(program, true)
      } finally {
        // Reset after a short delay to prevent race conditions
        setTimeout(() => { isStartingRef.current = false }, 1000)
      }
    },
    onSuccess: () => {
      refetchStatus()
      queryClient.invalidateQueries({ queryKey: ['billboard'] })
    },
    onError: () => {
      isStartingRef.current = false
    },
  })

  // Stop benchmark mutation
  const stopMutation = useMutation({
    mutationFn: api.stopBench,
    onSuccess: () => {
      refetchStatus()
      setContinuousMode(false)
      setContinuousPhase(null)
    },
  })

  // Apply routing mutation
  const applyRoutingMutation = useMutation({
    mutationFn: api.applyRouting,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['routing'] })
    },
  })

  const isRunning = status?.running ?? false

  // Handle continuous mode progression
  const handleContinuousProgression = () => {
    if (!autoAdvance) {
      console.log('[Bench] Auto-advance disabled, stopping progression')
      return
    }
    
    const currentOrder = PROGRAMS.find(p => p.id === continuousPhase)?.order ?? 0
    const nextProgram = PROGRAMS.find(p => p.order === currentOrder + 1)
    
    console.log(`[Bench] Continuous progression: current=${continuousPhase}, order=${currentOrder}, next=${nextProgram?.id || 'none'}`)
    
    if (nextProgram) {
      console.log(`[Bench] Advancing to ${nextProgram.id} in 3 seconds...`)
      setContinuousPhase(nextProgram.id)
      setSelectedProgram(nextProgram.id)
      // Delay to allow UI update and prevent race conditions
      setTimeout(() => {
        // Double-check not already running before starting
        if (!isStartingRef.current && !status?.running) {
          console.log(`[Bench] Starting ${nextProgram.id}`)
          startMutation.mutate(nextProgram.id)
          setPhaseStartTime(new Date())
        } else {
          console.log(`[Bench] Skipped starting ${nextProgram.id}: already running`)
        }
      }, 3000)
    } else if (continuousPhase === 'bench-advanced') {
      // All benchmark phases complete, switch to fine-tuning mode
      console.log('[Bench] All benchmark phases complete, entering fine-tuning')
      setContinuousPhase('fine-tuning')
      // TODO: Implement fine-tuning auto-trigger
    } else {
      // All phases including fine-tuning complete
      console.log('[Bench] Continuous benchmark fully complete')
      setContinuousMode(false)
      setContinuousPhase(null)
      setEstimatedTimeRemaining(null)
    }
  }

  // Start continuous benchmark
  const startContinuousBenchmark = () => {
    // Guard against double-start
    if (isStartingRef.current || status?.running) {
      console.log('[Bench] Continuous start blocked: already running')
      return
    }
    console.log('[Bench] Starting continuous benchmark from bench-fast')
    setContinuousMode(true)
    setContinuousPhase('bench-fast')
    setSelectedProgram('bench-fast')
    setPhaseStartTime(new Date())
    setEstimatedTimeRemaining(null)
    startMutation.mutate('bench-fast')
  }

  // Group history by role
  const historyByRole = ROLES.reduce((acc, role) => {
    acc[role] = history?.filter(h => h.role === role) || []
    return acc
  }, {} as Record<string, api.BenchResult[]>)

  // Group history by model within a role
  const getModelDetails = (role: string) => {
    const roleHistory = historyByRole[role]
    const byModel: Record<string, api.BenchResult[]> = {}
    roleHistory.forEach(h => {
      if (!byModel[h.model]) byModel[h.model] = []
      byModel[h.model].push(h)
    })
    return byModel
  }

  // Get best model for each role from billboard
  const bestByRole = billboard?.reduce((acc, entry) => {
    if (!acc[entry.role] || entry.score > acc[entry.role].score) {
      acc[entry.role] = entry
    }
    return acc
  }, {} as Record<string, api.BillboardEntry>) || {}

  // Get effective model for a role (override or best)
  const getEffectiveModel = (role: string): string | null => {
    const override = modelOverrides.find(o => o.role === role)
    if (override) return override.model
    return bestByRole[role]?.model || null
  }

  // Handle model override
  const setModelOverride = (role: string, model: string) => {
    setModelOverrides(prev => {
      const filtered = prev.filter(o => o.role !== role)
      return [...filtered, { role, model, isManual: true }]
    })
    setEditingRole(null)
  }

  // Clear model override
  const clearModelOverride = (role: string) => {
    setModelOverrides(prev => prev.filter(o => o.role !== role))
  }

  // Calculate statistics for a model
  const calculateModelStats = (results: api.BenchResult[]) => {
    if (results.length === 0) return null
    
    const scores = results.map(r => r.score)
    const latencies = results.map(r => r.latency_ms)
    
    return {
      avgScore: scores.reduce((a, b) => a + b, 0) / scores.length,
      minScore: Math.min(...scores),
      maxScore: Math.max(...scores),
      stdDev: Math.sqrt(scores.reduce((acc, s) => acc + Math.pow(s - (scores.reduce((a, b) => a + b, 0) / scores.length), 2), 0) / scores.length),
      avgLatency: latencies.reduce((a, b) => a + b, 0) / latencies.length,
      minLatency: Math.min(...latencies),
      maxLatency: Math.max(...latencies),
      totalRuns: results.length,
      successRate: (results.filter(r => r.status === 'ok').length / results.length) * 100
    }
  }

  // Export results
  const exportResults = (format: 'json' | 'csv') => {
    const data = {
      exported_at: new Date().toISOString(),
      program: selectedProgram,
      billboard: billboard,
      history: history,
      overrides: modelOverrides
    }
    
    let content: string
    let filename: string
    let mimeType: string
    
    if (format === 'json') {
      content = JSON.stringify(data, null, 2)
      filename = `freya-benchmark-${selectedProgram}-${new Date().toISOString().split('T')[0]}.json`
      mimeType = 'application/json'
    } else {
      // CSV export
      const rows = [['Role', 'Model', 'Phase', 'Score', 'Latency (ms)', 'Status']]
      history?.forEach(h => {
        rows.push([h.role, h.model, h.phase, h.score.toString(), h.latency_ms.toString(), h.status])
      })
      content = rows.map(r => r.join(',')).join('\n')
      filename = `freya-benchmark-${selectedProgram}-${new Date().toISOString().split('T')[0]}.csv`
      mimeType = 'text/csv'
    }
    
    const blob = new Blob([content], { type: mimeType })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }

  // Import benchmark file
  const handleImport = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return
    
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const content = e.target?.result as string
        let format = 'unknown'
        let models = 0
        
        if (file.name.endsWith('.json')) {
          const data = JSON.parse(content)
          format = data.format || 'Custom JSON'
          models = data.results?.length || data.models?.length || 0
        } else if (file.name.endsWith('.csv')) {
          format = 'CSV'
          models = content.split('\n').length - 1
        }
        
        setImportedBenchmarks(prev => [...prev, {
          name: file.name,
          format,
          models,
          imported_at: new Date().toISOString()
        }])
        
        setShowImportDialog(false)
      } catch {
        console.error('Failed to parse benchmark file')
      }
    }
    reader.readAsText(file)
    
    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Top Action Bar */}
      <div className="flex items-center justify-between p-4 border-b border-freya-border bg-freya-bg-secondary">
        <div className="flex items-center gap-4">
          {/* Program Selector */}
          <div className="flex items-center gap-2 bg-freya-bg-primary rounded-lg p-1">
            {PROGRAMS.map((prog) => {
              const Icon = prog.icon
              const isCurrent = continuousMode && continuousPhase === prog.id
              return (
                <button
                  key={prog.id}
                  onClick={() => !isRunning && !continuousMode && setSelectedProgram(prog.id)}
                  disabled={isRunning || continuousMode}
                  className={clsx(
                    'flex items-center gap-2 px-4 py-2 rounded-md transition-all relative',
                    selectedProgram === prog.id && !continuousMode
                      ? 'bg-freya-bg-tertiary text-freya-text-primary shadow-sm'
                      : 'text-freya-text-secondary hover:text-freya-text-primary',
                    (isRunning || continuousMode) && 'opacity-50 cursor-not-allowed',
                    isCurrent && 'ring-2 ring-freya-accent-blue'
                  )}
                >
                  <Icon className={clsx('w-4 h-4', prog.color)} />
                  <span className="font-medium">{prog.name}</span>
                  {isCurrent && (
                    <span className="absolute -top-1 -right-1 w-2 h-2 bg-freya-accent-blue rounded-full animate-pulse" />
                  )}
                </button>
              )
            })}
          </div>

          {/* Continuous Mode Toggle */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setContinuousMode(!continuousMode)}
              disabled={isRunning}
              className={clsx(
                'flex items-center gap-2 px-3 py-1.5 rounded-md text-sm transition-all',
                continuousMode
                  ? 'bg-freya-accent-purple/20 text-freya-accent-purple border border-freya-accent-purple/50'
                  : 'bg-freya-bg-primary text-freya-text-secondary hover:text-freya-text-primary',
                isRunning && 'opacity-50 cursor-not-allowed'
              )}
            >
              <Repeat className="w-4 h-4" />
              Continuous
            </button>
            
            {continuousMode && (
              <div className="flex items-center gap-1 text-xs text-freya-text-muted">
                <ArrowRight className="w-3 h-3" />
                <span>Fast → Standard → Advanced → Fine-tuning</span>
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Import Button */}
          <button
            onClick={() => setShowImportDialog(true)}
            className="btn-ghost p-2"
            title="Import Benchmarks"
          >
            <Upload className="w-5 h-5" />
          </button>
          
          {/* Settings Toggle */}
          <button
            onClick={() => setShowSettings(!showSettings)}
            className={clsx(
              'btn-ghost p-2',
              showSettings && 'bg-freya-bg-tertiary'
            )}
          >
            <Settings2 className="w-5 h-5" />
          </button>

          {/* Start/Stop Button */}
          {isRunning ? (
            <div className="flex items-center gap-2">
              {continuousMode && (
                <button
                  onClick={() => setAutoAdvance(!autoAdvance)}
                  className={clsx(
                    'btn-ghost p-2',
                    !autoAdvance && 'bg-freya-accent-yellow/20 text-freya-accent-yellow'
                  )}
                  title={autoAdvance ? 'Pause after current phase' : 'Resume auto-advance'}
                >
                  {autoAdvance ? <Pause className="w-4 h-4" /> : <SkipForward className="w-4 h-4" />}
                </button>
              )}
              <button
                onClick={() => stopMutation.mutate()}
                disabled={stopMutation.isPending}
                className="btn-danger flex items-center gap-2"
              >
                <Square className="w-4 h-4" />
                Stop
              </button>
            </div>
          ) : continuousMode ? (
            <button
              onClick={startContinuousBenchmark}
              disabled={startMutation.isPending}
              className="btn-primary flex items-center gap-2"
            >
              <Repeat className="w-4 h-4" />
              Start Continuous
            </button>
          ) : (
            <button
              onClick={() => startMutation.mutate(selectedProgram)}
              disabled={startMutation.isPending}
              className="btn-primary flex items-center gap-2"
            >
              <Play className="w-4 h-4" />
              Start Benchmark
            </button>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden flex">
        {/* Left Panel - Progress & Results */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Progress Card (when running) */}
          {isRunning && status && (
            <div className="card p-6 animate-fade-in">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="relative">
                    <RefreshCw className="w-6 h-6 text-freya-accent-blue animate-spin" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-freya-text-primary">
                      {continuousMode ? 'Continuous Benchmark' : 'Benchmark'} Running
                    </h3>
                    <p className="text-sm text-freya-text-secondary">
                      Phase: <span className="text-freya-accent-cyan">{status.phase}</span>
                      {continuousMode && (
                        <span className="ml-2 text-freya-accent-purple">
                          ({continuousPhase})
                        </span>
                      )}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-freya-accent-blue">
                    {Math.min(100, Math.round(status.progress_percent))}%
                  </div>
                  <p className="text-sm text-freya-text-muted">
                    Model {status.model_index}/{status.total_models}
                  </p>
                  {estimatedTimeRemaining && (
                    <p className="text-xs text-freya-accent-cyan mt-1">
                      {estimatedTimeRemaining}
                    </p>
                  )}
                </div>
              </div>

              {/* Continuous Mode Progress Indicator */}
              {continuousMode && (
                <div className="flex items-center gap-2 mb-4">
                  {PROGRAMS.map((prog, idx) => (
                    <div key={prog.id} className="flex items-center">
                      <div className={clsx(
                        'w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium',
                        continuousPhase === prog.id
                          ? 'bg-freya-accent-blue text-white'
                          : (PROGRAMS.findIndex(p => p.id === continuousPhase) > idx)
                            ? 'bg-freya-accent-green/20 text-freya-accent-green'
                            : 'bg-freya-bg-tertiary text-freya-text-muted'
                      )}>
                        {(PROGRAMS.findIndex(p => p.id === continuousPhase) > idx) ? (
                          <CheckCircle2 className="w-4 h-4" />
                        ) : (
                          prog.order
                        )}
                      </div>
                      {idx < PROGRAMS.length - 1 && (
                        <div className={clsx(
                          'w-8 h-0.5 mx-1',
                          (PROGRAMS.findIndex(p => p.id === continuousPhase) > idx)
                            ? 'bg-freya-accent-green'
                            : 'bg-freya-border'
                        )} />
                      )}
                    </div>
                  ))}
                  <div className="flex items-center">
                    <div className="w-8 h-0.5 mx-1 bg-freya-border" />
                    <div className={clsx(
                      'w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium',
                      continuousPhase === 'fine-tuning'
                        ? 'bg-freya-accent-purple text-white'
                        : 'bg-freya-bg-tertiary text-freya-text-muted'
                    )}>
                      <Sliders className="w-4 h-4" />
                    </div>
                  </div>
                </div>
              )}

              {/* Progress Bar */}
              <div className="progress-bar mb-4">
                <div 
                  className="progress-fill"
                  style={{ width: `${status.progress_percent}%` }}
                />
              </div>

              {/* Current Status */}
              <div className="grid grid-cols-5 gap-4 text-sm">
                <div className="bg-freya-bg-primary rounded-lg p-3">
                  <div className="text-freya-text-muted mb-1">Role</div>
                  <div className="font-medium text-freya-text-primary capitalize">{status.role}</div>
                </div>
                <div className="bg-freya-bg-primary rounded-lg p-3">
                  <div className="text-freya-text-muted mb-1">Model</div>
                  <div className="font-medium text-freya-text-primary truncate" title={status.model}>
                    {status.model}
                  </div>
                </div>
                <div className="bg-freya-bg-primary rounded-lg p-3">
                  <div className="text-freya-text-muted mb-1">Step</div>
                  <div className="font-medium text-freya-text-primary">
                    {status.step_index}/{status.total_steps}
                  </div>
                </div>
                <div className="bg-freya-bg-primary rounded-lg p-3">
                  <div className="text-freya-text-muted mb-1">Program</div>
                  <div className="font-medium text-freya-text-primary">{status.program}</div>
                </div>
                <div className="bg-freya-bg-primary rounded-lg p-3">
                  <div className="text-freya-text-muted mb-1">ETA</div>
                  <div className="font-medium text-freya-accent-cyan">
                    {estimatedTimeRemaining || 'Calculating...'}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Billboard - Best Models with Manual Override */}
          <div className="card">
            <div className="flex items-center justify-between p-4 border-b border-freya-border">
              <div className="flex items-center gap-2">
                <Award className="w-5 h-5 text-freya-accent-yellow" />
                <h3 className="font-semibold text-freya-text-primary">Best Models by Role</h3>
                {modelOverrides.length > 0 && (
                  <span className="badge badge-purple">{modelOverrides.length} overrides</span>
                )}
              </div>
              <div className="flex items-center gap-2">
                {modelOverrides.length > 0 && (
                  <button
                    onClick={() => setModelOverrides([])}
                    className="btn-ghost text-sm"
                  >
                    Reset Overrides
                  </button>
                )}
                {billboard && billboard.length > 0 && (
                  <button
                    onClick={() => applyRoutingMutation.mutate()}
                    disabled={applyRoutingMutation.isPending}
                    className="btn-secondary text-sm flex items-center gap-2"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    Apply as Routing
                  </button>
                )}
              </div>
            </div>

            <div className="p-4">
              {Object.keys(bestByRole).length > 0 || modelOverrides.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                  {ROLES.map((role) => {
                    const best = bestByRole[role]
                    const override = modelOverrides.find(o => o.role === role)
                    const effectiveModel = getEffectiveModel(role)
                    const isEditing = editingRole === role

                    return (
                      <div
                        key={role}
                        className={clsx(
                          'bg-freya-bg-primary rounded-lg p-4 border transition-colors',
                          override
                            ? 'border-freya-accent-purple/50'
                            : 'border-freya-border hover:border-freya-border-light'
                        )}
                      >
                        <div className="flex items-center justify-between mb-3">
                          <span className="text-sm font-medium text-freya-accent-blue capitalize">
                            {role}
                          </span>
                          <div className="flex items-center gap-1">
                            {override && (
                              <span className="badge badge-purple text-xs">Manual</span>
                            )}
                            {best && (
                              <span className={clsx(
                                'badge',
                                best.score >= 80 ? 'badge-green' :
                                best.score >= 60 ? 'badge-yellow' : 'badge-red'
                              )}>
                                {best.score.toFixed(0)}
                              </span>
                            )}
                          </div>
                        </div>
                        
                        {isEditing ? (
                          <div className="space-y-2">
                            <select
                              className="w-full bg-freya-bg-secondary border border-freya-border rounded px-2 py-1 text-sm"
                              value={override?.model || best?.model || ''}
                              onChange={(e) => setModelOverride(role, e.target.value)}
                            >
                              <option value="">Select model...</option>
                              {models?.map(m => (
                                <option key={m.name} value={m.name}>{m.name}</option>
                              ))}
                            </select>
                            <div className="flex gap-2">
                              <button
                                onClick={() => setEditingRole(null)}
                                className="btn-ghost text-xs flex-1"
                              >
                                Cancel
                              </button>
                              {override && (
                                <button
                                  onClick={() => {
                                    clearModelOverride(role)
                                    setEditingRole(null)
                                  }}
                                  className="btn-ghost text-xs flex-1 text-freya-accent-red"
                                >
                                  Reset
                                </button>
                              )}
                            </div>
                          </div>
                        ) : (
                          <>
                            <div 
                              className="font-medium text-freya-text-primary truncate mb-2 cursor-pointer hover:text-freya-accent-blue"
                              onClick={() => setEditingRole(role)}
                              title={effectiveModel || 'Click to select'}
                            >
                              {effectiveModel || 'No model selected'}
                              <Edit3 className="w-3 h-3 inline ml-2 opacity-50" />
                            </div>
                            {best && (
                              <div className="flex items-center gap-2 text-xs text-freya-text-muted">
                                <Clock className="w-3 h-3" />
                                <span>{(best.latency_ms / 1000).toFixed(1)}s</span>
                              </div>
                            )}
                          </>
                        )}
                      </div>
                    )
                  })}
                </div>
              ) : (
                <div className="text-center py-8 text-freya-text-muted">
                  <Target className="w-12 h-12 mx-auto mb-3 opacity-30" />
                  <p>No benchmark results yet</p>
                  <p className="text-sm mt-1">Run a benchmark to see the best models for each role</p>
                </div>
              )}
            </div>
          </div>

          {/* Detailed Results by Role - Enhanced */}
          <div className="card">
            <div className="flex items-center justify-between p-4 border-b border-freya-border">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-freya-accent-cyan" />
                <h3 className="font-semibold text-freya-text-primary">Detailed Results</h3>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowDetailedMetrics(!showDetailedMetrics)}
                  className={clsx(
                    'btn-ghost text-sm flex items-center gap-1',
                    showDetailedMetrics && 'text-freya-accent-cyan'
                  )}
                >
                  {showDetailedMetrics ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
                  Metrics
                </button>
              </div>
            </div>

            <div className="divide-y divide-freya-border">
              {ROLES.map((role) => {
                const roleHistory = historyByRole[role]
                const isExpanded = expandedRole === role
                const modelDetails = getModelDetails(role)
                const modelNames = Object.keys(modelDetails)

                return (
                  <div key={role}>
                    <button
                      onClick={() => setExpandedRole(isExpanded ? null : role)}
                      className="w-full flex items-center justify-between p-4 hover:bg-freya-bg-tertiary/50 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <span className="font-medium text-freya-text-primary capitalize">
                          {role}
                        </span>
                        <span className="badge badge-blue">
                          {roleHistory.length} runs
                        </span>
                        <span className="badge badge-purple">
                          {modelNames.length} models
                        </span>
                        {modelOverrides.find(o => o.role === role) && (
                          <span className="badge badge-yellow">Override</span>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-freya-text-muted">
                          {ROLE_DESCRIPTIONS[role]}
                        </span>
                        {isExpanded ? (
                          <ChevronUp className="w-5 h-5 text-freya-text-muted" />
                        ) : (
                          <ChevronDown className="w-5 h-5 text-freya-text-muted" />
                        )}
                      </div>
                    </button>

                    {isExpanded && (
                      <div className="px-4 pb-4 animate-slide-up space-y-4">
                        {/* Per-model breakdown */}
                        {modelNames.map((modelName) => {
                          const modelResults = modelDetails[modelName]
                          const stats = calculateModelStats(modelResults)
                          const isModelExpanded = expandedModel === `${role}-${modelName}`

                          return (
                            <div key={modelName} className="bg-freya-bg-primary rounded-lg overflow-hidden">
                              <button
                                onClick={() => setExpandedModel(isModelExpanded ? null : `${role}-${modelName}`)}
                                className="w-full flex items-center justify-between p-3 hover:bg-freya-bg-tertiary/50"
                              >
                                <div className="flex items-center gap-3">
                                  <Cpu className="w-4 h-4 text-freya-accent-cyan" />
                                  <span className="font-mono text-sm text-freya-text-primary">
                                    {modelName}
                                  </span>
                                  <span className="badge badge-blue text-xs">
                                    {modelResults.length} runs
                                  </span>
                                </div>
                                <div className="flex items-center gap-4">
                                  {stats && showDetailedMetrics && (
                                    <>
                                      <div className="text-xs text-freya-text-muted">
                                        Avg: <span className={clsx(
                                          'font-medium',
                                          stats.avgScore >= 80 ? 'text-freya-accent-green' :
                                          stats.avgScore >= 60 ? 'text-freya-accent-yellow' : 'text-freya-accent-red'
                                        )}>{stats.avgScore.toFixed(1)}</span>
                                      </div>
                                      <div className="text-xs text-freya-text-muted">
                                        σ: <span className="text-freya-text-secondary">{stats.stdDev.toFixed(1)}</span>
                                      </div>
                                      <div className="text-xs text-freya-text-muted">
                                        <Activity className="w-3 h-3 inline mr-1" />
                                        {stats.successRate.toFixed(0)}%
                                      </div>
                                    </>
                                  )}
                                  {isModelExpanded ? (
                                    <ChevronUp className="w-4 h-4 text-freya-text-muted" />
                                  ) : (
                                    <ChevronDown className="w-4 h-4 text-freya-text-muted" />
                                  )}
                                </div>
                              </button>

                              {isModelExpanded && stats && (
                                <div className="p-3 border-t border-freya-border space-y-3">
                                  {/* Stats Grid */}
                                  <div className="grid grid-cols-4 gap-3">
                                    <div className="bg-freya-bg-secondary rounded p-2">
                                      <div className="text-xs text-freya-text-muted">Avg Score</div>
                                      <div className={clsx(
                                        'font-semibold',
                                        stats.avgScore >= 80 ? 'text-freya-accent-green' :
                                        stats.avgScore >= 60 ? 'text-freya-accent-yellow' : 'text-freya-accent-red'
                                      )}>{stats.avgScore.toFixed(1)}</div>
                                    </div>
                                    <div className="bg-freya-bg-secondary rounded p-2">
                                      <div className="text-xs text-freya-text-muted">Score Range</div>
                                      <div className="text-freya-text-primary text-sm">
                                        {stats.minScore.toFixed(0)} - {stats.maxScore.toFixed(0)}
                                      </div>
                                    </div>
                                    <div className="bg-freya-bg-secondary rounded p-2">
                                      <div className="text-xs text-freya-text-muted">Std Dev</div>
                                      <div className="text-freya-text-primary font-semibold">{stats.stdDev.toFixed(2)}</div>
                                    </div>
                                    <div className="bg-freya-bg-secondary rounded p-2">
                                      <div className="text-xs text-freya-text-muted">Success Rate</div>
                                      <div className={clsx(
                                        'font-semibold',
                                        stats.successRate >= 90 ? 'text-freya-accent-green' :
                                        stats.successRate >= 70 ? 'text-freya-accent-yellow' : 'text-freya-accent-red'
                                      )}>{stats.successRate.toFixed(0)}%</div>
                                    </div>
                                  </div>

                                  {/* Latency Stats */}
                                  <div className="grid grid-cols-3 gap-3">
                                    <div className="bg-freya-bg-secondary rounded p-2">
                                      <div className="text-xs text-freya-text-muted flex items-center gap-1">
                                        <Timer className="w-3 h-3" /> Avg Latency
                                      </div>
                                      <div className="text-freya-text-primary font-semibold">
                                        {(stats.avgLatency / 1000).toFixed(2)}s
                                      </div>
                                    </div>
                                    <div className="bg-freya-bg-secondary rounded p-2">
                                      <div className="text-xs text-freya-text-muted">Min Latency</div>
                                      <div className="text-freya-accent-green font-semibold">
                                        {(stats.minLatency / 1000).toFixed(2)}s
                                      </div>
                                    </div>
                                    <div className="bg-freya-bg-secondary rounded p-2">
                                      <div className="text-xs text-freya-text-muted">Max Latency</div>
                                      <div className="text-freya-accent-red font-semibold">
                                        {(stats.maxLatency / 1000).toFixed(2)}s
                                      </div>
                                    </div>
                                  </div>

                                  {/* Individual Runs Table */}
                                  <div className="overflow-x-auto">
                                    <table className="table-freya text-xs">
                                      <thead>
                                        <tr>
                                          <th>Phase</th>
                                          <th>Score</th>
                                          <th>Latency</th>
                                          <th>Status</th>
                                        </tr>
                                      </thead>
                                      <tbody>
                                        {modelResults.slice(0, 10).map((result, idx) => (
                                          <tr key={idx}>
                                            <td className="text-freya-text-secondary">
                                              {result.phase}
                                            </td>
                                            <td>
                                              <span className={clsx(
                                                'font-medium',
                                                result.score >= 80 ? 'text-freya-accent-green' :
                                                result.score >= 60 ? 'text-freya-accent-yellow' : 'text-freya-accent-red'
                                              )}>
                                                {result.score.toFixed(1)}
                                              </span>
                                            </td>
                                            <td className="text-freya-text-secondary">
                                              {(result.latency_ms / 1000).toFixed(2)}s
                                            </td>
                                            <td>
                                              {result.status === 'ok' ? (
                                                <CheckCircle2 className="w-3 h-3 text-freya-accent-green" />
                                              ) : result.status === 'error' ? (
                                                <XCircle className="w-3 h-3 text-freya-accent-red" />
                                              ) : (
                                                <AlertTriangle className="w-3 h-3 text-freya-accent-yellow" />
                                              )}
                                            </td>
                                          </tr>
                                        ))}
                                      </tbody>
                                    </table>
                                  </div>
                                </div>
                              )}
                            </div>
                          )
                        })}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>

          {/* Imported Benchmarks */}
          {importedBenchmarks.length > 0 && (
            <div className="card">
              <div className="flex items-center gap-2 p-4 border-b border-freya-border">
                <Upload className="w-5 h-5 text-freya-accent-green" />
                <h3 className="font-semibold text-freya-text-primary">Imported Benchmarks</h3>
              </div>
              <div className="p-4">
                <div className="space-y-2">
                  {importedBenchmarks.map((imp, idx) => (
                    <div key={idx} className="flex items-center justify-between p-3 bg-freya-bg-primary rounded-lg">
                      <div className="flex items-center gap-3">
                        <FileJson className="w-4 h-4 text-freya-accent-cyan" />
                        <span className="font-medium text-freya-text-primary">{imp.name}</span>
                        <span className="badge badge-blue">{imp.format}</span>
                        <span className="badge badge-green">{imp.models} models</span>
                      </div>
                      <span className="text-xs text-freya-text-muted">
                        {new Date(imp.imported_at).toLocaleString()}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Panel - Settings (collapsible) */}
        {showSettings && (
          <div className="w-96 border-l border-freya-border bg-freya-bg-secondary p-4 overflow-y-auto animate-slide-in-right">
            <h3 className="font-semibold text-freya-text-primary mb-4">Benchmark Settings</h3>

            <div className="space-y-4">
              {/* Real-time Best Model */}
              {currentBestModel && status?.running && (
                <div className="bg-freya-accent-green/10 border border-freya-accent-green/30 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Star className="w-5 h-5 text-freya-accent-green" />
                    <h4 className="text-sm font-medium text-freya-accent-green">Current Best Model</h4>
                  </div>
                  <div className="text-freya-text-primary font-medium">{currentBestModel.model}</div>
                  <div className="text-xs text-freya-text-muted mt-1">
                    Role: {currentBestModel.role} • Score: {currentBestModel.score.toFixed(1)}
                  </div>
                </div>
              )}

              {/* Program Details */}
              <div className="bg-freya-bg-primary rounded-lg p-4">
                <h4 className="text-sm font-medium text-freya-text-secondary mb-3">
                  Selected Program
                </h4>
                {PROGRAMS.filter(p => p.id === selectedProgram).map((prog) => {
                  const Icon = prog.icon
                  return (
                    <div key={prog.id}>
                      <div className="flex items-center gap-2 mb-2">
                        <Icon className={clsx('w-5 h-5', prog.color)} />
                        <span className="font-medium text-freya-text-primary">{prog.name}</span>
                      </div>
                      <p className="text-sm text-freya-text-muted mb-3">{prog.description}</p>
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        <div className="bg-freya-bg-secondary rounded p-2">
                          <div className="text-freya-text-muted">Duration</div>
                          <div className="font-medium text-freya-text-primary">{prog.duration}</div>
                        </div>
                        <div className="bg-freya-bg-secondary rounded p-2">
                          <div className="text-freya-text-muted">Trials</div>
                          <div className="font-medium text-freya-text-primary">{trialsConfig[prog.id]}</div>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
              
              {/* Configurable Trials */}
              <div className="bg-freya-bg-primary rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-sm font-medium text-freya-text-secondary">
                    Trials per Category
                  </h4>
                  <button
                    onClick={() => setTrialsConfig({ 'bench-fast': 1, 'bench-standard': 5, 'bench-advanced': 5 })}
                    className="text-xs text-freya-accent-blue hover:underline flex items-center gap-1"
                  >
                    <RotateCcw className="w-3 h-3" />
                    Restore Default
                  </button>
                </div>
                <div className="space-y-3">
                  {PROGRAMS.map((prog) => (
                    <div key={prog.id} className="flex items-center justify-between">
                      <span className="text-sm text-freya-text-primary">{prog.name}</span>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => setTrialsConfig(prev => ({
                            ...prev,
                            [prog.id]: Math.max(1, prev[prog.id] - 1)
                          }))}
                          disabled={isRunning}
                          className="w-6 h-6 rounded bg-freya-bg-secondary flex items-center justify-center text-freya-text-muted hover:text-freya-text-primary disabled:opacity-50"
                        >
                          -
                        </button>
                        <span className="w-8 text-center text-sm font-medium text-freya-text-primary">
                          {trialsConfig[prog.id]}
                        </span>
                        <button
                          onClick={() => setTrialsConfig(prev => ({
                            ...prev,
                            [prog.id]: Math.min(20, prev[prog.id] + 1)
                          }))}
                          disabled={isRunning}
                          className="w-6 h-6 rounded bg-freya-bg-secondary flex items-center justify-center text-freya-text-muted hover:text-freya-text-primary disabled:opacity-50"
                        >
                          +
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Continuous Mode Settings */}
              {continuousMode && (
                <div className="bg-freya-bg-primary rounded-lg p-4">
                  <h4 className="text-sm font-medium text-freya-text-secondary mb-3">
                    Continuous Mode
                  </h4>
                  <div className="space-y-3">
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={autoAdvance}
                        onChange={(e) => setAutoAdvance(e.target.checked)}
                        className="rounded border-freya-border"
                      />
                      <span className="text-sm text-freya-text-primary">Auto-advance to next phase</span>
                    </label>
                    <div className="text-xs text-freya-text-muted p-2 bg-freya-bg-secondary rounded">
                      <Info className="w-3 h-3 inline mr-1" />
                      Phases: Fast → Standard → Advanced → Fine-tuning
                    </div>
                  </div>
                </div>
              )}

              {/* Roles Being Tested */}
              <div className="bg-freya-bg-primary rounded-lg p-4">
                <h4 className="text-sm font-medium text-freya-text-secondary mb-3">
                  Roles Being Tested
                </h4>
                <div className="flex flex-wrap gap-2">
                  {ROLES.map((role) => (
                    <span
                      key={role}
                      className={clsx(
                        'badge capitalize',
                        modelOverrides.find(o => o.role === role) ? 'badge-purple' : 'badge-blue'
                      )}
                    >
                      {role}
                    </span>
                  ))}
                </div>
              </div>

              {/* Import Section */}
              <div className="bg-freya-bg-primary rounded-lg p-4">
                <h4 className="text-sm font-medium text-freya-text-secondary mb-3">
                  Import External Benchmarks
                </h4>
                <p className="text-xs text-freya-text-muted mb-3">
                  Supported formats: MMLU, HellaSwag, custom JSON/CSV
                </p>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".json,.csv"
                  onChange={handleImport}
                  className="hidden"
                />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="btn-secondary w-full flex items-center justify-center gap-2"
                >
                  <Upload className="w-4 h-4" />
                  Import File
                </button>
              </div>

              {/* Export Section */}
              <div className="bg-freya-bg-primary rounded-lg p-4">
                <h4 className="text-sm font-medium text-freya-text-secondary mb-3">
                  Export Results
                </h4>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => exportResults('json')}
                    className="btn-secondary flex items-center justify-center gap-2"
                  >
                    <FileJson className="w-4 h-4" />
                    JSON
                  </button>
                  <button
                    onClick={() => exportResults('csv')}
                    className="btn-secondary flex items-center justify-center gap-2"
                  >
                    <FileSpreadsheet className="w-4 h-4" />
                    CSV
                  </button>
                </div>
              </div>
              
              {/* Delete Benchmarks Section */}
              <div className="bg-freya-bg-primary rounded-lg p-4">
                <h4 className="text-sm font-medium text-freya-text-secondary mb-3">
                  Manage Benchmarks
                </h4>
                <p className="text-xs text-freya-text-muted mb-3">
                  Clear benchmark results by category
                </p>
                <div className="space-y-2">
                  {models && models.length > 0 && (
                    <div className="space-y-2">
                      <label className="text-xs text-freya-text-muted">By Model:</label>
                      <div className="flex flex-wrap gap-1 max-h-32 overflow-y-auto">
                        {models.slice(0, 10).map((model) => (
                          <button
                            key={model.name}
                            onClick={() => {
                              // TODO: Implement delete by model API
                              console.log(`[Bench] Delete benchmarks for model: ${model.name}`)
                            }}
                            className="text-xs px-2 py-1 rounded bg-freya-bg-secondary text-freya-text-muted hover:text-freya-accent-red hover:bg-freya-accent-red/10 flex items-center gap-1"
                          >
                            <Trash2 className="w-3 h-3" />
                            {model.name.split(':')[0]}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                  <div className="pt-2 border-t border-freya-border">
                    <label className="text-xs text-freya-text-muted">By Program:</label>
                    <div className="flex gap-2 mt-2">
                      {PROGRAMS.map((prog) => (
                        <button
                          key={prog.id}
                          onClick={() => {
                            // TODO: Implement delete by program API
                            console.log(`[Bench] Delete benchmarks for program: ${prog.id}`)
                          }}
                          className="text-xs px-2 py-1 rounded bg-freya-bg-secondary text-freya-text-muted hover:text-freya-accent-red hover:bg-freya-accent-red/10 flex items-center gap-1"
                        >
                          <Trash2 className="w-3 h-3" />
                          {prog.name}
                        </button>
                      ))}
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      if (confirm('Are you sure you want to delete ALL benchmark results? This cannot be undone.')) {
                        // TODO: Implement clear all API
                        console.log('[Bench] Clearing all benchmark results')
                      }
                    }}
                    className="w-full mt-3 btn-ghost text-freya-accent-red flex items-center justify-center gap-2 border border-freya-accent-red/30"
                  >
                    <Trash2 className="w-4 h-4" />
                    Clear All Results
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Import Dialog */}
      {showImportDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-freya-bg-secondary rounded-lg p-6 max-w-md w-full mx-4 shadow-xl">
            <h3 className="text-lg font-semibold text-freya-text-primary mb-4">
              Import Benchmark Data
            </h3>
            <p className="text-sm text-freya-text-muted mb-4">
              Import benchmark results from external sources. Supported formats:
            </p>
            <ul className="text-sm text-freya-text-secondary mb-4 space-y-1">
              <li>• <strong>MMLU</strong> - Massive Multitask Language Understanding</li>
              <li>• <strong>HellaSwag</strong> - Commonsense reasoning benchmark</li>
              <li>• <strong>Custom JSON</strong> - Freya export format</li>
              <li>• <strong>CSV</strong> - Spreadsheet format</li>
            </ul>
            <input
              ref={fileInputRef}
              type="file"
              accept=".json,.csv"
              onChange={handleImport}
              className="hidden"
            />
            <div className="flex gap-3">
              <button
                onClick={() => fileInputRef.current?.click()}
                className="btn-primary flex-1 flex items-center justify-center gap-2"
              >
                <Upload className="w-4 h-4" />
                Select File
              </button>
              <button
                onClick={() => setShowImportDialog(false)}
                className="btn-ghost"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
