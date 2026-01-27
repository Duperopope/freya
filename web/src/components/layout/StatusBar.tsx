import { useAppStore } from '../../stores/appStore'
import { Wifi, WifiOff, Server, Clock, Activity } from 'lucide-react'
import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import * as api from '../../lib/api'

export function StatusBar() {
  const { connected, modelsCount, benchProgress, wsConnected, ollamaConnected } = useAppStore()
  const [time, setTime] = useState(new Date())

  // Fetch models to get actual count
  const { data: models } = useQuery({
    queryKey: ['models'],
    queryFn: api.getModels,
    refetchInterval: 60000, // Refresh every minute
  })
  
  // Use models from query or fallback to store
  const actualModelsCount = models?.length ?? modelsCount

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  const isOllamaConnected = ollamaConnected || connected

  return (
    <footer className="h-8 flex items-center justify-between px-4 bg-freya-bg-secondary border-t border-freya-border text-xs">
      {/* Left side */}
      <div className="flex items-center gap-4">
        {/* Connection status */}
        <div className="flex items-center gap-1.5">
          {isOllamaConnected ? (
            <Wifi className="w-3.5 h-3.5 text-freya-accent-green" />
          ) : (
            <WifiOff className="w-3.5 h-3.5 text-freya-accent-red" />
          )}
          <span className="text-freya-text-muted">
            Ollama: {isOllamaConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>

        {/* Models count - always show, explain 0 */}
        <div className="flex items-center gap-1.5 text-freya-text-muted">
          <Server className="w-3.5 h-3.5" />
          <span title={actualModelsCount === 0 ? 'No models installed in Ollama. Run "ollama pull <model>" to install models.' : `${actualModelsCount} model(s) available`}>
            {actualModelsCount} {actualModelsCount === 1 ? 'model' : 'models'}
            {actualModelsCount === 0 && isOllamaConnected && (
              <span className="text-freya-accent-yellow ml-1">(pull required)</span>
            )}
          </span>
        </div>

        {/* WebSocket */}
        <div className="flex items-center gap-1.5 text-freya-text-muted">
          <span className={`w-1.5 h-1.5 rounded-full ${wsConnected ? 'bg-freya-accent-green' : 'bg-freya-accent-red'}`} />
          <span>WebSocket: {wsConnected ? 'Live' : 'Offline'}</span>
        </div>
      </div>

      {/* Center - Activity */}
      {benchProgress?.running && (
        <div className="flex items-center gap-2 text-freya-accent-blue">
          <Activity className="w-3.5 h-3.5 animate-pulse" />
          <span>
            Benchmark: {benchProgress.phase} • {benchProgress.model?.split(':')[0]} • {Math.min(100, Math.round(benchProgress.progress_percent))}%
          </span>
        </div>
      )}

      {/* Right side */}
      <div className="flex items-center gap-4 text-freya-text-muted">
        <span className="font-medium">Freya v2.3.5</span>
        <div className="flex items-center gap-1.5">
          <Clock className="w-3.5 h-3.5" />
          <span>{time.toLocaleTimeString()}</span>
        </div>
      </div>
    </footer>
  )
}
