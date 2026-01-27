// web/src/components/launcher/LauncherPage.tsx
/**
 * Freya Launcher Page v2.5.5
 * 
 * One-click update and launch functionality:
 * - Check for updates from Git
 * - Pull latest changes
 * - Rebuild frontend
 * - Full bootstrap (update + build)
 * - View operation logs
 */

import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  Rocket, 
  RefreshCw, 
  GitBranch, 
  Hammer, 
  Play,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Terminal,
  Trash2,
  Clock,
  Cpu,
  ChevronDown,
  ChevronUp,
  Zap,
  Globe,
  Package
} from 'lucide-react'
import { clsx } from 'clsx'
import {
  getLauncherStatus,
  getLauncherLogs,
  checkForUpdates,
  triggerBuild,
  triggerBootstrap,
  triggerUpdateOnly,
  clearLauncherError,
  clearLauncherLogs,
  type LauncherLog
} from '../../lib/api'

export function LauncherPage() {
  const queryClient = useQueryClient()
  const logsEndRef = useRef<HTMLDivElement>(null)
  const [showLogs, setShowLogs] = useState(true)
  const [autoScroll, setAutoScroll] = useState(true)
  
  // Fetch launcher status
  const { data: status, isLoading: statusLoading } = useQuery({
    queryKey: ['launcher-status'],
    queryFn: getLauncherStatus,
    refetchInterval: 2000 // Poll every 2 seconds during operations
  })
  
  // Fetch logs
  const { data: logsData } = useQuery({
    queryKey: ['launcher-logs'],
    queryFn: () => getLauncherLogs(100),
    refetchInterval: 2000
  })
  
  // Mutations
  const checkUpdatesMutation = useMutation({
    mutationFn: checkForUpdates,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['launcher-status'] })
  })
  
  const buildMutation = useMutation({
    mutationFn: triggerBuild,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['launcher-status'] })
  })
  
  const bootstrapMutation = useMutation({
    mutationFn: triggerBootstrap,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['launcher-status'] })
  })
  
  const updateOnlyMutation = useMutation({
    mutationFn: triggerUpdateOnly,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['launcher-status'] })
  })
  
  const clearErrorMutation = useMutation({
    mutationFn: clearLauncherError,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['launcher-status'] })
  })
  
  const clearLogsMutation = useMutation({
    mutationFn: clearLauncherLogs,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['launcher-logs'] })
  })
  
  // Auto-scroll logs
  useEffect(() => {
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [logsData?.logs, autoScroll])
  
  const isOperationRunning = status?.is_updating || status?.is_building || status?.is_restarting
  const hasUpdates = status?.git_info?.has_updates
  const logs = logsData?.logs || []
  
  const formatDate = (dateStr: string | null | undefined) => {
    if (!dateStr) return 'Never'
    try {
      return new Date(dateStr).toLocaleString()
    } catch {
      return dateStr
    }
  }
  
  return (
    <div className="h-full overflow-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-xl bg-gradient-to-br from-freya-accent-purple/20 to-freya-accent-blue/20">
            <Rocket className="w-8 h-8 text-freya-accent-purple" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-freya-text-primary">Freya Launcher</h1>
            <p className="text-freya-text-muted">One-click update and launch</p>
          </div>
        </div>
        
        {/* Quick Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => checkUpdatesMutation.mutate()}
            disabled={isOperationRunning || checkUpdatesMutation.isPending}
            className={clsx(
              'flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all',
              'bg-freya-bg-tertiary hover:bg-freya-bg-elevated text-freya-text-secondary',
              'disabled:opacity-50 disabled:cursor-not-allowed'
            )}
          >
            <RefreshCw className={clsx('w-4 h-4', checkUpdatesMutation.isPending && 'animate-spin')} />
            Check Updates
          </button>
        </div>
      </div>
      
      {/* Error Banner */}
      {status?.error && (
        <div className="flex items-center justify-between p-4 rounded-xl bg-freya-accent-red/10 border border-freya-accent-red/30">
          <div className="flex items-center gap-3">
            <XCircle className="w-5 h-5 text-freya-accent-red" />
            <span className="text-freya-accent-red font-medium">{status.error}</span>
          </div>
          <button
            onClick={() => clearErrorMutation.mutate()}
            className="text-freya-text-muted hover:text-freya-text-primary transition-colors"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      )}
      
      {/* Main Actions Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* One-Click Bootstrap */}
        <div className="col-span-1 md:col-span-3">
          <button
            onClick={() => bootstrapMutation.mutate()}
            disabled={isOperationRunning}
            className={clsx(
              'w-full p-6 rounded-xl transition-all duration-300',
              'bg-gradient-to-r from-freya-accent-purple to-freya-accent-blue',
              'hover:from-freya-accent-purple/90 hover:to-freya-accent-blue/90',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              'group relative overflow-hidden'
            )}
          >
            <div className="absolute inset-0 bg-white/5 group-hover:bg-white/10 transition-colors" />
            <div className="relative flex items-center justify-center gap-4">
              {isOperationRunning ? (
                <>
                  <RefreshCw className="w-8 h-8 text-white animate-spin" />
                  <div className="text-left">
                    <h3 className="text-xl font-bold text-white">
                      {status?.current_operation || 'Processing...'}
                    </h3>
                    <div className="flex items-center gap-2 mt-1">
                      <div className="flex-1 h-2 bg-white/20 rounded-full overflow-hidden w-48">
                        <div 
                          className="h-full bg-white rounded-full transition-all duration-500"
                          style={{ width: `${status?.progress || 0}%` }}
                        />
                      </div>
                      <span className="text-white/80 text-sm">{status?.progress || 0}%</span>
                    </div>
                  </div>
                </>
              ) : (
                <>
                  <Zap className="w-8 h-8 text-white" />
                  <div className="text-left">
                    <h3 className="text-xl font-bold text-white">
                      {hasUpdates ? 'Update & Launch' : 'Launch Freya'}
                    </h3>
                    <p className="text-white/80 text-sm">
                      {hasUpdates 
                        ? `${status?.git_info?.behind} update(s) available - Click to update and rebuild`
                        : 'Pull latest changes, install dependencies, and build'}
                    </p>
                  </div>
                  {hasUpdates && (
                    <span className="absolute top-2 right-2 px-2 py-1 bg-freya-accent-green rounded-full text-xs text-white font-medium animate-pulse">
                      Updates Available
                    </span>
                  )}
                </>
              )}
            </div>
          </button>
        </div>
        
        {/* Update Only (Git + pip, skip npm) */}
        <ActionCard
          icon={GitBranch}
          title="Update Only"
          description="Git pull + pip (skip npm if built)"
          buttonText="Quick Update"
          onClick={() => updateOnlyMutation.mutate()}
          disabled={isOperationRunning || false}
          loading={updateOnlyMutation.isPending || false}
          color="blue"
        />
        
        {/* Build Frontend */}
        <ActionCard
          icon={Hammer}
          title="Build Frontend"
          description="npm install + build"
          buttonText="Build"
          onClick={() => buildMutation.mutate()}
          disabled={isOperationRunning || false}
          loading={buildMutation.isPending || status?.is_building || false}
          color="purple"
        />
        
        {/* System Status */}
        <ActionCard
          icon={Cpu}
          title="System"
          description={status?.system_info?.web_built ? 'Frontend OK' : 'Build needed'}
          buttonText="Refresh"
          onClick={() => queryClient.invalidateQueries({ queryKey: ['launcher-status'] })}
          disabled={false}
          loading={statusLoading}
          color="green"
        />
      </div>
      
      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Git Info */}
        <div className="p-4 rounded-xl bg-freya-bg-secondary border border-freya-border">
          <div className="flex items-center gap-2 mb-4">
            <GitBranch className="w-5 h-5 text-freya-accent-blue" />
            <h3 className="font-semibold text-freya-text-primary">Repository Status</h3>
          </div>
          
          {status?.git_info && (
            <div className="space-y-3 text-sm">
              <InfoRow 
                label="Branch" 
                value={status.git_info.branch}
                icon={<GitBranch className="w-4 h-4" />}
              />
              <InfoRow 
                label="Commit" 
                value={status.git_info.commit}
                mono
              />
              <InfoRow 
                label="Remote" 
                value={status.git_info.remote_url?.replace('https://github.com/', '')}
                icon={<Globe className="w-4 h-4" />}
              />
              <InfoRow 
                label="Status" 
                value={
                  status.git_info.has_updates 
                    ? `${status.git_info.behind} commit(s) behind` 
                    : 'Up to date'
                }
                valueClass={status.git_info.has_updates ? 'text-freya-accent-yellow' : 'text-freya-accent-green'}
              />
              {status.git_info.last_message && (
                <InfoRow 
                  label="Last commit" 
                  value={status.git_info.last_message}
                />
              )}
            </div>
          )}
        </div>
        
        {/* System Info */}
        <div className="p-4 rounded-xl bg-freya-bg-secondary border border-freya-border">
          <div className="flex items-center gap-2 mb-4">
            <Cpu className="w-5 h-5 text-freya-accent-purple" />
            <h3 className="font-semibold text-freya-text-primary">System Information</h3>
          </div>
          
          {status?.system_info && (
            <div className="space-y-3 text-sm">
              <InfoRow 
                label="Python" 
                value={status.system_info.python_version}
                icon={<Package className="w-4 h-4" />}
              />
              <InfoRow 
                label="Node.js" 
                value={status.system_info.node_version}
                valueClass={status.system_info.node_ok ? 'text-freya-accent-green' : 'text-freya-accent-red'}
              />
              <InfoRow 
                label="npm" 
                value={status.system_info.npm_version}
                valueClass={status.system_info.npm_ok ? 'text-freya-accent-green' : 'text-freya-accent-red'}
              />
              <InfoRow 
                label="Frontend" 
                value={status.system_info.web_built ? 'Built' : 'Not built'}
                valueClass={status.system_info.web_built ? 'text-freya-accent-green' : 'text-freya-accent-yellow'}
                icon={<Hammer className="w-4 h-4" />}
              />
              <InfoRow 
                label="Dependencies" 
                value={status.system_info.node_modules_installed ? 'Installed' : 'Not installed'}
                valueClass={status.system_info.node_modules_installed ? 'text-freya-accent-green' : 'text-freya-accent-yellow'}
                icon={<Package className="w-4 h-4" />}
              />
            </div>
          )}
        </div>
      </div>
      
      {/* Last Operations */}
      <div className="flex items-center gap-4 text-sm text-freya-text-muted">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4" />
          <span>Last update: {formatDate(status?.last_update)}</span>
        </div>
        <div className="flex items-center gap-2">
          <Hammer className="w-4 h-4" />
          <span>Last build: {formatDate(status?.last_build)}</span>
        </div>
      </div>
      
      {/* Logs Section */}
      <div className="rounded-xl bg-freya-bg-secondary border border-freya-border overflow-hidden">
        <div 
          className="flex items-center justify-between p-4 bg-freya-bg-tertiary cursor-pointer"
          onClick={() => setShowLogs(!showLogs)}
        >
          <div className="flex items-center gap-2">
            <Terminal className="w-5 h-5 text-freya-accent-blue" />
            <h3 className="font-semibold text-freya-text-primary">Operation Logs</h3>
            <span className="px-2 py-0.5 text-xs bg-freya-bg-elevated rounded-full text-freya-text-muted">
              {logs.length} entries
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={(e) => {
                e.stopPropagation()
                clearLogsMutation.mutate()
              }}
              className="p-1.5 hover:bg-freya-bg-elevated rounded-lg transition-colors"
              title="Clear logs"
            >
              <Trash2 className="w-4 h-4 text-freya-text-muted" />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation()
                setAutoScroll(!autoScroll)
              }}
              className={clsx(
                'p-1.5 rounded-lg transition-colors',
                autoScroll ? 'bg-freya-accent-blue/20 text-freya-accent-blue' : 'hover:bg-freya-bg-elevated text-freya-text-muted'
              )}
              title={autoScroll ? 'Auto-scroll enabled' : 'Auto-scroll disabled'}
            >
              <ChevronDown className="w-4 h-4" />
            </button>
            {showLogs ? (
              <ChevronUp className="w-4 h-4 text-freya-text-muted" />
            ) : (
              <ChevronDown className="w-4 h-4 text-freya-text-muted" />
            )}
          </div>
        </div>
        
        {showLogs && (
          <div className="max-h-64 overflow-y-auto p-4 font-mono text-sm bg-freya-bg-primary">
            {logs.length === 0 ? (
              <div className="text-freya-text-muted text-center py-4">
                No logs yet. Start an operation to see logs.
              </div>
            ) : (
              <div className="space-y-1">
                {logs.map((log, index) => (
                  <LogEntry key={index} log={log} />
                ))}
                <div ref={logsEndRef} />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

// Action Card Component
interface ActionCardProps {
  icon: React.ComponentType<{ className?: string }>
  title: string
  description: string
  buttonText: string
  onClick: () => void
  disabled: boolean
  loading: boolean
  color: 'blue' | 'purple' | 'green'
}

function ActionCard({ 
  icon: Icon, 
  title, 
  description, 
  buttonText, 
  onClick, 
  disabled, 
  loading,
  color 
}: ActionCardProps) {
  const colorClasses = {
    blue: 'from-freya-accent-blue/20 to-freya-accent-blue/5 border-freya-accent-blue/30',
    purple: 'from-freya-accent-purple/20 to-freya-accent-purple/5 border-freya-accent-purple/30',
    green: 'from-freya-accent-green/20 to-freya-accent-green/5 border-freya-accent-green/30'
  }
  
  const iconColors = {
    blue: 'text-freya-accent-blue',
    purple: 'text-freya-accent-purple',
    green: 'text-freya-accent-green'
  }
  
  return (
    <div className={clsx(
      'p-4 rounded-xl bg-gradient-to-br border transition-all',
      colorClasses[color]
    )}>
      <div className="flex items-start gap-3">
        <div className={clsx('p-2 rounded-lg bg-freya-bg-tertiary', iconColors[color])}>
          <Icon className="w-5 h-5" />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="font-semibold text-freya-text-primary">{title}</h4>
          <p className="text-sm text-freya-text-muted mt-0.5">{description}</p>
        </div>
      </div>
      <button
        onClick={onClick}
        disabled={disabled}
        className={clsx(
          'w-full mt-4 px-4 py-2 rounded-lg font-medium transition-all',
          'bg-freya-bg-tertiary hover:bg-freya-bg-elevated',
          'text-freya-text-primary',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          'flex items-center justify-center gap-2'
        )}
      >
        {loading ? (
          <RefreshCw className="w-4 h-4 animate-spin" />
        ) : (
          <Play className="w-4 h-4" />
        )}
        {buttonText}
      </button>
    </div>
  )
}

// Info Row Component
interface InfoRowProps {
  label: string
  value: string | undefined
  icon?: React.ReactNode
  mono?: boolean
  valueClass?: string
}

function InfoRow({ label, value, icon, mono, valueClass }: InfoRowProps) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-freya-text-muted">{label}</span>
      <div className={clsx(
        'flex items-center gap-1.5',
        valueClass || 'text-freya-text-primary',
        mono && 'font-mono'
      )}>
        {icon}
        <span className="truncate max-w-48">{value || 'N/A'}</span>
      </div>
    </div>
  )
}

// Log Entry Component
function LogEntry({ log }: { log: LauncherLog }) {
  const levelColors = {
    info: 'text-freya-accent-blue',
    warning: 'text-freya-accent-yellow',
    error: 'text-freya-accent-red',
    debug: 'text-freya-text-muted'
  }
  
  const levelIcons = {
    info: <CheckCircle2 className="w-3 h-3" />,
    warning: <AlertCircle className="w-3 h-3" />,
    error: <XCircle className="w-3 h-3" />,
    debug: <Terminal className="w-3 h-3" />
  }
  
  const level = log.level.toLowerCase() as keyof typeof levelColors
  
  return (
    <div className="flex items-start gap-2 py-0.5">
      <span className="text-freya-text-muted text-xs shrink-0">
        {new Date(log.timestamp).toLocaleTimeString()}
      </span>
      <span className={clsx('shrink-0', levelColors[level] || 'text-freya-text-muted')}>
        {levelIcons[level] || levelIcons.info}
      </span>
      <span className={clsx(
        'flex-1',
        levelColors[level] || 'text-freya-text-secondary'
      )}>
        {log.message}
      </span>
    </div>
  )
}
