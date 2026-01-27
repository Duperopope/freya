import { useState, useRef, useEffect, useCallback } from 'react'
import { Send, Loader2, Copy, Check, Settings2, Shield, Globe, FileText, X, Paperclip, Image, Plus, Edit2, Trash2, RotateCcw, StopCircle, Users, Brain, MessageSquare, History, ChevronDown, ChevronRight, Search, Lightbulb, Rocket, TrendingUp, Download, Share2 } from 'lucide-react'
import { useQuery, useMutation } from '@tanstack/react-query'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { clsx } from 'clsx'
import * as api from '../../lib/api'
import { useAppStore } from '../../stores/appStore'

// Chat modes - Added 'research' and 'exchange' modes
type ChatMode = 'standard' | 'multi-agent' | 'reflection' | 'research' | 'exchange'

// Research phases
type ResearchPhase = 'idle' | 'searching' | 'analyzing' | 'briefing' | 'bmad_ready' | 'bmad'

// Research sub-modes
type ResearchSubMode = 'assisted' | 'autonomous'

interface Message {
  id: string
  role: 'user' | 'assistant' | 'system' | 'tool' | 'synthesis' | 'agent'
  content: string
  timestamp: Date
  model?: string
  duration_ms?: number
  attachments?: AttachedFile[]
  searchResults?: api.SearchResult[]
  agentName?: string // For multi-agent mode
  isReflection?: boolean // For reflection mode
  isCollapsed?: boolean // For collapsible agent responses
}

interface Conversation {
  id: string
  title: string
  messages: Message[]
  createdAt: Date
  updatedAt: Date
}

interface AttachedFile {
  name: string
  type: string
  size: number
  content?: string
  preview?: string
}

// Storage keys
const STORAGE_KEYS = {
  CONVERSATIONS: 'freya_chat_conversations',
  CURRENT_CONVERSATION: 'freya_chat_current',
  CHAT_SETTINGS: 'freya_chat_settings',
}

export function ChatPage() {
  // Conversation management
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null)
  const [showHistory, setShowHistory] = useState(false)
  
  // Current messages (synced with current conversation)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [selectedHat, setSelectedHat] = useState<string>('')
  const [showSettings, setShowSettings] = useState(false)
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const [webSearchEnabled, setWebSearchEnabled] = useState(true) // Default ON
  const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null)
  const [editContent, setEditContent] = useState('')
  const [customHats, setCustomHats] = useState<api.HatPreset[]>([])
  const [showCreateHat, setShowCreateHat] = useState(false)
  const [newHatName, setNewHatName] = useState('')
  const [newHatDescription, setNewHatDescription] = useState('')
  
  // Advanced chat modes
  const [chatMode, setChatMode] = useState<ChatMode>('standard')
  const [selectedModels, setSelectedModels] = useState<string[]>([]) // For multi-agent mode
  const [reflectionDepth, setReflectionDepth] = useState(2) // For reflection mode
  const [isProcessingMulti, setIsProcessingMulti] = useState(false)
  const [collapsedAgents, setCollapsedAgents] = useState<Set<string>>(new Set()) // Track collapsed agent messages
  
  // Research mode state
  const [researchPhase, setResearchPhase] = useState<ResearchPhase>('idle')
  const [, setResearchAnalysis] = useState<string | null>(null)
  const [researchSubMode, setResearchSubMode] = useState<ResearchSubMode>('assisted')
  const [autonomousRunning, setAutonomousRunning] = useState(false)
  const [autonomousIteration, setAutonomousIteration] = useState(0)
  const autonomousStopRef = useRef(false) // FIXED: Use ref for async stop check
  
  // Exchange mode state (two AIs conversing)
  const [exchangeModel1, setExchangeModel1] = useState<string>('')
  const [exchangeModel2, setExchangeModel2] = useState<string>('')
  const [exchangeTopic, setExchangeTopic] = useState('')
  const [exchangeRunning, setExchangeRunning] = useState(false)
  const [exchangeIterations, setExchangeIterations] = useState(10)
  const [exchangeUnlimited, setExchangeUnlimited] = useState(false)
  const exchangeStopRef = useRef(false)
  
  // Global store for research state persistence
  const { setResearchState } = useAppStore()
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const abortControllerRef = useRef<AbortController | null>(null)
  
  // Load conversations from localStorage on mount
  // FIXED: Properly validate currentConversationId exists in loaded conversations
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEYS.CONVERSATIONS)
      let loadedConversations: Conversation[] = []
      
      if (saved) {
        const parsed = JSON.parse(saved)
        // Convert date strings back to Date objects
        loadedConversations = parsed.map((c: any) => ({
          ...c,
          createdAt: new Date(c.createdAt),
          updatedAt: new Date(c.updatedAt),
          messages: c.messages.map((m: any) => ({
            ...m,
            timestamp: new Date(m.timestamp)
          }))
        }))
        setConversations(loadedConversations)
      }
      
      const currentId = localStorage.getItem(STORAGE_KEYS.CURRENT_CONVERSATION)
      if (currentId) {
        // IMPORTANT: Verify the conversation still exists before setting it
        const convExists = loadedConversations.some(c => c.id === currentId)
        if (convExists) {
          setCurrentConversationId(currentId)
        } else {
          // Conversation was deleted, clear the stale reference
          console.log('[Chat] Clearing stale conversation ID:', currentId)
          localStorage.removeItem(STORAGE_KEYS.CURRENT_CONVERSATION)
          setCurrentConversationId(null)
          setMessages([])
        }
      }
      
      // Load chat settings
      const settings = localStorage.getItem(STORAGE_KEYS.CHAT_SETTINGS)
      if (settings) {
        const { mode, models, depth } = JSON.parse(settings)
        if (mode) setChatMode(mode)
        if (models) setSelectedModels(models)
        if (depth) setReflectionDepth(depth)
      }
    } catch (e) {
      console.error('Failed to load chat history:', e)
      // On error, reset to clean state
      setConversations([])
      setCurrentConversationId(null)
      setMessages([])
    }
  }, [])
  
  // Load current conversation messages when conversation changes
  useEffect(() => {
    if (currentConversationId) {
      const conv = conversations.find(c => c.id === currentConversationId)
      if (conv) {
        setMessages(conv.messages)
      } else {
        // Conversation was deleted, reset state
        setMessages([])
        setCurrentConversationId(null)
        localStorage.removeItem(STORAGE_KEYS.CURRENT_CONVERSATION)
      }
    } else {
      // No current conversation, ensure messages are empty
      setMessages([])
    }
  }, [currentConversationId, conversations])
  
  // Save conversations to localStorage when they change
  useEffect(() => {
    // Always persist, even if empty (to properly handle deletions)
    localStorage.setItem(STORAGE_KEYS.CONVERSATIONS, JSON.stringify(conversations))
  }, [conversations])
  
  // Save current conversation ID
  useEffect(() => {
    if (currentConversationId) {
      localStorage.setItem(STORAGE_KEYS.CURRENT_CONVERSATION, currentConversationId)
    }
  }, [currentConversationId])
  
  // Save chat settings
  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.CHAT_SETTINGS, JSON.stringify({
      mode: chatMode,
      models: selectedModels,
      depth: reflectionDepth
    }))
  }, [chatMode, selectedModels, reflectionDepth])
  
  // Update conversation when messages change
  const updateConversation = useCallback((newMessages: Message[]) => {
    if (!currentConversationId) {
      // Create new conversation
      const newConv: Conversation = {
        id: Date.now().toString(),
        title: newMessages[0]?.content.slice(0, 50) || 'New Conversation',
        messages: newMessages,
        createdAt: new Date(),
        updatedAt: new Date()
      }
      setConversations(prev => [newConv, ...prev])
      setCurrentConversationId(newConv.id)
    } else {
      // Update existing conversation
      setConversations(prev => prev.map(c => 
        c.id === currentConversationId 
          ? { ...c, messages: newMessages, updatedAt: new Date() }
          : c
      ))
    }
  }, [currentConversationId])
  
  // Create new conversation
  const createNewConversation = () => {
    setMessages([])
    setCurrentConversationId(null)
    setShowHistory(false)
  }
  
  // Switch to a conversation
  const switchConversation = (convId: string) => {
    setCurrentConversationId(convId)
    setShowHistory(false)
  }
  
  // Delete a conversation - FIXED: properly clear localStorage and state
  const deleteConversation = (convId: string) => {
    // First check if we need to clear current conversation
    const isCurrent = currentConversationId === convId
    
    // Update conversations list
    setConversations(prev => {
      const filtered = prev.filter(c => c.id !== convId)
      // Immediately persist the deletion to localStorage
      localStorage.setItem(STORAGE_KEYS.CONVERSATIONS, JSON.stringify(filtered))
      return filtered
    })
    
    // If deleting current conversation, reset to clean state
    if (isCurrent) {
      setMessages([])
      setCurrentConversationId(null)
      localStorage.removeItem(STORAGE_KEYS.CURRENT_CONVERSATION)
    }
  }
  
  // Export conversation to JSON
  const exportConversation = (conv: Conversation) => {
    const exportData = {
      id: conv.id,
      title: conv.title,
      createdAt: conv.createdAt.toISOString(),
      updatedAt: conv.updatedAt.toISOString(),
      messages: conv.messages.map(m => ({
        role: m.role,
        content: m.content,
        timestamp: m.timestamp.toISOString(),
        model: m.model,
        agentName: m.agentName,
      })),
      exportedAt: new Date().toISOString(),
      freya_version: '2.5',
    }
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `freya-chat-${conv.title.slice(0, 30).replace(/[^a-zA-Z0-9]/g, '-')}-${Date.now()}.json`
    a.click()
    URL.revokeObjectURL(url)
  }
  
  // Generate shareable link (copies to clipboard)
  const shareConversation = async (conv: Conversation) => {
    // Create a base64 encoded version for sharing
    const shareData = {
      t: conv.title,
      m: conv.messages.slice(-10).map(m => ({ r: m.role, c: m.content.slice(0, 500) })), // Last 10 messages, truncated
    }
    const encoded = btoa(unescape(encodeURIComponent(JSON.stringify(shareData))))
    const shareUrl = `${window.location.origin}/chat?share=${encoded}`
    
    try {
      await navigator.clipboard.writeText(shareUrl)
      alert('Share link copied to clipboard!')
    } catch (e) {
      // Fallback: show the link
      prompt('Copy this share link:', shareUrl)
    }
  }

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
        searchResults: data.search_results,
      }
      setMessages(prev => {
        const newMessages = [...prev, assistantMessage]
        updateConversation(newMessages)
        return newMessages
      })
    },
    onError: (error) => {
      const errorMessage: Message = {
        id: Date.now().toString(),
        role: 'system',
        content: `Error: ${error.message}`,
        timestamp: new Date(),
      }
      setMessages(prev => {
        const newMessages = [...prev, errorMessage]
        updateConversation(newMessages)
        return newMessages
      })
    },
  })
  
  // Toggle agent message collapse state
  const toggleAgentCollapse = (messageId: string) => {
    setCollapsedAgents(prev => {
      const newSet = new Set(prev)
      if (newSet.has(messageId)) {
        newSet.delete(messageId)
      } else {
        newSet.add(messageId)
      }
      return newSet
    })
  }
  
  // Multi-agent mode: query multiple models and synthesize
  const handleMultiAgentChat = async (text: string, messageContent: string) => {
    if (selectedModels.length < 2) {
      // Show error in chat instead of alert
      const errorMsg: Message = {
        id: `error-${Date.now()}`,
        role: 'system',
        content: `⚠️ **Mode Multi-Agent**: Veuillez sélectionner au moins 2 modèles. Actuellement sélectionnés: ${selectedModels.length}`,
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, errorMsg])
      return
    }
    
    console.log('[Multi-Agent] Starting with models:', selectedModels)
    setIsProcessingMulti(true)
    const responses: { model: string; content: string; duration_ms: number; messageId: string }[] = []
    const errors: { model: string; error: string }[] = []
    const agentMessageIds: string[] = []
    
    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date(),
      attachments: attachedFiles.length > 0 ? [...attachedFiles] : undefined,
    }
    
    setMessages(prev => {
      const newMessages = [...prev, userMessage]
      updateConversation(newMessages)
      return newMessages
    })
    setInput('')
    setAttachedFiles([])
    
    // Add processing indicator with thinking animation
    const processingId = `processing-${Date.now()}`
    const processingMessage: Message = {
      id: processingId,
      role: 'system',
      content: `🧠 **Multi-Agent Processing** - Querying ${selectedModels.length} models...\n\n${selectedModels.map((m, i) => `${i === 0 ? '🔄' : '⏳'} ${m}`).join('\n')}`,
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, processingMessage])
    
    // Query each model sequentially
    for (let i = 0; i < selectedModels.length; i++) {
      const model = selectedModels[i]
      
      // Update processing message with visual indicators
      const statusLines = selectedModels.map((m, idx) => {
        if (idx < i) return `✅ ${m}`
        if (idx === i) return `🧠 ${m} (thinking...)`
        return `⏳ ${m}`
      }).join('\n')
      
      setMessages(prev => prev.map(m => 
        m.id === processingId 
          ? { ...m, content: `🧠 **Multi-Agent Processing** - Model ${i + 1}/${selectedModels.length}\n\n${statusLines}` }
          : m
      ))
      
      try {
        console.log(`[Multi-Agent] Querying model: ${model}`)
        const data = await api.generateChat({
          message: messageContent,
          model,
          hat: selectedHat || undefined,
          web_search: i === 0 ? webSearchEnabled : false, // Only search on first model
          max_tokens: 2048,
        })
        
        console.log(`[Multi-Agent] Response from ${model}:`, data.content.slice(0, 100))
        const agentMsgId = `agent-${Date.now()}-${model.replace(/[^a-zA-Z0-9]/g, '')}`
        responses.push({ model, content: data.content, duration_ms: data.duration_ms, messageId: agentMsgId })
        agentMessageIds.push(agentMsgId)
        
        // Add individual agent response (collapsed by default)
        const agentMessage: Message = {
          id: agentMsgId,
          role: 'agent',
          content: data.content,
          timestamp: new Date(),
          model,
          agentName: model.split(':')[0],
          duration_ms: data.duration_ms,
          isCollapsed: true, // Collapsed by default
        }
        
        // Collapse this agent by default
        setCollapsedAgents(prev => new Set([...prev, agentMsgId]))
        
        setMessages(prev => {
          // Keep processing indicator, add agent message
          const newMessages = [...prev, agentMessage]
          return newMessages
        })
      } catch (e) {
        const errorMsg = e instanceof Error ? e.message : 'Unknown error'
        console.error(`[Multi-Agent] Error from model ${model}:`, errorMsg)
        errors.push({ model, error: errorMsg })
      }
    }
    
    // Remove processing indicator
    setMessages(prev => prev.filter(m => m.id !== processingId))
    
    // Show errors for failed models
    if (errors.length > 0) {
      const errorSummary: Message = {
        id: `${Date.now()}-errors`,
        role: 'system',
        content: `⚠️ **${errors.length} model(s) failed:**\n${errors.map(e => `• ${e.model}: ${e.error}`).join('\n')}`,
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, errorSummary])
    }
    
    // Synthesize responses if we have at least 2 successful responses
    if (responses.length >= 2) {
      // Add synthesis processing indicator
      const synthProcessingMsg: Message = {
        id: 'synth-processing',
        role: 'system',
        content: `🔄 **Synthesis** - Cross-checking ${responses.length} agent responses...`,
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, synthProcessingMsg])
      
      const synthesisPrompt = `Tu es un agent de synthèse expert. Plusieurs agents IA ont fourni des réponses à la requête utilisateur. Ta tâche est de:
1. Vérifier et cross-checker les informations fournies par chaque agent
2. Identifier les points d'accord et de désaccord
3. Synthétiser une réponse complète et précise combinant les meilleures insights
4. Signaler toute contradiction ou incertitude

**Requête utilisateur:** "${text}"

**Réponses des agents:**
${responses.map(r => `### ${r.model} (${(r.duration_ms / 1000).toFixed(1)}s):\n${r.content}`).join('\n\n---\n\n')}

