import { useEffect, useRef, useCallback } from 'react'
import { useAppStore } from '../stores/appStore'

interface WSMessage {
  channel: string
  event: string
  data: Record<string, unknown>
  timestamp: string
}

type MessageHandler = (message: WSMessage) => void

// Global message handlers
const messageHandlers = new Set<MessageHandler>()

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<number>()
  const { setWsConnected, setBenchProgress, setBMADProgress } = useAppStore()

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws`)

    ws.onopen = () => {
      console.log('WebSocket connected')
      setWsConnected(true)
      
      // Subscribe to all channels
      ws.send(JSON.stringify({ action: 'subscribe', channel: 'bench' }))
      ws.send(JSON.stringify({ action: 'subscribe', channel: 'bmad' }))
      ws.send(JSON.stringify({ action: 'subscribe', channel: 'system' }))
    }

    ws.onmessage = (event) => {
      try {
        const message: WSMessage = JSON.parse(event.data)
        
        // Handle bench progress
        if (message.channel === 'bench' && message.event === 'progress') {
          setBenchProgress(message.data as never)
        }
        
        // Handle BMAD progress
        if (message.channel === 'bmad') {
          if (message.event === 'started') {
            setBMADProgress({
              running: true,
              current_agent: null,
              agents_completed: [],
              artifacts_generated: [],
            })
          } else if (message.event === 'agent_start') {
            setBMADProgress((prev) => ({
              ...prev!,
              current_agent: message.data.agent as string,
            }))
          } else if (message.event === 'agent_done') {
            setBMADProgress((prev) => ({
              ...prev!,
              agents_completed: [...(prev?.agents_completed || []), message.data.agent as string],
              artifacts_generated: [...(prev?.artifacts_generated || []), message.data.artifact as string],
            }))
          } else if (message.event === 'complete' || message.event === 'error') {
            setBMADProgress((prev) => ({
              ...prev!,
              running: false,
            }))
          }
        }

        // Notify all handlers
        messageHandlers.forEach(handler => handler(message))
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e)
      }
    }

    ws.onclose = () => {
      console.log('WebSocket disconnected')
      setWsConnected(false)
      
      // Reconnect after delay
      reconnectTimeoutRef.current = window.setTimeout(() => {
        connect()
      }, 3000)
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    wsRef.current = ws
  }, [setWsConnected, setBenchProgress, setBMADProgress])

  useEffect(() => {
    connect()

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [connect])

  return wsRef.current
}

// Hook to subscribe to specific message types
export function useWSMessage(handler: MessageHandler) {
  useEffect(() => {
    messageHandlers.add(handler)
    return () => {
      messageHandlers.delete(handler)
    }
  }, [handler])
}
