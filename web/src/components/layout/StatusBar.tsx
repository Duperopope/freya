import { useAppStore } from '../../stores/appStore'
import { Wifi, WifiOff, Server, Clock } from 'lucide-react'
import { useState, useEffect } from 'react'

export function StatusBar() {
  const { connected, modelsCount, benchProgress, wsConnected } = useAppStore()
  const [time, setTime] = useState(new Date())

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  return (
    <footer className="h-8 flex items-center justify-between px-4 bg-freya-bg-secondary border-t border-freya-border text-xs">
      {/* Left side */}
      <div className="flex items-center gap-4">
        {/* Connection status */}
        <div className="flex items-center gap-1.5">
          {connected ? (
            <Wifi className="w-3.5 h-3.5 text-freya-accent-green" />
          ) : (
            <WifiOff className="w-3.5 h-3.5 text-freya-accent-red" />
          )}
          <span className="text-freya-text-muted">
            Ollama: {connected ? 'Connected' : 'Disconnected'}
          </span>
        </div>

        {/* Models count */}
        {connected && (
          <div className="flex items-center gap-1.5 text-freya-text-muted">
            <Server className="w-3.5 h-3.5" />
            <span>{modelsCount} models</span>
          </div>
        )}

        {/* WebSocket */}
        <div className="flex items-center gap-1.5 text-freya-text-muted">
          <span className={`w-1.5 h-1.5 rounded-full ${wsConnected ? 'bg-freya-accent-green' : 'bg-freya-accent-red'}`} />
          <span>WebSocket: {wsConnected ? 'Live' : 'Offline'}</span>
        </div>
      </div>

      {/* Center - Activity */}
      {benchProgress?.running && (
        <div className="flex items-center gap-2 text-freya-accent-blue">
          <span className="w-1.5 h-1.5 rounded-full bg-freya-accent-blue animate-pulse" />
          <span>
            Benchmark: {benchProgress.phase} • {benchProgress.model} • {Math.round(benchProgress.progress_percent)}%
          </span>
        </div>
      )}

      {/* Right side */}
      <div className="flex items-center gap-4 text-freya-text-muted">
        <span>Freya v2.0.0</span>
        <div className="flex items-center gap-1.5">
          <Clock className="w-3.5 h-3.5" />
          <span>{time.toLocaleTimeString()}</span>
        </div>
      </div>
    </footer>
  )
}