**Fournis une réponse de synthèse structurée avec:**
- ✅ Points d'accord entre agents
- ⚠️ Contradictions ou incertitudes
- 📝 Synthèse finale consolidée`
      
      try {
        const synthesisData = await api.generateChat({
          message: synthesisPrompt,
          system_prompt: 'Tu es un agent de synthèse méticuleux qui cross-check les informations et fournit des réponses précises et complètes. Réponds en français.',
        })
        
        const synthesisMessage: Message = {
          id: `${Date.now()}-synthesis`,
          role: 'synthesis',
          content: synthesisData.content,
          timestamp: new Date(),
          model: synthesisData.model,
          agentName: 'Synthèse Cross-Checkée',
          duration_ms: synthesisData.duration_ms,
        }
        
        setMessages(prev => {
          const filtered = prev.filter(m => m.id !== 'synth-processing')
          const newMessages = [...filtered, synthesisMessage]
          updateConversation(newMessages)
          return newMessages
        })
      } catch (e) {
        console.error('[Multi-Agent] Synthesis error:', e)
        const synthErrorMsg: Message = {
          id: `${Date.now()}-synth-error`,
          role: 'system',
          content: `❌ **Erreur de synthèse**: ${e instanceof Error ? e.message : 'Erreur inconnue'}`,
          timestamp: new Date(),
        }
        setMessages(prev => {
          const filtered = prev.filter(m => m.id !== 'synth-processing')
          const newMessages = [...filtered, synthErrorMsg]
          updateConversation(newMessages)
          return newMessages
        })
      }
    } else if (responses.length === 1) {
      // Only one model responded - expand it and show warning
      const singleModel = responses[0]
      setCollapsedAgents(prev => {
        const newSet = new Set(prev)
        newSet.delete(singleModel.messageId)
        return newSet
      })
      const msg: Message = {
        id: `${Date.now()}-single`,
        role: 'system',
        content: `⚠️ Un seul modèle a répondu (${singleModel.model}). La synthèse nécessite au moins 2 réponses. La réponse ci-dessus est affichée directement.`,
        timestamp: new Date(),
      }
      setMessages(prev => {
        const newMessages = [...prev, msg]
        updateConversation(newMessages)
        return newMessages
      })
    } else if (errors.length > 0 && responses.length === 0) {
      const msg: Message = {
        id: `${Date.now()}-all-errors`,
        role: 'system',
        content: `❌ **Tous les modèles ont échoué.** Veuillez vérifier que les modèles sont disponibles et réessayer.`,
        timestamp: new Date(),
      }
      setMessages(prev => {
        const newMessages = [...prev, msg]
        updateConversation(newMessages)
        return newMessages
      })
    }
    
    setIsProcessingMulti(false)
  }
  
  // Reflection mode: iterative self-improvement
  const handleReflectionChat = async (text: string, messageContent: string) => {
    setIsProcessingMulti(true)
    
    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date(),
      attachments: attachedFiles.length > 0 ? [...attachedFiles] : undefined,
    }
    
    setMessages(prev => {
      const newMessages = [...prev, userMessage]
      updateConversation(newMessages)
      return newMessages
    })
    setInput('')
    setAttachedFiles([])
    
    let currentResponse = ''
    
    // Initial response
    try {
      const initialData = await api.generateChat({
        message: messageContent,
        hat: selectedHat || undefined,
        web_search: webSearchEnabled,
      })
      currentResponse = initialData.content
      
      const initialMessage: Message = {
        id: `${Date.now()}-initial`,
        role: 'assistant',
        content: currentResponse,
        timestamp: new Date(),
        model: initialData.model,
        isReflection: false,
      }
      
      setMessages(prev => {
        const newMessages = [...prev, initialMessage]
        updateConversation(newMessages)
        return newMessages
      })
    } catch (e) {
      console.error('Initial response error:', e)
      setIsProcessingMulti(false)
      return
    }
    
    // Reflection iterations
    for (let i = 0; i < reflectionDepth; i++) {
      const reflectionPrompt = `You are a critical reviewer. Review and improve this response:

