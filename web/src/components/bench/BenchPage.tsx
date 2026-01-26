/**
 * BenchPage - LLM Benchmarking Dashboard
 * 
 * Modern, professional interface for running and analyzing LLM benchmarks.
 * Features real-time progress tracking, result visualization, and routing configuration.
 */

import { useState, useEffect } from 'react'
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
  Download
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
}

const PROGRAMS: ProgramInfo[] = [
  {
    id: 'bench-fast',
    name: 'Fast Scan',
    description: 'Quick evaluation with single trial per model',
    icon: Zap,
    duration: '~5 min',
    trials: 1,
    color: 'text-freya-accent-green'
  },
  {
    id: 'bench-standard',
    name: 'Standard',
    description: 'Balanced benchmark with multiple trials',
    icon: Target,
    duration: '~20 min',
    trials: 5,
    color: 'text-freya-accent-blue'
  },
  {
    id: 'bench-advanced',
    name: 'Advanced',
    description: 'Comprehensive multi-phase benchmark',
    icon: Award,
    duration: '~60 min',
    trials: 5,
    color: 'text-freya-accent-purple'
  }
]

const ROLES = ['analyst', 'pm', 'architect', 'po', 'sm', 'dev', 'qa']

export function BenchPage() {
  const queryClient = useQueryClient()
  const { benchProgress, setBenchProgress } = useAppStore()
  const [selectedProgram, setSelectedProgram] = useState<BenchProgram>('bench-fast')
  const [expandedRole, setExpandedRole] = useState<string | null>(null)
  const [showSettings, setShowSettings] = useState(false)

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
  const { data: history } = useQuery({
    queryKey: ['benchHistory', selectedProgram],
    queryFn: () => api.getBenchHistory(selectedProgram, 100),
  })

  // Update store when status changes
  useEffect(() => {
    if (status) {
      setBenchProgress(status.running ? {
        running: status.running,
        program: status.program,
        phase: status.phase,
        role: status.role,
        model: status.model,
        progress_percent: status.progress_percent,
      } : null)
    }
  }, [status, setBenchProgress])

  // Start benchmark mutation
  const startMutation = useMutation({
    mutationFn: () => api.startBench(selectedProgram, true),
    onSuccess: () => {
      refetchStatus()
      queryClient.invalidateQueries({ queryKey: ['billboard'] })
    },
  })

  // Stop benchmark mutation
  const stopMutation = useMutation({
    mutationFn: api.stopBench,
    onSuccess: () => {
      refetchStatus()
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

  // Group history by role
  const historyByRole = ROLES.reduce((acc, role) => {
    acc[role] = history?.filter(h => h.role === role) || []
    return acc
  }, {} as Record<string, api.BenchResult[]>)

  // Get best model for each role from billboard
  const bestByRole = billboard?.reduce((acc, entry) => {
    if (!acc[entry.role] || entry.score > acc[entry.role].score) {
      acc[entry.role] = entry
    }
    return acc
  }, {} as Record<string, api.BillboardEntry>) || {}

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Top Action Bar */}
      <div className="flex items-center justify-between p-4 border-b border-freya-border bg-freya-bg-secondary">
        <div className="flex items-center gap-4">
          {/* Program Selector */}
          <div className="flex items-center gap-2 bg-freya-bg-primary rounded-lg p-1">
            {PROGRAMS.map((prog) => {
              const Icon = prog.icon
              return (
                <button
                  key={prog.id}
                  onClick={() => !isRunning && setSelectedProgram(prog.id)}
                  disabled={isRunning}
                  className={clsx(
                    'flex items-center gap-2 px-4 py-2 rounded-md transition-all',
                    selectedProgram === prog.id
                      ? 'bg-freya-bg-tertiary text-freya-text-primary shadow-sm'
                      : 'text-freya-text-secondary hover:text-freya-text-primary',
                    isRunning && 'opacity-50 cursor-not-allowed'
                  )}
                >
                  <Icon className={clsx('w-4 h-4', prog.color)} />
                  <span className="font-medium">{prog.name}</span>
                </button>
              )
            })}
          </div>

          {/* Program Info */}
          <div className="text-sm text-freya-text-muted">
            {PROGRAMS.find(p => p.id === selectedProgram)?.description}
            <span className="ml-2 text-freya-text-secondary">
              • {PROGRAMS.find(p => p.id === selectedProgram)?.duration}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
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
            <button
              onClick={() => stopMutation.mutate()}
              disabled={stopMutation.isPending}
              className="btn-danger flex items-center gap-2"
            >
              <Square className="w-4 h-4" />
              Stop Benchmark
            </button>
          ) : (
            <button
              onClick={() => startMutation.mutate()}
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
                    <h3 className="font-semibold text-freya-text-primary">Benchmark Running</h3>
                    <p className="text-sm text-freya-text-secondary">
                      Phase: <span className="text-freya-accent-cyan">{status.phase}</span>
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-freya-accent-blue">
                    {Math.round(status.progress_percent)}%
                  </div>
                  <p className="text-sm text-freya-text-muted">
                    Model {status.model_index}/{status.total_models}
                  </p>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="progress-bar mb-4">
                <div 
                  className="progress-fill"
                  style={{ width: `${status.progress_percent}%` }}
                />
              </div>

              {/* Current Status */}
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div className="bg-freya-bg-primary rounded-lg p-3">
                  <div className="text-freya-text-muted mb-1">Role</div>
                  <div className="font-medium text-freya-text-primary capitalize">{status.role}</div>
                </div>
                <div className="bg-freya-bg-primary rounded-lg p-3">
                  <div className="text-freya-text-muted mb-1">Model</div>
                  <div className="font-medium text-freya-text-primary truncate">{status.model}</div>
                </div>
                <div className="bg-freya-bg-primary rounded-lg p-3">
                  <div className="text-freya-text-muted mb-1">Step</div>
                  <div className="font-medium text-freya-text-primary">
                    {status.step_index}/{status.total_steps}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Billboard - Best Models */}
          <div className="card">
            <div className="flex items-center justify-between p-4 border-b border-freya-border">
              <div className="flex items-center gap-2">
                <Award className="w-5 h-5 text-freya-accent-yellow" />
                <h3 className="font-semibold text-freya-text-primary">Best Models by Role</h3>
              </div>
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

            <div className="p-4">
              {Object.keys(bestByRole).length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                  {ROLES.map((role) => {
                    const best = bestByRole[role]
                    if (!best) return null

                    return (
                      <div
                        key={role}
                        className="bg-freya-bg-primary rounded-lg p-4 border border-freya-border hover:border-freya-border-light transition-colors"
                      >
                        <div className="flex items-center justify-between mb-3">
                          <span className="text-sm font-medium text-freya-accent-blue capitalize">
                            {role}
                          </span>
                          <span className={clsx(
                            'badge',
                            best.score >= 80 ? 'badge-green' :
                            best.score >= 60 ? 'badge-yellow' : 'badge-red'
                          )}>
                            {best.score.toFixed(0)}
                          </span>
                        </div>
                        <div className="font-medium text-freya-text-primary truncate mb-2">
                          {best.model}
                        </div>
                        <div className="flex items-center gap-2 text-xs text-freya-text-muted">
                          <Clock className="w-3 h-3" />
                          <span>{(best.latency_ms / 1000).toFixed(1)}s</span>
                        </div>
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

          {/* Detailed Results by Role */}
          <div className="card">
            <div className="flex items-center gap-2 p-4 border-b border-freya-border">
              <TrendingUp className="w-5 h-5 text-freya-accent-cyan" />
              <h3 className="font-semibold text-freya-text-primary">Detailed Results</h3>
            </div>

            <div className="divide-y divide-freya-border">
              {ROLES.map((role) => {
                const roleHistory = historyByRole[role]
                const isExpanded = expandedRole === role

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
                      </div>
                      {isExpanded ? (
                        <ChevronUp className="w-5 h-5 text-freya-text-muted" />
                      ) : (
                        <ChevronDown className="w-5 h-5 text-freya-text-muted" />
                      )}
                    </button>

                    {isExpanded && roleHistory.length > 0 && (
                      <div className="px-4 pb-4 animate-slide-up">
                        <table className="table-freya">
                          <thead>
                            <tr>
                              <th>Model</th>
                              <th>Phase</th>
                              <th>Score</th>
                              <th>Latency</th>
                              <th>Status</th>
                            </tr>
                          </thead>
                          <tbody>
                            {roleHistory.slice(0, 10).map((result, idx) => (
                              <tr key={idx}>
                                <td className="font-mono text-freya-text-primary">
                                  {result.model}
                                </td>
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
                                  {(result.latency_ms / 1000).toFixed(1)}s
                                </td>
                                <td>
                                  {result.status === 'ok' ? (
                                    <CheckCircle2 className="w-4 h-4 text-freya-accent-green" />
                                  ) : result.status === 'error' ? (
                                    <XCircle className="w-4 h-4 text-freya-accent-red" />
                                  ) : (
                                    <AlertTriangle className="w-4 h-4 text-freya-accent-yellow" />
                                  )}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        {/* Right Panel - Settings (collapsible) */}
        {showSettings && (
          <div className="w-80 border-l border-freya-border bg-freya-bg-secondary p-4 overflow-y-auto animate-slide-in-right">
            <h3 className="font-semibold text-freya-text-primary mb-4">Benchmark Settings</h3>

            <div className="space-y-4">
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
                          <div className="font-medium text-freya-text-primary">{prog.trials}</div>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>

              {/* Roles Being Tested */}
              <div className="bg-freya-bg-primary rounded-lg p-4">
                <h4 className="text-sm font-medium text-freya-text-secondary mb-3">
                  Roles Being Tested
                </h4>
                <div className="flex flex-wrap gap-2">
                  {ROLES.map((role) => (
                    <span
                      key={role}
                      className="badge badge-blue capitalize"
                    >
                      {role}
                    </span>
                  ))}
                </div>
              </div>

              {/* Export Button */}
              <button className="btn-secondary w-full flex items-center justify-center gap-2">
                <Download className="w-4 h-4" />
                Export Results
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
