import { useState, useRef, useEffect } from 'react'
import { Send, Loader2, Copy, Check, Settings2, Search, Shield } from 'lucide-react'
import { useQuery, useMutation } from '@tanstack/react-query'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { clsx } from 'clsx'
import * as api from '../../lib/api'

interface Message {
  id: string
  role: 'user' | 'assistant' | 'system' | 'tool'
  content: string
  timestamp: Date
  model?: string
  duration_ms?: number
}

export function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [selectedHat, setSelectedHat] = useState<string>('')
  const [showSettings, setShowSettings] = useState(false)
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Fetch available hats
  const { data: hats } = useQuery({
    queryKey: ['hats'],
    queryFn: api.getHats,
  })

  // Fetch models
  const { data: models } = useQuery({
    queryKey: ['models'],
    queryFn: api.getModels,
  })

  // Chat mutation
  const chatMutation = useMutation({
    mutationFn: api.generateChat,
    onSuccess: (data) => {
      const assistantMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: data.content,
        timestamp: new Date(),
        model: data.model,
        duration_ms: data.duration_ms,
      }
      setMessages(prev => [...prev, assistantMessage])
    },
    onError: (error) => {
      const errorMessage: Message = {
        id: Date.now().toString(),
        role: 'system',
        content: `Error: ${error.message}`,
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, errorMessage])
    },
  })

  // Search mutation
  const searchMutation = useMutation({
    mutationFn: (query: string) => api.webSearch(query),
    onSuccess: (results) => {
      const content = results.length > 0
        ? `### Search Results\n\n${results.map(r => `- **[${r.title}](${r.url})**\n  ${r.snippet}`).join('\n\n')}`
        : 'No results found.'
      
      const toolMessage: Message = {
        id: Date.now().toString(),
        role: 'tool',
        content,
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, toolMessage])
    },
  })

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Handle send
  const handleSend = () => {
    const text = input.trim()
    if (!text || chatMutation.isPending) return

    // Check for commands
    if (text.startsWith('/search ')) {
      const query = text.slice(8).trim()
      if (query) {
        const userMessage: Message = {
          id: Date.now().toString(),
          role: 'user',
          content: text,
          timestamp: new Date(),
        }
        setMessages(prev => [...prev, userMessage])
        setInput('')
        searchMutation.mutate(query)
      }
      return
    }

    // Regular chat
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, userMessage])
    setInput('')

    chatMutation.mutate({
      message: text,
      hat: selectedHat || undefined,
    })
  }

  // Copy message
  const copyMessage = async (content: string, id: string) => {
    await navigator.clipboard.writeText(content)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  // Handle key press
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex h-full">
      {/* Main chat area */}
      <div className="flex-1 flex flex-col">
        {/* Toolbar */}
        <div className="flex items-center gap-3 p-4 border-b border-freya-border bg-freya-bg-secondary">
          {/* Hat selector */}
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-freya-text-muted" />
            <select
              value={selectedHat}
              onChange={(e) => setSelectedHat(e.target.value)}
              className="input py-1.5 text-sm w-40"
            >
              <option value="">Default</option>
              {hats?.map((hat) => (
                <option key={hat.name} value={hat.name}>
                  {hat.name.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </option>
              ))}
            </select>
          </div>

          <div className="flex-1" />

          {/* Quick actions */}
          <button
            onClick={() => setShowSettings(!showSettings)}
            className={clsx('btn-ghost p-2', showSettings && 'bg-freya-bg-tertiary')}
          >
            <Settings2 className="w-4 h-4" />
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-16 h-16 rounded-full bg-freya-bg-tertiary flex items-center justify-center mb-4">
                <Send className="w-8 h-8 text-freya-accent-blue" />
              </div>
              <h2 className="text-xl font-semibold text-freya-text-primary mb-2">
                Start a Conversation
              </h2>
              <p className="text-freya-text-muted max-w-md">
                Ask Freya anything about development, security, or architecture.
                Use <code className="text-freya-accent-cyan">/search query</code> to search the web.
              </p>
              
              {/* Quick prompts */}
              <div className="flex flex-wrap gap-2 mt-6 max-w-lg justify-center">
                {[
                  'Explain BMAD methodology',
                  'Best practices for API security',
                  'Help me architect a microservice',
                ].map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => setInput(prompt)}
                    className="btn-secondary text-sm"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              className={clsx(
                'animate-slide-up',
                message.role === 'user' && 'flex justify-end'
              )}
            >
              <div
                className={clsx(
                  'max-w-3xl rounded-lg p-4',
                  message.role === 'user' && 'bg-freya-accent-blue/20 border border-freya-accent-blue/30',
                  message.role === 'assistant' && 'bg-freya-bg-tertiary border border-freya-border',
                  message.role === 'system' && 'bg-freya-accent-red/10 border border-freya-accent-red/30',
                  message.role === 'tool' && 'bg-freya-accent-purple/10 border border-freya-accent-purple/30'
                )}
              >
                {/* Header */}
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className={clsx(
                      'text-xs font-medium',
                      message.role === 'user' && 'text-freya-accent-blue',
                      message.role === 'assistant' && 'text-freya-accent-green',
                      message.role === 'system' && 'text-freya-accent-red',
                      message.role === 'tool' && 'text-freya-accent-purple'
                    )}>
                      {message.role === 'user' ? 'You' : 
                       message.role === 'assistant' ? 'Freya' :
                       message.role === 'tool' ? 'Tool' : 'System'}
                    </span>
                    {message.model && (
                      <span className="text-xs text-freya-text-muted">
                        • {message.model}
                      </span>
                    )}
                    {message.duration_ms && (
                      <span className="text-xs text-freya-text-muted">
                        • {(message.duration_ms / 1000).toFixed(1)}s
                      </span>
                    )}
                  </div>
                  
                  {/* Actions */}
                  <button
                    onClick={() => copyMessage(message.content, message.id)}
                    className="p-1 rounded hover:bg-freya-bg-primary/50 transition-colors"
                    title="Copy"
                  >
                    {copiedId === message.id ? (
                      <Check className="w-4 h-4 text-freya-accent-green" />
                    ) : (
                      <Copy className="w-4 h-4 text-freya-text-muted" />
                    )}
                  </button>
                </div>

                {/* Content */}
                <div className="prose-freya">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {message.content}
                  </ReactMarkdown>
                </div>
              </div>
            </div>
          ))}

          {/* Loading indicator */}
          {chatMutation.isPending && (
            <div className="flex items-center gap-2 text-freya-text-muted animate-pulse">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Freya is thinking...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        <div className="p-4 border-t border-freya-border bg-freya-bg-secondary">
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask Freya anything... (Ctrl+Enter to send)"
                className="textarea min-h-[80px] pr-12"
                disabled={chatMutation.isPending}
              />
              <button
                onClick={() => {
                  const query = prompt('Search query:')
                  if (query) {
                    setInput(`/search ${query}`)
                  }
                }}
                className="absolute right-3 top-3 p-1.5 rounded hover:bg-freya-bg-tertiary transition-colors"
                title="Web Search"
              >
                <Search className="w-4 h-4 text-freya-text-muted" />
              </button>
            </div>
            <button
              onClick={handleSend}
              disabled={!input.trim() || chatMutation.isPending}
              className="btn-primary h-fit self-end flex items-center gap-2"
            >
              {chatMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
              Send
            </button>
          </div>
          <p className="text-xs text-freya-text-muted mt-2">
            Press <kbd className="px-1.5 py-0.5 rounded bg-freya-bg-tertiary text-freya-text-secondary">Ctrl</kbd> + <kbd className="px-1.5 py-0.5 rounded bg-freya-bg-tertiary text-freya-text-secondary">Enter</kbd> to send
          </p>
        </div>
      </div>

      {/* Settings panel */}
      {showSettings && (
        <div className="w-80 border-l border-freya-border bg-freya-bg-secondary p-4 animate-slide-in-right">
          <h3 className="font-semibold text-freya-text-primary mb-4">Chat Settings</h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-freya-text-secondary mb-2">
                Available Models
              </label>
              <div className="space-y-1 max-h-48 overflow-y-auto">
                {models?.map((model) => (
                  <div
                    key={model.name}
                    className="flex items-center justify-between text-sm p-2 rounded bg-freya-bg-tertiary"
                  >
                    <span className="text-freya-text-primary">{model.name}</span>
                    {model.size_gb && (
                      <span className="text-freya-text-muted">{model.size_gb.toFixed(1)} GB</span>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm text-freya-text-secondary mb-2">
                Hat Presets
              </label>
              <div className="space-y-1">
                {hats?.map((hat) => (
                  <button
                    key={hat.name}
                    onClick={() => setSelectedHat(hat.name)}
                    className={clsx(
                      'w-full text-left p-2 rounded text-sm transition-colors',
                      selectedHat === hat.name
                        ? 'bg-freya-accent-blue/20 text-freya-accent-blue'
                        : 'bg-freya-bg-tertiary text-freya-text-primary hover:bg-freya-bg-elevated'
                    )}
                  >
                    <div className="font-medium">{hat.name.replace('_', ' ')}</div>
                    <div className="text-xs text-freya-text-muted">{hat.description}</div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