Original query: "${text}"

Current response:
${currentResponse}

Please:
1. Identify any errors, inaccuracies, or missing information
2. Check for logical inconsistencies
3. Suggest improvements for clarity and completeness
4. Provide an improved version

Reflection ${i + 1}/${reflectionDepth}:`
      
      try {
        const reflectionData = await api.generateChat({
          message: reflectionPrompt,
          system_prompt: 'You are a meticulous critic that improves responses through careful analysis.',
        })
        
        currentResponse = reflectionData.content
        
        const reflectionMessage: Message = {
          id: `${Date.now()}-reflection-${i}`,
          role: 'assistant',
          content: `**🔍 Reflection ${i + 1}/${reflectionDepth}:**\n\n${currentResponse}`,
          timestamp: new Date(),
          model: reflectionData.model,
          isReflection: true,
        }
        
        setMessages(prev => {
          const newMessages = [...prev, reflectionMessage]
          updateConversation(newMessages)
          return newMessages
        })
      } catch (e) {
        console.error(`Reflection ${i + 1} error:`, e)
        break
      }
    }
    
    setIsProcessingMulti(false)
  }
  
  // Research mode: Internet search → Analysis → BMAD Analyst briefing - IMPROVED with real-time logging
  const handleResearchChat = async (text: string) => {
    if (!text.trim()) return
    
    console.log('[Research] Starting research for:', text)
    setIsProcessingMulti(true)
    setResearchPhase('searching')
    
    // Helper to add progress logs
    const addProgressLog = (content: string) => {
      const logId = `research-log-${Date.now()}-${Math.random().toString(36).slice(2, 5)}`
      const logMsg: Message = {
        id: logId,
        role: 'system',
        content: content,
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, logMsg])
      return logId
    }
    
    // Helper to update a log message
    const updateLogMsg = (msgId: string, newContent: string) => {
      setMessages(prev => prev.map(m => 
        m.id === msgId ? { ...m, content: newContent } : m
      ))
    }
    
    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    }
    setMessages(prev => {
      const newMsgs = [...prev, userMessage]
      updateConversation(newMsgs)
      return newMsgs
    })
    setInput('')
    
    // Phase 1: Web Search for market research with detailed progress
    addProgressLog(`🔍 **Phase 1/4: Recherche Internet**\n\n📡 Lancement des recherches pour: "${text}"`)
    
    let allSearchResults: api.SearchResult[] = []
    
    try {
      console.log('[Research] Phase 1: Starting web search')
      // Search for market opportunities - with detailed progress for each search
      let marketSearch: api.SearchResult[] = []
      let techSearch: api.SearchResult[] = []
      let competitorSearch: api.SearchResult[] = []
      
      let searchLogId = addProgressLog(`_🔎 Recherche marché: "${text} market opportunity"..._`)
      try {
        marketSearch = await api.webSearch(`${text} application market opportunity 2024 2025`, 5)
        updateLogMsg(searchLogId, `✓ Opportunités marché: ${marketSearch.length} résultats`)
        console.log('[Research] Market search results:', marketSearch.length)
      } catch (e) {
        updateLogMsg(searchLogId, `⚠️ Recherche marché: échec (${e instanceof Error ? e.message : 'erreur'})`)
        console.warn('[Research] Market search failed:', e)
      }
      
      searchLogId = addProgressLog(`_🔎 Recherche technique: "no-code low-code"..._`)
      try {
        techSearch = await api.webSearch(`${text} technical feasibility no-code low-code`, 5)
        updateLogMsg(searchLogId, `✓ Faisabilité technique: ${techSearch.length} résultats`)
        console.log('[Research] Tech search results:', techSearch.length)
      } catch (e) {
        updateLogMsg(searchLogId, `⚠️ Recherche technique: échec`)
        console.warn('[Research] Tech search failed:', e)
      }
      
      searchLogId = addProgressLog(`_🔎 Recherche concurrence: "competitors alternatives"..._`)
      try {
        competitorSearch = await api.webSearch(`${text} competitors alternatives pricing`, 5)
        updateLogMsg(searchLogId, `✓ Analyse concurrentielle: ${competitorSearch.length} résultats`)
        console.log('[Research] Competitor search results:', competitorSearch.length)
      } catch (e) {
        updateLogMsg(searchLogId, `⚠️ Recherche concurrence: échec`)
        console.warn('[Research] Competitor search failed:', e)
      }
      
      allSearchResults = [...marketSearch, ...techSearch, ...competitorSearch]
      console.log('[Research] Total search results:', allSearchResults.length)
      
      // Summary of search results
      if (allSearchResults.length > 0) {
        addProgressLog(`📊 **Résultats compilés:** ${allSearchResults.length} sources trouvées\n\n${allSearchResults.slice(0, 5).map((r, i) => `${i+1}. ${r.title}`).join('\n')}`)
      } else {
        addProgressLog(`⚠️ Aucun résultat de recherche. L'analyse continuera avec les connaissances générales.`)
      }
    } catch (e) {
      console.error('[Research] Search error:', e)
      addProgressLog(`⚠️ **Recherche Internet limitée**\n\nErreur: ${e instanceof Error ? e.message : 'erreur'}. Continuation avec analyse générale...`)
    }
    
    // Phase 2: Analysis by Research Analyst
    console.log('[Research] Phase 2: Starting analysis')
    setResearchPhase('analyzing')
    
    addProgressLog(`\n🧠 **Phase 2/4: Analyse de Marché**`)
    const analysisMsgId = addProgressLog(`_💭 L'Analyste de Recherche examine ${allSearchResults.length} sources..._`)
    
    // Small delay to ensure UI updates
    await new Promise(resolve => setTimeout(resolve, 100))
    
    try {
      const analysisPrompt = `Tu es un Analyste de Recherche spécialisé en opportunités d'applications rentables et réalisables.

**Contexte de recherche:** "${text}"

**Données collectées:**
${allSearchResults.map(r => `- ${r.title}: ${r.snippet}`).join('\n')}

**Ta mission:**
1. 📊 **Analyse de Marché**: Identifie les opportunités concrètes
2. 💰 **Potentiel de Rentabilité**: Estime le potentiel (faible/moyen/élevé)
3. 🛠️ **Faisabilité Technique**: Évalue si c'est réalisable avec des outils no-code/low-code
4. 🎯 **Recommandation Top 3**: Liste les 3 meilleures idées d'applications à développer
5. ⚠️ **Risques et Défis**: Identifie les obstacles potentiels

Fournis une analyse structurée et actionnable.`

      const analysisData = await api.generateChat({
        message: analysisPrompt,
        system_prompt: 'Tu es un analyste de recherche de marché expert en applications SaaS et produits tech. Tu fournis des analyses détaillées et actionnables.',
        max_tokens: 2048,
      })
      
      // Store the analysis for briefing phase
      const analysisContentForBrief = analysisData.content
      setResearchAnalysis(analysisContentForBrief)
      
      // Update progress log
      updateLogMsg(analysisMsgId, `✓ Analyse terminée (${analysisData.model})`)
      
      const analysisResult: Message = {
        id: `research-result-${Date.now()}`,
        role: 'assistant',
        content: `## 📊 Rapport d'Analyse de Marché\n\n${analysisData.content}`,
        timestamp: new Date(),
        model: analysisData.model,
        agentName: 'Research Analyst',
      }
      
      // Add result
      setMessages(prev => [...prev, analysisResult])
      
      // Small delay between phases
      await new Promise(resolve => setTimeout(resolve, 300))
      
      // Phase 3: Briefing for BMAD Analyst (inside the try block to use analysisContentForBrief)
      console.log('[Research] Phase 3: Starting briefing')
      setResearchPhase('briefing')
      
      addProgressLog(`\n📋 **Phase 3/4: Préparation du Brief BMAD**`)
      const briefingMsgId = addProgressLog(`_✍️ Génération du brief projet..._`)
      
      // Small delay to ensure UI updates
      await new Promise(resolve => setTimeout(resolve, 100))
      
      try {
        const briefPrompt = `Basé sur cette analyse de marché:

${analysisContentForBrief}

Prépare un brief structuré pour l'Analyste BMAD qui va lancer le développement. Le brief doit inclure:

1. **Idée sélectionnée**: L'application la plus prometteuse
2. **Objectif principal**: Ce que l'app doit accomplir
3. **Utilisateurs cibles**: Qui va utiliser l'app
4. **Fonctionnalités clés**: 3-5 features essentielles
5. **Proposition de valeur**: Pourquoi les utilisateurs paieraient
6. **Stack technique suggéré**: Technologies recommandées (no-code si possible)
7. **MVP Timeline**: Estimation réaliste

Format: Brief concis et actionnable pour démarrer un projet BMAD.`

        const briefData = await api.generateChat({
          message: briefPrompt,
          system_prompt: 'Tu es un consultant stratégique qui prépare des briefs projets clairs et actionnables.',
          max_tokens: 1500,
        })
        
        console.log('[Research] Phase 4: BMAD ready')
        updateLogMsg(briefingMsgId, `✓ Brief généré (${briefData.model})`)
        
        const briefResult: Message = {
          id: `research-brief-${Date.now()}`,
          role: 'synthesis',
          content: `## 📋 Brief Projet BMAD\n\n${briefData.content}`,
          timestamp: new Date(),
          model: briefData.model,
          agentName: 'Strategic Brief',
        }
        
        // Update state for BMAD handoff
        setResearchState({
          isActive: true,
          phase: 'bmad_ready' as ResearchPhase,
          searchResults: allSearchResults,
          analysisReport: analysisContentForBrief,
          selectedIdea: briefData.content,
        })
        
        setMessages(prev => {
          const newMsgs = [...prev, briefResult]
          updateConversation(newMsgs)
          return newMsgs
        })
        
        // Final success message
        addProgressLog(`\n🚀 **Phase 4/4: Prêt pour BMAD**\n\n✅ Recherche complète! Allez dans l'onglet **BMAD Studio** pour lancer la génération du projet.`)
        
        setResearchPhase('bmad_ready')
      } catch (briefError) {
        console.error('[Research] Briefing error:', briefError)
        updateLogMsg(briefingMsgId, `❌ Brief échoué: ${briefError instanceof Error ? briefError.message : 'Erreur'}`)
      }
      
    } catch (e) {
      console.error('[Research] Analysis error:', e)
      updateLogMsg(analysisMsgId, `❌ Analyse échouée: ${e instanceof Error ? e.message : 'Erreur inconnue'}`)
    }
    
    setIsProcessingMulti(false)
  }
  
  // Autonomous Research mode: auto-search for app ideas, analyze, and send to BMAD
  // IMPROVED: Real-time detailed logging like modern LLMs
  // FIXED: Use ref for reliable async stop detection (closure-safe)
  const handleAutonomousResearch = async () => {
    autonomousStopRef.current = false // Reset stop flag
    setAutonomousRunning(true)
    setAutonomousIteration(1)
    setResearchPhase('searching')
    
    // Helper to add log messages with timestamps
    const addLog = (content: string, isProgress = false) => {
      const logMsg: Message = {
        id: `auto-log-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
        role: 'system',
        content: isProgress ? `_${content}_` : content,
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, logMsg])
      return logMsg.id
    }
    
    // Helper to update existing message
    const updateLog = (msgId: string, newContent: string) => {
      setMessages(prev => prev.map(m => 
        m.id === msgId ? { ...m, content: newContent } : m
      ))
    }
    
    addLog(`🤖 **Mode Autonome Activé**\n\n🔄 Initialisation de la recherche automatique d'opportunités...`)
    
    try {
      // Phase 1: Search for trending app ideas with detailed logging
      addLog(`📡 **Phase 1/4: Recherche Web**`)
      
      let searchId = addLog(`🔍 Recherche: "trending SaaS ideas 2024 2025 profitable"...`, true)
      const trendingSearch = await api.webSearch('trending SaaS ideas 2024 2025 profitable', 5)
      updateLog(searchId, `✓ Tendances SaaS: ${trendingSearch.length} résultats`)
      
      if (autonomousStopRef.current) { addLog(`⏹️ Arrêté par l'utilisateur`); return }
      
      searchId = addLog(`🔍 Recherche: "software market gaps opportunities"...`, true)
      const gapSearch = await api.webSearch('software market gaps opportunities underserved', 5)
      updateLog(searchId, `✓ Opportunités marché: ${gapSearch.length} résultats`)
      
      if (autonomousStopRef.current) { addLog(`⏹️ Arrêté par l'utilisateur`); return }
      
      searchId = addLog(`🔍 Recherche: "no-code low-code app ideas"...`, true)
      const techSearch = await api.webSearch('no-code low-code app ideas for developers', 5)
      updateLog(searchId, `✓ Apps no-code: ${techSearch.length} résultats`)
      
      const allResults = [...trendingSearch, ...gapSearch, ...techSearch]
      
      addLog(`📊 **Résultats compilés:** ${allResults.length} opportunités trouvées\n\n${allResults.slice(0, 6).map((r, i) => `${i+1}. ${r.title}`).join('\n')}`)
      
      if (autonomousStopRef.current) { addLog(`⏹️ Arrêté par l'utilisateur`); return }
      
      // Phase 2: AI selects the best idea
      setResearchPhase('analyzing')
      addLog(`🧠 **Phase 2/4: Analyse par IA**`)
      const analysisId = addLog(`💭 L'IA analyse les ${allResults.length} opportunités et sélectionne la meilleure...`, true)
      
      const selectionPrompt = `Based on these market opportunities, select the ONE most promising app idea that:
1. Has clear market demand
2. Is technically feasible with modern tools
3. Has a clear monetization path
4. Can be developed in a reasonable timeframe

Opportunities found:
${allResults.map(r => `- ${r.title}: ${r.snippet}`).join('\n')}

Respond with:
**Selected Idea:** [Name]
**Why:** [Brief justification]
**Target Users:** [Who]
**Key Features:** [3-5 bullet points]
**Monetization:** [Strategy]`

      const selectionData = await api.generateChat({
        message: selectionPrompt,
        system_prompt: 'You are an expert startup advisor selecting the most viable app idea. Be concise but thorough.',
        max_tokens: 1024,
      })
      
      updateLog(analysisId, `✓ Analyse terminée (${selectionData.model})`)
      
      if (autonomousStopRef.current) { addLog(`⏹️ Arrêté par l'utilisateur`); return }
      
      const ideaMsg: Message = {
        id: `auto-idea-${Date.now()}`,
        role: 'assistant',
        content: `## 🎯 Idée Sélectionnée\n\n${selectionData.content}`,
        timestamp: new Date(),
        model: selectionData.model,
        agentName: 'Autonomous Selector',
      }
      setMessages(prev => [...prev, ideaMsg])
      
      // Phase 3: Prepare BMAD brief
      setResearchPhase('briefing')
      addLog(`📋 **Phase 3/4: Génération du Brief BMAD**`)
      const briefId = addLog(`✍️ Création du brief structuré pour le pipeline BMAD...`, true)
      
      const briefPrompt = `Convert this selected idea into a BMAD project brief:

${selectionData.content}

Create a structured brief with:
1. **Project Name**: Clear, memorable name
2. **Goal**: One-sentence project goal
3. **User Stories**: 3 key user stories
4. **Technical Stack**: Recommended technologies
5. **MVP Scope**: What to include in v1
6. **Success Metrics**: How to measure success`

      const briefData = await api.generateChat({
        message: briefPrompt,
        system_prompt: 'You are a product strategist creating actionable project briefs. Be specific and practical.',
        max_tokens: 1500,
      })
      
      updateLog(briefId, `✓ Brief généré (${briefData.model})`)
      
      const briefMsg: Message = {
        id: `auto-brief-${Date.now()}`,
        role: 'synthesis',
        content: `## 📋 Brief BMAD Auto-Généré\n\n${briefData.content}`,
        timestamp: new Date(),
        model: briefData.model,
        agentName: 'Autonomous Brief',
      }
      setMessages(prev => [...prev, briefMsg])
      
      // Phase 4: Ready for BMAD
      addLog(`🚀 **Phase 4/4: Prêt pour BMAD**\n\n✅ Le brief a été préparé et sera transféré au pipeline BMAD.\n\n➡️ Allez dans l'onglet **BMAD Studio** pour lancer la génération du projet.`)
      
      // Update global state for BMAD integration
      setResearchState({
        isActive: true,
        phase: 'bmad_ready',
        searchResults: allResults,
        analysisReport: selectionData.content,
        selectedIdea: briefData.content,
      })
      
      setResearchPhase('bmad_ready')
      setAutonomousIteration(prev => prev + 1)
      
    } catch (e) {
      console.error('[Autonomous] Error:', e)
      const errorDetails = e instanceof Error 
        ? `${e.message}${e.stack ? '\n\nStack: ' + e.stack.split('\n').slice(0, 3).join('\n') : ''}`
        : 'Erreur inconnue'
      
      addLog(`❌ **Erreur en mode autonome:**\n\n\`\`\`\n${errorDetails}\n\`\`\`\n\n💡 **Solutions possibles:**\n- Vérifiez que Ollama est démarré\n- Vérifiez votre connexion internet pour la recherche web\n- Réessayez dans quelques secondes`)
    }
    
    setAutonomousRunning(false)
    setResearchPhase('idle')
  }
  
  // Exchange mode: Two AIs have natural conversation - IMPROVED with unlimited mode
  const handleExchangeChat = async () => {
    if (!exchangeModel1 || !exchangeModel2 || !exchangeTopic) {
      const errorMsg: Message = {
        id: `exchange-error-${Date.now()}`,
        role: 'system',
        content: `⚠️ Sélectionnez deux modèles et entrez un sujet.`,
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, errorMsg])
      return
    }
    
    if (exchangeModel1 === exchangeModel2) {
      const errorMsg: Message = {
        id: `exchange-error-${Date.now()}`,
        role: 'system',
        content: `⚠️ Sélectionnez deux modèles différents.`,
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, errorMsg])
      return
    }
    
    exchangeStopRef.current = false
    setExchangeRunning(true)
    
    const model1 = exchangeModel1
    const model2 = exchangeModel2
    const topic = exchangeTopic
    const maxIterations = exchangeUnlimited ? 999 : exchangeIterations
    
    // Conversation history for context
    const conversationHistory: { speaker: string; content: string }[] = []
    
    // Start message (compact)
    const startMsg: Message = {
      id: `exchange-start-${Date.now()}`,
      role: 'system',
      content: `💬 **${model1.split(':')[0]}** ↔ **${model2.split(':')[0]}** — "${topic}"${exchangeUnlimited ? ' (illimité)' : ''}`,
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, startMsg])
    
    const runExchange = async () => {
      let currentExchange = 0
      
      while (currentExchange < maxIterations && !exchangeStopRef.current) {
        const isModel1Turn = currentExchange % 2 === 0
        const currentModel = isModel1Turn ? model1 : model2
        const otherModel = isModel1Turn ? model2 : model1
        const modelShortName = currentModel.split(':')[0]
        
        // Discreet progress indicator (small, will be replaced)
        const progressId = `exchange-progress-${Date.now()}`
        setMessages(prev => [...prev, {
          id: progressId,
          role: 'system',
          content: `_${modelShortName} réfléchit..._`,
          timestamp: new Date(),
        }])
        
        try {
          // Build natural conversation context
          let prompt: string
          if (currentExchange === 0) {
            prompt = `Tu participes à une discussion sur: "${topic}".\n\nCommence la conversation avec ton point de vue. Sois naturel, engageant et direct. Pas de formalités inutiles.`
          } else {
            // Include recent conversation history for context
            const recentHistory = conversationHistory.slice(-6).map(h => 
              `**${h.speaker}:** ${h.content}`
            ).join('\n\n')
            
            prompt = `Tu es en pleine discussion avec ${otherModel.split(':')[0]} sur "${topic}".\n\n**Conversation récente:**\n${recentHistory}\n\n**Instructions:** Réponds naturellement comme dans une vraie conversation. Tu peux:\n- Rebondir sur ce qui a été dit\n- Apporter de nouvelles idées\n- Poser des questions\n- Exprimer un désaccord constructif\n- Approfondir un point intéressant\n\nSois concis (2-4 phrases max) mais pertinent.`
          }
          
          const response = await api.generateChat({
            message: prompt,
            model: currentModel,
            system_prompt: `Tu es ${modelShortName}, un participant engagé dans une conversation naturelle. Réponds de manière authentique et conversationnelle. Évite les phrases génériques. Sois direct et intéressant.`,
            max_tokens: 400,
          })
          
          // Add to conversation history
          conversationHistory.push({
            speaker: modelShortName,
            content: response.content
          })
          
          // Replace progress with actual response
          setMessages(prev => {
            const filtered = prev.filter(m => m.id !== progressId)
            const agentMsg: Message = {
              id: `exchange-${currentExchange}-${Date.now()}`,
              role: 'agent',
              content: response.content,
              timestamp: new Date(),
              model: currentModel,
              agentName: modelShortName,
              duration_ms: response.duration_ms,
            }
            return [...filtered, agentMsg]
          })
          
          currentExchange++
          
          // Small delay between exchanges
          await new Promise(resolve => setTimeout(resolve, 800))
          
        } catch (e) {
          console.error(`[Exchange] Error:`, e)
          setMessages(prev => {
            const filtered = prev.filter(m => m.id !== progressId)
            return [...filtered, {
              id: `exchange-error-${Date.now()}`,
              role: 'system',
              content: `⚠️ Erreur: ${e instanceof Error ? e.message : 'Erreur inconnue'}`,
              timestamp: new Date(),
            }]
          })
          break
        }
      }
      
      // End message
      const wasStoppedManually = exchangeStopRef.current
      setMessages(prev => [...prev, {
        id: `exchange-end-${Date.now()}`,
        role: 'synthesis',
        content: wasStoppedManually 
          ? `✋ **Conversation arrêtée** après ${conversationHistory.length} échanges.`
          : `✅ **Conversation terminée** — ${conversationHistory.length} échanges entre ${model1.split(':')[0]} et ${model2.split(':')[0]}.`,
        timestamp: new Date(),
        agentName: 'Fin',
      }])
      
      setExchangeRunning(false)
    }
    
    runExchange()
  }
  
  // Stop exchange
  const stopExchange = () => {
    exchangeStopRef.current = true
    setExchangeRunning(false)
  }

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
    if (!text || chatMutation.isPending || isProcessingMulti) return

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
        setMessages(prev => {
          const newMessages = [...prev, userMessage]
          updateConversation(newMessages)
          return newMessages
        })
        setInput('')
        searchMutation.mutate(query)
      }
      return
    }

    // Build context from attachments
    let messageContent = text
    if (attachedFiles.length > 0) {
      const fileContext = attachedFiles.map(f => {
        if (f.content) {
          return `\n\n--- Attached File: ${f.name} ---\n${f.content.slice(0, 10000)}${f.content.length > 10000 ? '\n... (truncated)' : ''}`
        }
        return `\n\n[Attached: ${f.name} (${f.type})]`
      }).join('')
      messageContent = text + fileContext
    }

    // Route to appropriate mode
    if (chatMode === 'multi-agent') {
      handleMultiAgentChat(text, messageContent)
      return
    }
    
    if (chatMode === 'reflection') {
      handleReflectionChat(text, messageContent)
      return
    }
    
    if (chatMode === 'research') {
      handleResearchChat(text)
      return
    }
    
    if (chatMode === 'exchange') {
      // Exchange mode uses its own topic input
      return
    }

    // Standard chat mode
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date(),
      attachments: attachedFiles.length > 0 ? [...attachedFiles] : undefined,
    }
    setMessages(prev => {
      const newMessages = [...prev, userMessage]
      updateConversation(newMessages)
      return newMessages
    })
    setInput('')
    setAttachedFiles([]) // Clear attachments after sending

    chatMutation.mutate({
      message: messageContent,
      hat: selectedHat || undefined,
      web_search: webSearchEnabled,
    })
  }
  
  // Handle file attachment
  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (!files || files.length === 0) return
    
    setIsUploading(true)
    
    try {
      for (const file of Array.from(files)) {
        const attached: AttachedFile = {
          name: file.name,
          type: file.type,
          size: file.size,
        }
        
        // Read text-based files
        if (file.type.startsWith('text/') || 
            file.name.endsWith('.md') || 
            file.name.endsWith('.json') ||
            file.name.endsWith('.py') ||
            file.name.endsWith('.js') ||
            file.name.endsWith('.ts') ||
            file.name.endsWith('.tsx') ||
            file.name.endsWith('.jsx') ||
            file.name.endsWith('.css') ||
            file.name.endsWith('.html') ||
            file.name.endsWith('.xml') ||
            file.name.endsWith('.yaml') ||
            file.name.endsWith('.yml') ||
            file.name.endsWith('.toml') ||
            file.name.endsWith('.ini') ||
            file.name.endsWith('.cfg') ||
            file.name.endsWith('.log') ||
            file.name.endsWith('.csv') ||
            file.name.endsWith('.sql')) {
          const content = await file.text()
          attached.content = content
        }
        
        // Create preview for images
        if (file.type.startsWith('image/')) {
          const reader = new FileReader()
          attached.preview = await new Promise((resolve) => {
            reader.onload = (e) => resolve(e.target?.result as string)
            reader.readAsDataURL(file)
          })
        }
        
        setAttachedFiles(prev => [...prev, attached])
      }
    } catch (error) {
      console.error('Failed to process file:', error)
    } finally {
      setIsUploading(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }
  
  // Remove attached file
  const removeAttachedFile = (index: number) => {
    setAttachedFiles(prev => prev.filter((_, i) => i !== index))
  }

  // Copy message
  const copyMessage = async (content: string, id: string) => {
    await navigator.clipboard.writeText(content)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  // Handle key press - Enter to send, Ctrl/Cmd+Enter for newline
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter') {
      if (e.ctrlKey || e.metaKey || e.shiftKey) {
        // Insert newline with Ctrl/Cmd/Shift+Enter
        e.preventDefault()
        const target = e.target as HTMLTextAreaElement
        const start = target.selectionStart
        const end = target.selectionEnd
        const newValue = input.slice(0, start) + '\n' + input.slice(end)
        setInput(newValue)
        // Set cursor position after newline
        setTimeout(() => {
          target.selectionStart = target.selectionEnd = start + 1
        }, 0)
        return
      }
      e.preventDefault()
      handleSend()
    }
  }

  // Cancel last message generation
  const cancelGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }
  }

  // Delete last message
  const deleteLastMessage = () => {
    if (messages.length > 0) {
      setMessages(prev => prev.slice(0, -1))
    }
  }

  // Edit message
  const startEditMessage = (msg: Message) => {
    setEditingMessageId(msg.id)
    setEditContent(msg.content)
  }

  // Save edited message (removes subsequent context)
  const saveEditedMessage = (msgId: string) => {
    const msgIndex = messages.findIndex(m => m.id === msgId)
    if (msgIndex >= 0) {
      setMessages(prev => {
        const updated = [...prev]
        updated[msgIndex] = { ...updated[msgIndex], content: editContent }
        // Remove all messages after the edited one to prevent context carryover
        return updated.slice(0, msgIndex + 1)
      })
    }
    setEditingMessageId(null)
    setEditContent('')
  }

  // Cancel edit
  const cancelEdit = () => {
    setEditingMessageId(null)
    setEditContent('')
  }

  // Add custom hat
  const addCustomHat = () => {
    if (newHatName.trim()) {
      const newHat: api.HatPreset = {
        name: newHatName.trim().toLowerCase().replace(/\s+/g, '_'),
        description: newHatDescription.trim() || `Custom ${newHatName} personality`,
        system_prompt: newHatDescription.trim()
      }
      setCustomHats(prev => [...prev, newHat])
      setNewHatName('')
      setNewHatDescription('')
      setShowCreateHat(false)
    }
  }

  // All hats (API + custom)
  const allHats = [...(hats || []), ...customHats]
  
  // Toggle model selection for multi-agent mode
  const toggleModelSelection = (model: string) => {
    setSelectedModels(prev => 
      prev.includes(model) 
        ? prev.filter(m => m !== model)
        : [...prev, model]
    )
  }

  return (
    <div className="flex h-full">
      {/* Conversation History Sidebar */}
      {showHistory && (
        <div className="w-64 border-r border-freya-border bg-freya-bg-secondary flex flex-col">
          <div className="p-3 border-b border-freya-border flex items-center justify-between">
            <h3 className="font-medium text-freya-text-primary flex items-center gap-2">
              <History className="w-4 h-4" />
              Conversations
            </h3>
            <button
              onClick={createNewConversation}
              className="p-1.5 rounded hover:bg-freya-bg-tertiary text-freya-accent-blue"
              title="New conversation"
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {conversations.length === 0 ? (
              <p className="text-sm text-freya-text-muted text-center py-4">No conversations yet</p>
            ) : (
              conversations.map(conv => (
                <div
                  key={conv.id}
                  className={clsx(
                    'group p-2 rounded-lg cursor-pointer flex items-center justify-between',
                    currentConversationId === conv.id
                      ? 'bg-freya-accent-blue/20 border border-freya-accent-blue/30'
                      : 'hover:bg-freya-bg-tertiary'
                  )}
                  onClick={() => switchConversation(conv.id)}
                >
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-freya-text-primary truncate">
                      {conv.title}
                    </p>
                    <p className="text-xs text-freya-text-muted">
                      {conv.messages.length} messages
                    </p>
                  </div>
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-all">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        shareConversation(conv)
                      }}
                      className="p-1 rounded hover:bg-freya-accent-blue/20 text-freya-text-muted hover:text-freya-accent-blue"
                      title="Share"
                    >
                      <Share2 className="w-3 h-3" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        exportConversation(conv)
                      }}
                      className="p-1 rounded hover:bg-freya-accent-green/20 text-freya-text-muted hover:text-freya-accent-green"
                      title="Export JSON"
                    >
                      <Download className="w-3 h-3" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        deleteConversation(conv.id)
                      }}
                      className="p-1 rounded hover:bg-freya-accent-red/20 text-freya-text-muted hover:text-freya-accent-red"
                      title="Delete"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
      
      {/* Main chat area */}
      <div className="flex-1 flex flex-col">
        {/* Toolbar */}
        <div className="flex items-center gap-3 p-4 border-b border-freya-border bg-freya-bg-secondary">
          {/* History toggle */}
          <button
            onClick={() => setShowHistory(!showHistory)}
            className={clsx(
              'p-2 rounded-lg transition-colors',
              showHistory ? 'bg-freya-accent-blue/20 text-freya-accent-blue' : 'hover:bg-freya-bg-tertiary text-freya-text-muted'
            )}
            title="Conversation history"
          >
            <History className="w-4 h-4" />
          </button>
          
          {/* New Chat button - always visible */}
          <button
            onClick={createNewConversation}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-freya-accent-green/20 text-freya-accent-green hover:bg-freya-accent-green/30 transition-colors"
            title="Start new conversation"
          >
            <Plus className="w-4 h-4" />
            <span className="text-sm font-medium">New Chat</span>
          </button>
          
          {/* Chat Mode Selector */}
          <div className="flex items-center gap-1 bg-freya-bg-tertiary rounded-lg p-1">
            <button
              onClick={() => setChatMode('standard')}
              className={clsx(
                'flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-all',
                chatMode === 'standard'
                  ? 'bg-freya-bg-primary text-freya-text-primary shadow'
                  : 'text-freya-text-muted hover:text-freya-text-secondary'
              )}
              title="Standard single-model chat"
            >
              <MessageSquare className="w-4 h-4" />
              <span className="hidden sm:inline">Standard</span>
            </button>
            <button
              onClick={() => setChatMode('multi-agent')}
              className={clsx(
                'flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-all',
                chatMode === 'multi-agent'
                  ? 'bg-freya-accent-purple/20 text-freya-accent-purple shadow'
                  : 'text-freya-text-muted hover:text-freya-text-secondary'
              )}
              title="Multi-agent mode: Multiple models + synthesis"
            >
              <Users className="w-4 h-4" />
              <span className="hidden sm:inline">Multi-Agent</span>
            </button>
            <button
              onClick={() => setChatMode('reflection')}
              className={clsx(
                'flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-all',
                chatMode === 'reflection'
                  ? 'bg-freya-accent-cyan/20 text-freya-accent-cyan shadow'
                  : 'text-freya-text-muted hover:text-freya-text-secondary'
              )}
              title="Reflection mode: Self-critique and improvement"
            >
              <Brain className="w-4 h-4" />
              <span className="hidden sm:inline">Reflection</span>
            </button>
            <button
              onClick={() => setChatMode('research')}
              className={clsx(
                'flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-all',
                chatMode === 'research'
                  ? 'bg-freya-accent-yellow/20 text-freya-accent-yellow shadow'
                  : 'text-freya-text-muted hover:text-freya-text-secondary'
              )}
              title="Research mode: Internet search → Market analysis → BMAD brief"
            >
              <Search className="w-4 h-4" />
              <span className="hidden sm:inline">Research</span>
            </button>
            <button
              onClick={() => setChatMode('exchange')}
              className={clsx(
                'flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-all',
                chatMode === 'exchange'
                  ? 'bg-freya-accent-red/20 text-freya-accent-red shadow'
                  : 'text-freya-text-muted hover:text-freya-text-secondary'
              )}
              title="Exchange mode: Two AIs discuss autonomously"
            >
              <Users className="w-4 h-4" />
              <span className="hidden sm:inline">Exchange</span>
            </button>
          </div>
          
          <div className="h-6 w-px bg-freya-border" />
          
          {/* Hat selector */}
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-freya-text-muted" />
            <select
              value={selectedHat}
              onChange={(e) => setSelectedHat(e.target.value)}
              className="input py-1.5 text-sm w-32"
            >
              <option value="">Default</option>
              {allHats.map((hat) => (
                <option key={hat.name} value={hat.name}>
                  {hat.name.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </option>
              ))}
            </select>
            <button
              onClick={() => setShowCreateHat(true)}
              className="p-1.5 rounded hover:bg-freya-bg-tertiary"
              title="Create custom personality"
            >
              <Plus className="w-4 h-4 text-freya-text-muted" />
            </button>
          </div>
          
          {/* Web Search Toggle */}
          <button
            onClick={() => setWebSearchEnabled(!webSearchEnabled)}
            className={clsx(
              'flex items-center gap-2 px-3 py-1.5 rounded-md text-sm transition-all',
              webSearchEnabled
                ? 'bg-freya-accent-green/20 text-freya-accent-green border border-freya-accent-green/50'
                : 'bg-freya-bg-tertiary text-freya-text-muted hover:text-freya-text-primary'
            )}
            title="Enable web search for responses"
          >
            <Globe className="w-4 h-4" />
            <span className="hidden sm:inline">Web Search</span>
          </button>

          <div className="flex-1" />

          {/* Quick actions */}
          <button
            onClick={() => setShowSettings(!showSettings)}
            className={clsx('btn-ghost p-2', showSettings && 'bg-freya-bg-tertiary')}
          >
            <Settings2 className="w-4 h-4" />
          </button>
        </div>
        
        {/* Mode-specific settings bar */}
        {chatMode === 'multi-agent' && (
          <div className="p-3 border-b border-freya-border bg-freya-accent-purple/5">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Users className="w-4 h-4 text-freya-accent-purple" />
                <span className="text-sm font-medium text-freya-text-primary">Select Models ({selectedModels.length}/{ models?.length || 0}):</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {models?.map(model => (
                  <button
                    key={model.name}
                    onClick={() => toggleModelSelection(model.name)}
                    className={clsx(
                      'px-2 py-1 rounded text-xs font-medium transition-all',
                      selectedModels.includes(model.name)
                        ? 'bg-freya-accent-purple text-white'
                        : 'bg-freya-bg-tertiary text-freya-text-muted hover:bg-freya-bg-secondary'
                    )}
                  >
                    {model.name}
                  </button>
                ))}
              </div>
              {selectedModels.length < 2 && (
                <span className="text-xs text-freya-accent-yellow">Select at least 2 models</span>
              )}
            </div>
          </div>
        )}
        
        {chatMode === 'reflection' && (
          <div className="p-3 border-b border-freya-border bg-freya-accent-cyan/5">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Brain className="w-4 h-4 text-freya-accent-cyan" />
                <span className="text-sm font-medium text-freya-text-primary">Reflection Depth:</span>
              </div>
              <div className="flex items-center gap-2">
                {[1, 2, 3, 4].map(depth => (
                  <button
                    key={depth}
                    onClick={() => setReflectionDepth(depth)}
                    className={clsx(
                      'w-8 h-8 rounded-lg text-sm font-medium transition-all',
                      reflectionDepth === depth
                        ? 'bg-freya-accent-cyan text-white'
                        : 'bg-freya-bg-tertiary text-freya-text-muted hover:bg-freya-bg-secondary'
                    )}
                  >
                    {depth}
                  </button>
                ))}
              </div>
              <span className="text-xs text-freya-text-muted">
                {reflectionDepth} iteration{reflectionDepth > 1 ? 's' : ''} of self-critique and improvement
              </span>
            </div>
          </div>
        )}
        
        {chatMode === 'research' && (
          <div className="p-3 border-b border-freya-border bg-freya-accent-yellow/5">
            <div className="flex items-center gap-4 flex-wrap">
              {/* Sub-mode selector */}
              <div className="flex items-center gap-1 bg-freya-bg-tertiary rounded-lg p-1">
                <button
                  onClick={() => setResearchSubMode('assisted')}
                  className={clsx(
                    'px-3 py-1.5 rounded-md text-sm transition-all',
                    researchSubMode === 'assisted'
                      ? 'bg-freya-accent-yellow text-white'
                      : 'text-freya-text-muted hover:text-freya-text-secondary'
                  )}
                >
                  Assisted
                </button>
                <button
                  onClick={() => setResearchSubMode('autonomous')}
                  className={clsx(
                    'px-3 py-1.5 rounded-md text-sm transition-all',
                    researchSubMode === 'autonomous'
                      ? 'bg-freya-accent-red text-white'
                      : 'text-freya-text-muted hover:text-freya-text-secondary'
                  )}
                >
                  Autonomous
                </button>
              </div>
              
              {/* Mode description */}
              <div className="flex items-center gap-3 text-xs text-freya-text-muted">
                {researchSubMode === 'assisted' ? (
                  <>
                    <span className="flex items-center gap-1">
                      <Globe className="w-3 h-3" />
                      Your idea
                    </span>
                    <span>→</span>
                    <span className="flex items-center gap-1">
                      <TrendingUp className="w-3 h-3" />
                      Analysis
                    </span>
                    <span>→</span>
                    <span className="flex items-center gap-1">
                      <Rocket className="w-3 h-3" />
                      BMAD
                    </span>
                  </>
                ) : (
                  <>
                    <span className="flex items-center gap-1">
                      <Search className="w-3 h-3" />
                      Auto-search
                    </span>
                    <span>→</span>
                    <span className="flex items-center gap-1">
                      <Lightbulb className="w-3 h-3" />
                      Ideas
                    </span>
                    <span>→</span>
                    <span className="flex items-center gap-1">
                      <Rocket className="w-3 h-3" />
                      Pipeline
                    </span>
                    <span>→</span>
                    <span className="badge badge-red text-xs">Loop</span>
                  </>
                )}
              </div>
              
              {/* Status */}
              {researchPhase !== 'idle' && (
                <span className={clsx(
                  'badge',
                  researchPhase === 'searching' && 'badge-blue',
                  researchPhase === 'analyzing' && 'badge-purple',
                  researchPhase === 'briefing' && 'badge-cyan',
                  researchPhase === 'bmad_ready' && 'badge-green'
                )}>
                  {researchPhase === 'searching' && '🔍 Recherche...'}
                  {researchPhase === 'analyzing' && '🧠 Analyse...'}
                  {researchPhase === 'briefing' && '📋 Brief...'}
                  {researchPhase === 'bmad_ready' && '✅ Prêt pour BMAD'}
                </span>
              )}
              
              {/* Autonomous controls */}
              {researchSubMode === 'autonomous' && (
                <div className="flex items-center gap-2">
                  {autonomousRunning ? (
                    <button
                      onClick={() => {
                        autonomousStopRef.current = true // Signal stop to async function
                        setAutonomousRunning(false)
                      }}
                      className="btn-danger text-xs px-2 py-1 flex items-center gap-1"
                    >
                      <StopCircle className="w-3 h-3" />
                      Stop (#{autonomousIteration})
                    </button>
                  ) : (
                    <button
                      onClick={() => handleAutonomousResearch()}
                      disabled={isProcessingMulti}
                      className="btn-primary text-xs px-2 py-1 flex items-center gap-1"
                    >
                      <Rocket className="w-3 h-3" />
                      Start Autonomous
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
        
        {/* Exchange Mode Settings */}
        {chatMode === 'exchange' && (
          <div className="p-3 border-b border-freya-border bg-freya-accent-red/5">
            <div className="flex items-center gap-3 flex-wrap">
              {/* Model selectors */}
              <select
                value={exchangeModel1}
                onChange={(e) => setExchangeModel1(e.target.value)}
                className="input py-1.5 text-sm w-36"
                disabled={exchangeRunning}
              >
                <option value="">IA 1...</option>
                {models?.map(m => (
                  <option key={m.name} value={m.name}>{m.name.split(':')[0]}</option>
                ))}
              </select>
              <span className="text-freya-accent-red font-bold">↔</span>
              <select
                value={exchangeModel2}
                onChange={(e) => setExchangeModel2(e.target.value)}
                className="input py-1.5 text-sm w-36"
                disabled={exchangeRunning}
              >
                <option value="">IA 2...</option>
                {models?.map(m => (
                  <option key={m.name} value={m.name}>{m.name.split(':')[0]}</option>
                ))}
              </select>
              
              <div className="h-4 w-px bg-freya-border" />
              
              {/* Iterations or Unlimited */}
              <div className="flex items-center gap-2">
                <label className="flex items-center gap-1.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={exchangeUnlimited}
                    onChange={(e) => setExchangeUnlimited(e.target.checked)}
                    className="w-4 h-4 rounded border-freya-border"
                    disabled={exchangeRunning}
                  />
                  <span className="text-xs text-freya-text-secondary">Illimité</span>
                </label>
                {!exchangeUnlimited && (
                  <input
                    type="number"
                    min="2"
                    max="50"
                    value={exchangeIterations}
                    onChange={(e) => setExchangeIterations(Math.max(2, parseInt(e.target.value) || 10))}
                    className="input py-1 text-xs w-14 text-center"
                    disabled={exchangeRunning}
                  />
                )}
              </div>
              
              {/* Control */}
              {exchangeRunning ? (
                <button
                  onClick={stopExchange}
                  className="btn-danger text-sm px-3 py-1.5 flex items-center gap-1.5"
                >
                  <StopCircle className="w-4 h-4" />
                  Arrêter
                </button>
              ) : (
                <button
                  onClick={() => handleExchangeChat()}
                  disabled={!exchangeModel1 || !exchangeModel2 || !exchangeTopic || exchangeModel1 === exchangeModel2}
                  className="btn-primary text-sm px-3 py-1.5 flex items-center gap-1.5"
                >
                  <MessageSquare className="w-4 h-4" />
                  Démarrer
                </button>
              )}
            </div>
            
            {/* Topic input */}
            <div className="mt-2">
              <input
                type="text"
                value={exchangeTopic}
                onChange={(e) => setExchangeTopic(e.target.value)}
                placeholder="Sujet de la conversation... (ex: 'Quel est le meilleur framework frontend en 2025?')"
                className="input text-sm w-full"
                disabled={exchangeRunning}
              />
            </div>
          </div>
        )}

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

          {messages.map((message) => {
            const isAgent = message.role === 'agent'
            const isCollapsed = isAgent && collapsedAgents.has(message.id)
            
            return (
            <div
              key={message.id}
              className={clsx(
                'animate-slide-up',
                message.role === 'user' && 'flex justify-end'
              )}
            >
              <div
                className={clsx(
                  'max-w-3xl rounded-lg',
                  isCollapsed ? 'p-2' : 'p-4',
                  message.role === 'user' && 'bg-freya-accent-blue/20 border border-freya-accent-blue/30',
                  message.role === 'assistant' && 'bg-freya-bg-tertiary border border-freya-border',
                  message.role === 'agent' && 'bg-freya-accent-purple/10 border border-freya-accent-purple/30',
                  message.role === 'synthesis' && 'bg-freya-accent-green/15 border-2 border-freya-accent-green/50 shadow-lg',
                  message.role === 'system' && 'bg-freya-accent-yellow/10 border border-freya-accent-yellow/30',
                  message.role === 'tool' && 'bg-freya-accent-purple/10 border border-freya-accent-purple/30',
                  message.isReflection && 'bg-freya-accent-cyan/10 border border-freya-accent-cyan/30'
                )}
              >
                {/* Attachments preview for user messages */}
                {message.attachments && message.attachments.length > 0 && !isCollapsed && (
                  <div className="flex flex-wrap gap-2 mb-2">
                    {message.attachments.map((file, idx) => (
                      <div key={idx} className="flex items-center gap-1 px-2 py-1 rounded bg-freya-bg-primary text-xs">
                        {file.type.startsWith('image/') ? (
                          <Image className="w-3 h-3" />
                        ) : (
                          <FileText className="w-3 h-3" />
                        )}
                        <span className="text-freya-text-secondary">{file.name}</span>
                      </div>
                    ))}
                  </div>
                )}
                
                {/* Header */}
                <div className={clsx(
                  'flex items-center justify-between',
                  !isCollapsed && 'mb-2'
                )}>
                  <div className="flex items-center gap-2">
                    {/* Collapse toggle for agent messages */}
                    {isAgent && (
                      <button
                        onClick={() => toggleAgentCollapse(message.id)}
                        className="p-0.5 rounded hover:bg-freya-bg-tertiary transition-colors"
                        title={isCollapsed ? 'Expand response' : 'Collapse response'}
                      >
                        {isCollapsed ? (
                          <ChevronRight className="w-4 h-4 text-freya-accent-purple" />
                        ) : (
                          <ChevronDown className="w-4 h-4 text-freya-accent-purple" />
                        )}
                      </button>
                    )}
                    <span className={clsx(
                      'text-xs font-medium',
                      message.role === 'user' && 'text-freya-accent-blue',
                      message.role === 'assistant' && 'text-freya-accent-green',
                      message.role === 'agent' && 'text-freya-accent-purple',
                      message.role === 'synthesis' && 'text-freya-accent-green font-semibold',
                      message.role === 'system' && 'text-freya-accent-yellow',
                      message.role === 'tool' && 'text-freya-accent-purple',
                      message.isReflection && 'text-freya-accent-cyan'
                    )}>
                      {message.role === 'user' ? 'You' : 
                       message.role === 'synthesis' ? '🔄 Synthèse Cross-Checkée' :
                       message.role === 'agent' ? `🤖 ${message.agentName || 'Agent'}` :
                       message.isReflection ? '🔍 Reflection' :
                       message.role === 'assistant' ? 'Freya' :
                       message.role === 'tool' ? 'Tool' : 'ℹ️ Info'}
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
                    {message.searchResults && message.searchResults.length > 0 && (
                      <span className="text-xs text-freya-accent-cyan flex items-center gap-1">
                        <Globe className="w-3 h-3" />
                        {message.searchResults.length} sources
                      </span>
                    )}
                    {isCollapsed && (
                      <span className="text-xs text-freya-text-muted italic">
                        (click to expand)
                      </span>
                    )}
                  </div>
                  
                  {/* Actions */}
                  <div className="flex items-center gap-1">
                    {message.role === 'user' && (
                      <button
                        onClick={() => startEditMessage(message)}
                        className="p-1 rounded hover:bg-freya-bg-primary/50 transition-colors"
                        title="Edit message"
                      >
                        <Edit2 className="w-4 h-4 text-freya-text-muted" />
                      </button>
                    )}
                    {!isCollapsed && (
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
                    )}
                  </div>
                </div>

                {/* Content - hidden when collapsed */}
                {!isCollapsed && (
                  <>
                    {editingMessageId === message.id ? (
                      <div className="space-y-2">
                        <textarea
                          value={editContent}
                          onChange={(e) => setEditContent(e.target.value)}
                          className="w-full p-2 rounded bg-freya-bg-primary border border-freya-border text-sm"
                          rows={3}
                        />
                        <div className="flex gap-2">
                          <button
                            onClick={() => saveEditedMessage(message.id)}
                            className="btn-primary text-xs px-2 py-1"
                          >
                            Save (removes context)
                          </button>
                          <button
                            onClick={cancelEdit}
                            className="btn-ghost text-xs px-2 py-1"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className={clsx(
                        'prose-freya',
                        message.role === 'synthesis' && 'text-freya-text-primary'
                      )}>
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {message.content}
                        </ReactMarkdown>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          )})}
          

          {/* Loading indicator with cancel */}
          {chatMutation.isPending && (
            <div className="flex items-center gap-3 text-freya-text-muted animate-pulse">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Freya is thinking...</span>
              <button
                onClick={cancelGeneration}
                className="flex items-center gap-1 px-2 py-1 rounded text-xs bg-freya-accent-red/20 text-freya-accent-red hover:bg-freya-accent-red/30"
              >
                <StopCircle className="w-3 h-3" />
                Cancel
              </button>
            </div>
          )}
          
          {/* Quick actions when messages exist */}
          {messages.length > 0 && !chatMutation.isPending && (
            <div className="flex items-center gap-2 mt-2">
              <button
                onClick={deleteLastMessage}
                className="flex items-center gap-1 px-2 py-1 rounded text-xs bg-freya-bg-tertiary text-freya-text-muted hover:text-freya-accent-red"
                title="Delete last message"
              >
                <Trash2 className="w-3 h-3" />
                Delete last
              </button>
              <button
                onClick={() => setMessages([])}
                className="flex items-center gap-1 px-2 py-1 rounded text-xs bg-freya-bg-tertiary text-freya-text-muted hover:text-freya-accent-yellow"
                title="Clear all messages"
              >
                <RotateCcw className="w-3 h-3" />
                Clear all
              </button>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        <div className="p-4 border-t border-freya-border bg-freya-bg-secondary">
          {/* Attached files preview */}
          {attachedFiles.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-3 p-2 bg-freya-bg-tertiary rounded-lg">
              {attachedFiles.map((file, idx) => (
                <div key={idx} className="flex items-center gap-2 px-2 py-1 rounded bg-freya-bg-primary">
                  {file.preview ? (
                    <img src={file.preview} alt={file.name} className="w-8 h-8 object-cover rounded" />
                  ) : file.type.startsWith('image/') ? (
                    <Image className="w-4 h-4 text-freya-accent-purple" />
                  ) : (
                    <FileText className="w-4 h-4 text-freya-accent-cyan" />
                  )}
                  <span className="text-sm text-freya-text-primary max-w-[120px] truncate">{file.name}</span>
                  <span className="text-xs text-freya-text-muted">
                    {(file.size / 1024).toFixed(1)}KB
                  </span>
                  <button
                    onClick={() => removeAttachedFile(idx)}
                    className="p-0.5 rounded hover:bg-freya-accent-red/20"
                  >
                    <X className="w-3 h-3 text-freya-text-muted hover:text-freya-accent-red" />
                  </button>
                </div>
              ))}
            </div>
          )}
          
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={webSearchEnabled 
                  ? "Ask with web search enabled... (Enter to send)" 
                  : "Ask Freya anything... (Enter to send)"}
                className="textarea min-h-[80px] pr-24"
                disabled={chatMutation.isPending}
              />
              <div className="absolute right-3 top-3 flex items-center gap-1">
                {/* File attachment */}
                <input
                  ref={fileInputRef}
                  type="file"
                  onChange={handleFileSelect}
                  className="hidden"
                  multiple
                  accept=".txt,.md,.json,.py,.js,.ts,.tsx,.jsx,.css,.html,.xml,.yaml,.yml,.toml,.ini,.cfg,.log,.csv,.sql,.png,.jpg,.jpeg,.gif,.webp"
                />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isUploading}
                  className="p-1.5 rounded hover:bg-freya-bg-tertiary transition-colors"
                  title="Attach file (text, code, or image)"
                >
                  {isUploading ? (
                    <Loader2 className="w-4 h-4 text-freya-text-muted animate-spin" />
                  ) : (
                    <Paperclip className="w-4 h-4 text-freya-text-muted" />
                  )}
                </button>
                {/* Web search toggle */}
                <button
                  onClick={() => setWebSearchEnabled(!webSearchEnabled)}
                  className={clsx(
                    'p-1.5 rounded transition-colors',
                    webSearchEnabled 
                      ? 'bg-freya-accent-green/20 text-freya-accent-green' 
                      : 'hover:bg-freya-bg-tertiary text-freya-text-muted'
                  )}
                  title={webSearchEnabled ? 'Web search enabled' : 'Enable web search'}
                >
                  <Globe className="w-4 h-4" />
                </button>
              </div>
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
          <div className="flex items-center justify-between mt-2">
            <p className="text-xs text-freya-text-muted">
              Press <kbd className="px-1.5 py-0.5 rounded bg-freya-bg-tertiary text-freya-text-secondary">Enter</kbd> to send • <kbd className="px-1.5 py-0.5 rounded bg-freya-bg-tertiary text-freya-text-secondary">Ctrl+Enter</kbd> for newline
            </p>
            <div className="flex items-center gap-3 text-xs">
              {webSearchEnabled && (
                <span className="text-freya-accent-green flex items-center gap-1">
                  <Globe className="w-3 h-3" />
                  Web search enabled
                </span>
              )}
              {attachedFiles.length > 0 && (
                <span className="text-freya-accent-cyan flex items-center gap-1">
                  <Paperclip className="w-3 h-3" />
                  {attachedFiles.length} file(s) attached
                </span>
              )}
            </div>
          </div>
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
                {allHats.map((hat) => (
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
                <button
                  onClick={() => setShowCreateHat(true)}
                  className="w-full text-left p-2 rounded text-sm bg-freya-bg-tertiary text-freya-text-muted hover:bg-freya-bg-elevated border border-dashed border-freya-border"
                >
                  <Plus className="w-4 h-4 inline mr-2" />
                  Create custom personality
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create Custom Hat Modal */}
      {showCreateHat && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-freya-bg-secondary rounded-lg p-6 max-w-md w-full mx-4 shadow-xl">
            <h3 className="text-lg font-semibold text-freya-text-primary mb-4">
              Create Custom Personality
            </h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-freya-text-secondary mb-1">Name</label>
                <input
                  type="text"
                  value={newHatName}
                  onChange={(e) => setNewHatName(e.target.value)}
                  placeholder="e.g., security_expert, creative_writer"
                  className="input w-full"
                />
              </div>
              <div>
                <label className="block text-sm text-freya-text-secondary mb-1">Description / System Prompt</label>
                <textarea
                  value={newHatDescription}
                  onChange={(e) => setNewHatDescription(e.target.value)}
                  placeholder="Describe the personality and behavior..."
                  className="textarea w-full min-h-[100px]"
                />
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button onClick={addCustomHat} className="btn-primary flex-1">
                Create
              </button>
              <button onClick={() => setShowCreateHat(false)} className="btn-ghost">
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
