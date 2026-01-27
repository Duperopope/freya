import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Sidebar } from './components/layout/Sidebar'
import { Header } from './components/layout/Header'
import { StatusBar } from './components/layout/StatusBar'
import { ChatPage } from './components/chat/ChatPage'
import { BenchPage } from './components/bench/BenchPage'
import { BMADPage } from './components/bmad/BMADPage'
import { SettingsPage } from './components/settings/SettingsPage'
import { FilesPage } from './components/files/FilesPage'
import { WatchPage } from './components/watch/WatchPage'
import { useAppStore } from './stores/appStore'
import { useWebSocket } from './hooks/useWebSocket'

function App() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const { setConnected, setOllamaConnected, setSystemInfo } = useAppStore()

  // Initialize WebSocket connection
  useWebSocket()

  // Check API health on mount
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch('/api/health')
        const data = await res.json()
        setConnected(data.ready && data.ollama?.connected)
        // Update Ollama connection status with actual model count
        setOllamaConnected(data.ollama?.connected ?? false, data.ollama?.models_count ?? 0)
        
        // Fetch system info
        const sysRes = await fetch('/api/system')
        if (sysRes.ok) {
          const sysData = await sysRes.json()
          setSystemInfo(sysData)
        }
      } catch {
        setConnected(false)
      }
    }

    checkHealth()
    const interval = setInterval(checkHealth, 30000)
    return () => clearInterval(interval)
  }, [setConnected, setSystemInfo])

  return (
    <BrowserRouter>
      <div className="flex h-screen overflow-hidden bg-freya-bg-primary">
        {/* Sidebar */}
        <Sidebar 
          collapsed={sidebarCollapsed} 
          onToggle={() => setSidebarCollapsed(!sidebarCollapsed)} 
        />

        {/* Main content area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Header */}
          <Header />

          {/* Page content */}
          <main className="flex-1 overflow-hidden">
            <Routes>
              <Route path="/" element={<Navigate to="/chat" replace />} />
              <Route path="/chat" element={<ChatPage />} />
              <Route path="/bench" element={<BenchPage />} />
              <Route path="/bmad" element={<BMADPage />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="/files" element={<FilesPage />} />
              <Route path="/watch" element={<WatchPage />} />
            </Routes>
          </main>

          {/* Status bar */}
          <StatusBar />
        </div>
      </div>
    </BrowserRouter>
  )
}

export default App
