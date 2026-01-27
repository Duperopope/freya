/**
 * BMADPage - BMAD Studio v2.5
 * 
 * Refactored UX for intuitive, dynamic, and intelligent workflow management.
 * Features:
 * - Real-time pipeline overview with visual progress
 * - Contextual AI-powered suggestions
 * - Seamless Research mode integration
 * - Smart agent status tracking
 * - Responsive and ergonomic design
 */

import { useState, useEffect, useRef } from 'react'
import {
  Play,
  Square,
  FileText,
  GitBranch,
  Code2,
  Users,
  Layers,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  ChevronRight,
  Eye,
  Download,
  Sparkles,
  Target,
  Building2,
  ClipboardList,
  BookOpen,
  TestTube2,
  ArrowRight,
  MessageSquare,
  Send,
  Loader2,
  ChevronDown,
  AlertTriangle,
  FileJson,
  Repeat,
  Timer,
  Activity,
  FolderOpen,
  History,
  PanelLeftClose,
  PanelLeft,
  Rocket,
  Brain,
  Zap,
  Maximize2,
  Minimize2
} from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { clsx } from 'clsx'
import { format, formatDistanceToNow } from 'date-fns'
import * as api from '../../lib/api'
import { useAppStore } from '../../stores/appStore'

// BMAD Agent definitions
interface AgentDef {
  id: string
  name: string
  role: string
  icon: typeof FileText
  color: string
  bgColor: string
  output: string
  description: string
  questions: string[]
}

const AGENTS: AgentDef[] = [
  {
    id: 'analyst',
    name: 'Analyst',
    role: 'analyst',
    icon: Target,
    color: 'text-freya-accent-blue',
    bgColor: 'bg-freya-accent-blue/20',
    output: 'project-brief.md',
    description: 'Analyzes goals and creates project brief',
    questions: [
      'What is the primary purpose of this application?',
      'Who are the target users?',
      'What are the key features you want?',
      'Are there any technical constraints?',
      'What is the expected timeline?'
    ]
  },
  {
    id: 'pm',
    name: 'Product Manager',
    role: 'pm',
    icon: ClipboardList,
    color: 'text-freya-accent-purple',
    bgColor: 'bg-freya-accent-purple/20',
    output: 'PRD.md',
    description: 'Creates Product Requirements Document',
    questions: []
  },
  {
    id: 'architect',
    name: 'Architect',
    role: 'architect',
    icon: Building2,
    color: 'text-freya-accent-cyan',
    bgColor: 'bg-freya-accent-cyan/20',
    output: 'architecture.md',
    description: 'Designs system architecture',
    questions: []
  },
  {
    id: 'po',
    name: 'Product Owner',
    role: 'po',
    icon: Layers,
    color: 'text-freya-accent-yellow',
    bgColor: 'bg-freya-accent-yellow/20',
    output: 'epics/',
    description: 'Breaks down into epics',
    questions: []
  },
  {
    id: 'sm',
    name: 'Scrum Master',
    role: 'sm',
    icon: Users,
    color: 'text-freya-accent-green',
    bgColor: 'bg-freya-accent-green/20',
    output: 'stories/',
    description: 'Creates user stories',
    questions: []
  },
  {
    id: 'dev',
    name: 'Developer',
    role: 'dev',
    icon: Code2,
    color: 'text-freya-accent-red',
    bgColor: 'bg-freya-accent-red/20',
    output: 'code/',
    description: 'Implements the code',
    questions: []
  },
  {
    id: 'qa',
    name: 'QA Engineer',
    role: 'qa',
    icon: TestTube2,
    color: 'text-freya-accent-purple',
    bgColor: 'bg-freya-accent-purple/20',
    output: 'QA.md',
    description: 'Runs quality assurance',
    questions: []
  },
  {
    id: 'runner',
    name: 'Test Runner',
    role: 'runner',
    icon: Rocket,
    color: 'text-freya-accent-cyan',
    bgColor: 'bg-freya-accent-cyan/20',
    output: 'run-report.md',
    description: 'Launches and tests the application',
    questions: []
  },
  {
    id: 'validator',
    name: 'Validator',
    role: 'validator',
    icon: CheckCircle2,
    color: 'text-freya-accent-green',
    bgColor: 'bg-freya-accent-green/20',
    output: 'validation.md',
    description: 'Final validation loop (Dev→QA)',
    questions: []
  }
]

type BMADMode = 'brainstorm' | 'running' | 'complete' | 'research'

interface ChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  agent?: string
}

interface AgentLog {
  agent: string
  event: string
  message: string
  timestamp: Date
  details?: Record<string, unknown>
}

interface PipelineError {
  agent: string
  error: string
  timestamp: string
  stack?: string
}

export function BMADPage() {
  useQueryClient()
  const { bmadProgress, setBMADProgress, researchState, setResearchState } = useAppStore()
  
  // Track if auto-start has been triggered to prevent multiple runs
  const autoStartTriggeredRef = useRef(false)
  
  // Main state
  const [goal, setGoal] = useState('')
  const [projectName, setProjectName] = useState('FreyaProject')
  const [mode, setMode] = useState<BMADMode>('brainstorm')
  const [continuousMode, setContinuousMode] = useState(true)
  
  // Brainstorming state
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [chatInput, setChatInput] = useState('')
  const [isBrainstorming, setIsBrainstorming] = useState(false)
  const [brainstormComplete, setBrainstormComplete] = useState(false)
  const chatEndRef = useRef<HTMLDivElement>(null)
  
  // Analyst chat history
  const [analystHistory, setAnalystHistory] = useState<{ projectName: string; messages: ChatMessage[]; updatedAt: string }[]>([])
  const [showAnalystHistory, setShowAnalystHistory] = useState(false)
  
  // Quick action suggestions from analyst
  const [quickSuggestions, setQuickSuggestions] = useState<string[]>([])
  
  // Pipeline state
  const [selectedArtifact, setSelectedArtifact] = useState<string | null>(null)
  const [artifactContent, setArtifactContent] = useState<string>('')
  const [agentLogs, setAgentLogs] = useState<AgentLog[]>([])
  const [expandedAgent, setExpandedAgent] = useState<string | null>(null)
  const [pipelineErrors, setPipelineErrors] = useState<PipelineError[]>([])
  const [startTime, setStartTime] = useState<Date | null>(null)
  
  // Analyst panel state - Always visible by default with hide option
  const [showAnalystPanel, setShowAnalystPanel] = useState(true)
  
  // Pipeline view mode: compact or expanded
  const [pipelineViewMode, setPipelineViewMode] = useState<'compact' | 'expanded'>('expanded')
  
  // Recent projects state
  const [recentProjects, setRecentProjects] = useState<{ name: string; lastModified: string; goal: string }[]>([])
  const [showRecentProjects, setShowRecentProjects] = useState(false)
  const [selectedProject, setSelectedProject] = useState<{ name: string; goal: string } | null>(null)
  const [resumeInfo, setResumeInfo] = useState<api.ResumeInfo | null>(null)
  const [checkingResume, setCheckingResume] = useState(false)

  // Fetch BMAD status
  const { data: status, refetch: refetchStatus } = useQuery({
    queryKey: ['bmadStatus'],
    queryFn: api.getBMADStatus,
    refetchInterval: bmadProgress?.running ? 1000 : 10000,
    staleTime: 1000, // Keep data fresh for 1 second
    gcTime: 5 * 60 * 1000, // Keep in cache for 5 minutes
  })

  // Fetch artifacts - persist across tab changes
  const { data: artifacts, refetch: refetchArtifacts } = useQuery({
    queryKey: ['artifacts', projectName],
    queryFn: () => api.getArtifacts(projectName),
    refetchInterval: bmadProgress?.running ? 3000 : 30000,
    staleTime: 30000, // Keep data fresh for 30 seconds
    gcTime: 30 * 60 * 1000, // Keep in cache for 30 minutes
    refetchOnWindowFocus: false, // Don't refetch when switching tabs
  })

  // Update store and mode when status changes
  useEffect(() => {
    if (status) {
      // Include logs from status in the progress
      setBMADProgress(status.running ? {
        running: status.running,
        current_agent: status.current_agent,
        agents_completed: status.agents_completed,
        artifacts_generated: status.artifacts_generated,
        logs: status.logs?.map(log => ({
          timestamp: log.timestamp,
          level: log.level,
          agent: log.agent,
          message: log.message,
          details: log.details || {},
        })) || [],
      } : null)
      
      // Also update local agentLogs from status logs
      if (status.logs && status.logs.length > 0) {
        const newLogs = status.logs.map(log => ({
          agent: log.agent || 'system',
          event: log.level,
          message: log.message,
          timestamp: new Date(),
          details: log.details,
        }))
        setAgentLogs(newLogs)
      }
      
      if (status.running) {
        setMode('running')
      } else if (status.agents_completed.length >= AGENTS.length - 2) {
        // Complete when main agents are done (ignore runner/validator if not run)
        setMode('complete')
      }
      
      if (status.error) {
        setPipelineErrors(prev => [...prev, {
          agent: status.current_agent || 'unknown',
          error: status.error!,
          timestamp: new Date().toISOString()
        }])
      }
    }
  }, [status, setBMADProgress])

  // Auto-scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatMessages])
  
  // Load chat history from localStorage on mount
  useEffect(() => {
    try {
      const savedHistory = localStorage.getItem('freya_analyst_chat_history')
      if (savedHistory) {
        setAnalystHistory(JSON.parse(savedHistory))
      }
    } catch (e) {
      console.error('Failed to load analyst chat history:', e)
    }
  }, [])
  
  // Save chat messages for current project to localStorage
  useEffect(() => {
    if (chatMessages.length > 0 && projectName) {
      try {
        const history = JSON.parse(localStorage.getItem('freya_analyst_chat_history') || '[]')
        const updatedHistory = [
          { projectName, messages: chatMessages, updatedAt: new Date().toISOString() },
          ...history.filter((h: { projectName: string }) => h.projectName !== projectName)
        ].slice(0, 20) // Keep last 20 project histories
        localStorage.setItem('freya_analyst_chat_history', JSON.stringify(updatedHistory))
        setAnalystHistory(updatedHistory)
      } catch (e) {
        console.error('Failed to save analyst chat history:', e)
      }
    }
  }, [chatMessages, projectName])
  
  // Extract quick suggestions from analyst responses
  useEffect(() => {
    const lastAssistantMessage = [...chatMessages].reverse().find(m => m.role === 'assistant')
    if (lastAssistantMessage) {
      // Extract numbered items or questions
      const content = lastAssistantMessage.content
      const suggestions: string[] = []
      
      // Match numbered items (1. 2. 3.)
      const numberedMatches = content.match(/\d+\.\s*\*{0,2}([^\n*]+)/g)
      if (numberedMatches) {
        numberedMatches.slice(0, 4).forEach(match => {
          const cleaned = match.replace(/^\d+\.\s*\*{0,2}/, '').replace(/\*{0,2}$/, '').trim()
          if (cleaned.length > 10 && cleaned.length < 100) {
            suggestions.push(cleaned)
          }
        })
      }
      
      // Match questions ending with ?
      const questionMatches = content.match(/[^.!?\n]+\?/g)
      if (questionMatches) {
        questionMatches.slice(0, 3).forEach(match => {
          const cleaned = match.trim()
          if (cleaned.length > 15 && cleaned.length < 100 && !suggestions.includes(cleaned)) {
            suggestions.push(cleaned)
          }
        })
      }
      
      setQuickSuggestions(suggestions.slice(0, 4))
    }
  }, [chatMessages])

  // Start BMAD mutation
  const startMutation = useMutation({
    mutationFn: () => api.runBMAD(goal, projectName),
    onSuccess: () => {
      setMode('running')
      setStartTime(new Date())
      setPipelineErrors([])
      setAgentLogs([])
      refetchStatus()
      refetchArtifacts()
      // Save to recent projects
      saveToRecentProjects()
    },
  })
  
  // Save current project to recent projects
  const saveToRecentProjects = () => {
    const project = { name: projectName, lastModified: new Date().toISOString(), goal: goal.slice(0, 100) }
    setRecentProjects(prev => {
      const filtered = prev.filter(p => p.name !== projectName)
      return [project, ...filtered].slice(0, 10)
    })
    // Persist to localStorage
    try {
      const projects = JSON.parse(localStorage.getItem('freya_recent_projects') || '[]')
      const filtered = projects.filter((p: { name: string }) => p.name !== projectName)
      localStorage.setItem('freya_recent_projects', JSON.stringify([project, ...filtered].slice(0, 10)))
    } catch (e) {
      console.error('Failed to save recent projects:', e)
    }
  }
  
  // AUTO-START: Detect when Research mode sends a brief and auto-launch pipeline
  useEffect(() => {
    if (
      researchState.autoStartBMAD && 
      researchState.bmadGoal && 
      researchState.bmadProjectName &&
      !autoStartTriggeredRef.current &&
      !bmadProgress?.running
    ) {
      console.log('[BMAD] Auto-start triggered from Research mode')
      autoStartTriggeredRef.current = true
      
      // Set the goal and project name from research
      setGoal(researchState.bmadGoal)
      setProjectName(researchState.bmadProjectName)
      setBrainstormComplete(true) // Skip brainstorm since we have the brief
      
      // Add system message about auto-start
      setChatMessages([{
        role: 'system',
        content: `🤖 **Mode Autonome** - Brief reçu de Research Mode\n\n📋 **Projet:** ${researchState.bmadProjectName}\n\n🚀 **Lancement automatique du pipeline BMAD...**`,
        timestamp: new Date(),
      }])
      
      // Clear the auto-start flag
      setResearchState({
        autoStartBMAD: false,
      })
      
      // Start the pipeline after a short delay to let state settle
      setTimeout(() => {
        console.log('[BMAD] Starting pipeline automatically...')
        startMutation.mutate()
      }, 1000)
    }
  }, [researchState.autoStartBMAD, researchState.bmadGoal, researchState.bmadProjectName, bmadProgress?.running])
  
  // Load recent projects on mount - from localStorage AND from Files/artifacts
  useEffect(() => {
    const loadProjects = async () => {
      try {
        // Load from localStorage first
        const localProjects = JSON.parse(localStorage.getItem('freya_recent_projects') || '[]')
        
        // Also scan the artifacts folder for real projects
        try {
          const artifactsList = await api.getArtifacts()
          if (artifactsList && artifactsList.length > 0) {
            // Group artifacts by project directory
            const projectMap = new Map<string, { name: string; lastModified: string; goal: string }>()
            
            for (const artifact of artifactsList) {
              // Extract project name from path (e.g., "FreyaProject/project-brief.md" -> "FreyaProject")
              const parts = artifact.path.split('/')
              if (parts.length >= 2) {
                const projectName = parts[0]
                if (!projectMap.has(projectName)) {
                  projectMap.set(projectName, {
                    name: projectName,
                    lastModified: artifact.modified_at || new Date().toISOString(),
                    goal: `Project from Files (${projectName})`
                  })
                } else {
                  // Update lastModified if this artifact is more recent
                  const existing = projectMap.get(projectName)!
                  if (artifact.modified_at && artifact.modified_at > existing.lastModified) {
                    existing.lastModified = artifact.modified_at
                  }
                }
              }
            }
            
            // Merge with localStorage projects (local takes priority)
            const localNames = new Set(localProjects.map((p: { name: string }) => p.name))
            const fileProjects = Array.from(projectMap.values()).filter(p => !localNames.has(p.name))
            
            const merged = [...localProjects, ...fileProjects].slice(0, 10)
            setRecentProjects(merged)
          } else {
            setRecentProjects(localProjects)
          }
        } catch (artifactError) {
          console.error('Failed to load projects from artifacts:', artifactError)
          setRecentProjects(localProjects)
        }
      } catch (e) {
        console.error('Failed to load recent projects:', e)
      }
    }
    
    loadProjects()
  }, [])

  // Load artifact content
  useEffect(() => {
    if (selectedArtifact) {
      api.getArtifact(selectedArtifact)
        .then(data => setArtifactContent(data.content))
        .catch(() => setArtifactContent('Error loading artifact'))
    }
  }, [selectedArtifact])

  // Brainstorming with Analyst
  const sendBrainstormMessage = async () => {
    if (!chatInput.trim() || isBrainstorming) return
    
    const userMessage: ChatMessage = {
      role: 'user',
      content: chatInput,
      timestamp: new Date()
    }
    
    setChatMessages(prev => [...prev, userMessage])
    setChatInput('')
    setIsBrainstorming(true)
    
    try {
      // Call chat API with analyst persona
      const response = await api.generateChat({
        message: chatInput,
        hat: 'analyst',
        system_prompt: `Tu es l'Analyst de l'équipe BMAD. Tu aides à clarifier et structurer les besoins du projet.
        
Contexte du projet: ${goal || 'Non défini'}
Nom du projet: ${projectName}

Ton rôle:
1. Poser des questions pertinentes pour clarifier les besoins
2. Identifier les fonctionnalités clés
3. Définir les contraintes techniques
4. Valider la compréhension du besoin

Quand tu estimes avoir assez d'informations, termine par: "BRAINSTORM_COMPLETE" et résume les points clés.`,
        web_search: false,
        max_tokens: 1024
      })
      
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.content,
        timestamp: new Date(),
        agent: 'analyst'
      }
      
      setChatMessages(prev => [...prev, assistantMessage])
      
      // Check if brainstorm is complete
      if (response.content.includes('BRAINSTORM_COMPLETE')) {
        setBrainstormComplete(true)
        // Update goal with refined understanding
        const refinedGoal = `${goal}\n\n### Clarifications from brainstorming:\n${chatMessages.map(m => `- ${m.content}`).join('\n')}`
        setGoal(refinedGoal)
      }
    } catch (error) {
      const errorMessage: ChatMessage = {
        role: 'system',
        content: `Error: ${error instanceof Error ? error.message : 'Failed to get response'}`,
        timestamp: new Date()
      }
      setChatMessages(prev => [...prev, errorMessage])
    } finally {
      setIsBrainstorming(false)
    }
  }

  // Start brainstorming
  const startBrainstorm = () => {
    if (!goal.trim()) return
    
    const welcomeMessage: ChatMessage = {
      role: 'assistant',
      content: `Bonjour ! Je suis l'**Analyst** de l'équipe BMAD. Je vais vous aider à clarifier et structurer votre projet.

**Projet:** ${projectName}
**Objectif initial:** ${goal}

Pour mieux comprendre vos besoins, j'ai quelques questions:

1. **Utilisateurs cibles** - Qui utilisera cette application ?
2. **Fonctionnalités clés** - Quelles sont les 3-5 fonctionnalités essentielles ?
3. **Contraintes techniques** - Y a-t-il des technologies imposées ou à éviter ?
4. **Timeline** - Quelle est la date cible ?

Répondez à ces questions ou posez-moi les vôtres !`,
      timestamp: new Date(),
      agent: 'analyst'
    }
    
    setChatMessages([welcomeMessage])
    setMode('brainstorm')
    setBrainstormComplete(false)
  }
  
  // Skip brainstorming
  const skipBrainstorm = () => {
    setBrainstormComplete(true)
    startMutation.mutate()
  }

  // Export all logs as JSON (errors + pipeline logs)
  const exportLogsJSON = () => {
    const data = {
      project: projectName,
      goal: goal,
      exported_at: new Date().toISOString(),
      status: {
        running: status?.running ?? false,
        current_agent: status?.current_agent,
        completed_agents: status?.agents_completed ?? [],
        artifacts_generated: status?.artifacts_generated ?? [],
      },
      total_errors: pipelineErrors.length,
      errors: pipelineErrors.map(e => ({
        agent: e.agent,
        error: e.error,
        timestamp: e.timestamp,
        stack: e.stack
      })),
      pipeline_logs: bmadProgress?.logs ?? [],
      agent_logs: agentLogs,
      artifacts: artifacts ?? [],
    }
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `freya-bmad-logs-${projectName}-${format(new Date(), 'yyyy-MM-dd-HHmm')}.json`
    a.click()
    URL.revokeObjectURL(url)
  }
  
  // Legacy alias for backward compatibility
  const exportErrorsJSON = exportLogsJSON

  const isRunning = status?.running ?? false
  const completedAgents = status?.agents_completed ?? []
  const currentAgent = status?.current_agent
  
  // Auto-expand currently running agent
  useEffect(() => {
    if (currentAgent) {
      setExpandedAgent(currentAgent)
    }
  }, [currentAgent])

  // Get agent status
  const getAgentStatus = (agentId: string): 'completed' | 'running' | 'pending' | 'error' => {
    if (completedAgents.includes(agentId)) return 'completed'
    if (currentAgent === agentId) return 'running'
    if (pipelineErrors.some(e => e.agent === agentId)) return 'error'
    return 'pending'
  }

  // Calculate elapsed time
  const elapsedTime = startTime ? formatDistanceToNow(startTime, { addSuffix: false }) : null

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Top Bar */}
      <div className="p-4 border-b border-freya-border bg-freya-bg-secondary">
        <div className="flex items-center gap-4">
          {/* Goal Input */}
          <div className="flex-1">
            <div className="relative">
              <Sparkles className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-freya-accent-yellow" />
              <input
                type="text"
                value={goal}
                onChange={(e) => setGoal(e.target.value)}
                placeholder="Describe your project goal... (e.g., 'Build a task management API with user authentication')"
                className="input pl-11 pr-4"
                disabled={isRunning}
              />
            </div>
          </div>

          {/* Project Name */}
          <div className="w-48">
            <input
              type="text"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              placeholder="Project name"
              className="input"
              disabled={isRunning}
            />
          </div>

          {/* Continuous Mode Toggle */}
          <button
            onClick={() => setContinuousMode(!continuousMode)}
            disabled={isRunning}
            className={clsx(
              'flex items-center gap-2 px-3 py-2 rounded-lg border transition-all',
              continuousMode
                ? 'border-freya-accent-green/50 bg-freya-accent-green/10 text-freya-accent-green'
                : 'border-freya-border bg-freya-bg-tertiary text-freya-text-muted'
            )}
            title="Continuous mode: pipeline runs until app is complete"
          >
            <Repeat className="w-4 h-4" />
            <span className="text-sm">Continuous</span>
          </button>

          {/* New Project Button - Always visible */}
          <button
            onClick={() => {
              setProjectName('NewProject')
              setGoal('')
              setChatMessages([])
              setBrainstormComplete(false)
              setMode('brainstorm')
              setPipelineErrors([])
              setAgentLogs([])
              setSelectedArtifact(null)
              setArtifactContent('')
              setStartTime(null)
            }}
            disabled={isRunning}
            className="btn-secondary flex items-center gap-2"
            title="Start a new project"
          >
            <Sparkles className="w-4 h-4" />
            New Project
          </button>

          {/* Action Button */}
          {mode === 'brainstorm' ? (
            <div className="flex items-center gap-2">
              <button
                onClick={skipBrainstorm}
                className="btn-secondary"
              >
                Skip
              </button>
              <button
                onClick={() => brainstormComplete && startMutation.mutate()}
                disabled={!brainstormComplete || startMutation.isPending}
                className="btn-primary flex items-center gap-2"
              >
                <Play className="w-4 h-4" />
                Launch Pipeline
              </button>
            </div>
          ) : isRunning ? (
            <button
              onClick={() => {/* TODO: stopMutation.mutate() */}}
              className="btn-danger flex items-center gap-2"
            >
              <Square className="w-4 h-4" />
              Stop
            </button>
          ) : (
            <button
              onClick={() => goal.trim() ? startBrainstorm() : null}
              disabled={!goal.trim() || startMutation.isPending}
              className="btn-primary flex items-center gap-2"
            >
              <MessageSquare className="w-4 h-4" />
              Start Brainstorm
            </button>
          )}
        </div>

        {/* Running Status Bar */}
        {isRunning && (
          <div className="mt-3 flex items-center justify-between text-sm">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-2 text-freya-accent-blue">
                <Activity className="w-4 h-4 animate-pulse" />
                Pipeline running...
              </span>
              {elapsedTime && (
                <span className="flex items-center gap-1 text-freya-text-muted">
                  <Timer className="w-4 h-4" />
                  {elapsedTime}
                </span>
              )}
              {currentAgent && (
                <span className="flex items-center gap-1 text-freya-accent-cyan">
                  <Brain className="w-4 h-4 animate-pulse" />
                  {AGENTS.find(a => a.id === currentAgent)?.name} thinking...
                </span>
              )}
            </div>
            <div className="flex items-center gap-2">
              <span className="text-freya-text-muted">
                {completedAgents.length}/{AGENTS.length} agents completed
              </span>
              <div className="w-32 h-2 bg-freya-bg-tertiary rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-freya-accent-blue to-freya-accent-cyan transition-all"
                  style={{ width: `${(completedAgents.length / AGENTS.length) * 100}%` }}
                />
              </div>
            </div>
          </div>
        )}
        
        {/* Research Mode Integration Banner */}
        {researchState?.isActive && researchState.phase === 'bmad' && !isRunning && (
          <div className="mt-3 p-3 bg-freya-accent-green/10 border border-freya-accent-green/30 rounded-lg animate-fade-in">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-freya-accent-green/20 flex items-center justify-center">
                  <Rocket className="w-5 h-5 text-freya-accent-green" />
                </div>
                <div>
                  <div className="font-medium text-freya-accent-green">Research Brief Ready</div>
                  <div className="text-sm text-freya-text-muted">
                    A market research brief is ready from Research mode. Click to import and launch BMAD.
                  </div>
                </div>
              </div>
              <button
                onClick={() => {
                  if (researchState.selectedIdea) {
                    setGoal(researchState.selectedIdea)
                    setMode('brainstorm')
                  }
                }}
                className="btn-primary flex items-center gap-2"
              >
                <Zap className="w-4 h-4" />
                Import Brief
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden flex">
        {/* Analyst Panel Toggle Button (when panel is hidden) */}
        {!showAnalystPanel && (
          <button
            onClick={() => setShowAnalystPanel(true)}
            className="absolute left-0 top-1/2 -translate-y-1/2 z-10 p-2 bg-freya-bg-secondary border border-freya-border rounded-r-lg shadow-lg hover:bg-freya-bg-tertiary"
            title="Show Analyst Panel"
          >
            <PanelLeft className="w-5 h-5 text-freya-accent-blue" />
          </button>
        )}
        
        {/* Brainstorm Chat - Always visible with hide option */}
        {showAnalystPanel && (
          <div className={clsx(
            'border-r border-freya-border flex flex-col bg-freya-bg-secondary transition-all relative',
            mode === 'brainstorm' ? 'w-96' : 'w-80'
          )}>
            {/* Panel Header with Hide Button */}
            <div className="p-4 border-b border-freya-border">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-freya-text-primary flex items-center gap-2">
                  <MessageSquare className="w-5 h-5 text-freya-accent-blue" />
                  Analyst Panel
                </h3>
                <button
                  onClick={() => setShowAnalystPanel(false)}
                  className="p-1 rounded hover:bg-freya-bg-tertiary"
                  title="Hide Analyst Panel"
                >
                  <PanelLeftClose className="w-4 h-4 text-freya-text-muted" />
                </button>
              </div>
              <p className="text-xs text-freya-text-muted mt-1">
                Clarify your requirements before starting the pipeline
              </p>
            </div>
            
            {/* Recent Projects Section */}
            <div className="border-b border-freya-border">
              <button
                onClick={() => setShowRecentProjects(!showRecentProjects)}
                className="w-full flex items-center justify-between p-3 hover:bg-freya-bg-tertiary/50"
              >
                <span className="flex items-center gap-2 text-sm text-freya-text-secondary">
                  <History className="w-4 h-4" />
                  Recent Projects
                </span>
                <ChevronDown className={clsx('w-4 h-4 text-freya-text-muted transition-transform', showRecentProjects && 'rotate-180')} />
              </button>
              
              {showRecentProjects && (
                <div className="px-3 pb-3 space-y-2 max-h-64 overflow-y-auto">
                  {recentProjects.length > 0 ? (
                    recentProjects.map((project, idx) => (
                      <div
                        key={idx}
                        className={clsx(
                          "w-full text-left p-2 rounded border transition-all",
                          selectedProject?.name === project.name
                            ? "bg-freya-accent-blue/10 border-freya-accent-blue/30"
                            : "bg-freya-bg-primary border-transparent hover:bg-freya-bg-tertiary"
                        )}
                      >
                        <button
                          onClick={async () => {
                            setProjectName(project.name)
                            setGoal(project.goal)
                            setSelectedProject(project)
                            
                            // Check if project can be resumed
                            setCheckingResume(true)
                            try {
                              const info = await api.checkBMADResume(project.name)
                              setResumeInfo(info)
                            } catch {
                              setResumeInfo(null)
                            }
                            setCheckingResume(false)
                          }}
                          className="w-full text-left"
                        >
                          <div className="flex items-center gap-2">
                            <FolderOpen className="w-4 h-4 text-freya-accent-yellow" />
                            <span className="font-medium text-freya-text-primary text-sm truncate">{project.name}</span>
                          </div>
                          <p className="text-xs text-freya-text-muted mt-1 truncate">{project.goal}</p>
                          <p className="text-xs text-freya-text-muted/60 mt-0.5">
                            {new Date(project.lastModified).toLocaleDateString()}
                          </p>
                        </button>
                        
                        {/* Resume info for selected project */}
                        {selectedProject?.name === project.name && (
                          <div className="mt-2 pt-2 border-t border-freya-border">
                            {checkingResume ? (
                              <div className="flex items-center gap-2 text-xs text-freya-text-muted">
                                <Loader2 className="w-3 h-3 animate-spin" />
                                Vérification...
                              </div>
                            ) : resumeInfo?.can_resume ? (
                              <div className="space-y-2">
                                <div className="text-xs text-freya-text-muted">
                                  <span className="text-freya-accent-green">✓</span> Peut reprendre depuis: <strong>{resumeInfo.next_agent}</strong>
                                </div>
                                <div className="text-xs text-freya-text-muted">
                                  Complétés: {resumeInfo.completed_agents.join(', ') || 'Aucun'}
                                </div>
                                <div className="flex gap-2">
                                  <button
                                    onClick={() => {
                                      setBrainstormComplete(true)
                                      setShowRecentProjects(false)
                                      // Start from where we left off
                                      startMutation.mutate()
                                    }}
                                    className="flex-1 btn-primary text-xs py-1"
                                  >
                                    <Repeat className="w-3 h-3 mr-1" />
                                    Reprendre
                                  </button>
                                  <button
                                    onClick={() => {
                                      setShowRecentProjects(false)
                                      setMode('brainstorm')
                                    }}
                                    className="flex-1 btn-secondary text-xs py-1"
                                  >
                                    Modifier
                                  </button>
                                </div>
                              </div>
                            ) : (
                              <div className="flex gap-2">
                                <button
                                  onClick={() => {
                                    setBrainstormComplete(true)
                                    setShowRecentProjects(false)
                                    startMutation.mutate()
                                  }}
                                  className="flex-1 btn-primary text-xs py-1"
                                >
                                  <Play className="w-3 h-3 mr-1" />
                                  Relancer
                                </button>
                                <button
                                  onClick={() => {
                                    setShowRecentProjects(false)
                                    setMode('brainstorm')
                                  }}
                                  className="flex-1 btn-secondary text-xs py-1"
                                >
                                  Modifier
                                </button>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-freya-text-muted text-center py-2">No recent projects</p>
                  )}
                  
                  {/* New Project Button */}
                  <button
                    onClick={() => {
                      setProjectName('NewProject')
                      setGoal('')
                      setChatMessages([])
                      setBrainstormComplete(false)
                      setMode('brainstorm')
                      setShowRecentProjects(false)
                      setSelectedProject(null)
                      setResumeInfo(null)
                    }}
                    className="w-full text-left p-2 rounded border border-dashed border-freya-border hover:border-freya-accent-blue hover:bg-freya-accent-blue/5"
                  >
                    <div className="flex items-center gap-2 text-freya-accent-blue">
                      <Sparkles className="w-4 h-4" />
                      <span className="text-sm">Start New Project</span>
                    </div>
                  </button>
                </div>
              )}
            </div>

            {/* Chat Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {chatMessages.map((msg, idx) => (
                <div
                  key={idx}
                  className={clsx(
                    'flex',
                    msg.role === 'user' ? 'justify-end' : 'justify-start'
                  )}
                >
                  <div
                    className={clsx(
                      'max-w-[85%] rounded-lg p-3',
                      msg.role === 'user'
                        ? 'bg-freya-accent-blue text-white'
                        : msg.role === 'system'
                        ? 'bg-freya-accent-red/20 text-freya-accent-red'
                        : 'bg-freya-bg-tertiary text-freya-text-primary'
                    )}
                  >
                    {msg.agent && (
                      <div className="text-xs text-freya-accent-cyan mb-1 font-medium">
                        {AGENTS.find(a => a.id === msg.agent)?.name}
                      </div>
                    )}
                    <div className="prose-freya text-sm">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {msg.content.replace('BRAINSTORM_COMPLETE', '')}
                      </ReactMarkdown>
                    </div>
                    <div className="text-xs opacity-60 mt-1">
                      {format(msg.timestamp, 'HH:mm')}
                    </div>
                  </div>
                </div>
              ))}
              {isBrainstorming && (
                <div className="flex justify-start">
                  <div className="bg-freya-bg-tertiary rounded-lg p-3">
                    <Loader2 className="w-5 h-5 animate-spin text-freya-accent-blue" />
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            {/* Chat Input */}
            <div className="p-4 border-t border-freya-border">
              {brainstormComplete && (
                <div className="mb-3 p-2 bg-freya-accent-green/10 rounded-lg text-sm text-freya-accent-green flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4" />
                  Brainstorming complete! Ready to launch pipeline.
                </div>
              )}
              
              {/* Quick Suggestions - Clickable */}
              {quickSuggestions.length > 0 && !brainstormComplete && !isBrainstorming && (
                <div className="mb-3">
                  <div className="text-xs text-freya-text-muted mb-2 flex items-center gap-1">
                    <Sparkles className="w-3 h-3" />
                    Quick responses:
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {quickSuggestions.map((suggestion, idx) => (
                      <button
                        key={idx}
                        onClick={() => {
                          setChatInput(suggestion)
                          // Optionally auto-send
                          // sendBrainstormMessage()
                        }}
                        className="text-xs px-2 py-1 rounded-full bg-freya-bg-tertiary text-freya-text-secondary hover:bg-freya-accent-blue/20 hover:text-freya-accent-blue transition-colors truncate max-w-[200px]"
                        title={suggestion}
                      >
                        {suggestion.slice(0, 40)}{suggestion.length > 40 ? '...' : ''}
                      </button>
                    ))}
                  </div>
                </div>
              )}
              
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && sendBrainstormMessage()}
                  placeholder="Type your response..."
                  className="input flex-1"
                  disabled={isBrainstorming || isRunning}
                />
                <button
                  onClick={sendBrainstormMessage}
                  disabled={!chatInput.trim() || isBrainstorming || isRunning}
                  className="btn-primary p-2"
                >
                  <Send className="w-5 h-5" />
                </button>
              </div>
              
              {/* Chat History Access */}
              {analystHistory.length > 0 && (
                <div className="mt-2 flex items-center justify-between">
                  <button
                    onClick={() => setShowAnalystHistory(!showAnalystHistory)}
                    className="text-xs text-freya-text-muted hover:text-freya-accent-blue flex items-center gap-1"
                  >
                    <History className="w-3 h-3" />
                    {showAnalystHistory ? 'Hide history' : 'Load from history'}
                  </button>
                  {mode !== 'brainstorm' && chatMessages.length > 0 && (
                    <button
                      onClick={() => setMode('brainstorm')}
                      className="text-xs text-freya-accent-blue hover:underline"
                    >
                      Continue brainstorming
                    </button>
                  )}
                </div>
              )}
              
              {/* Chat History Dropdown */}
              {showAnalystHistory && (
                <div className="mt-2 p-2 bg-freya-bg-primary rounded border border-freya-border max-h-32 overflow-y-auto">
                  {analystHistory.map((h, idx) => (
                    <button
                      key={idx}
                      onClick={() => {
                        setProjectName(h.projectName)
                        setChatMessages(h.messages.map(m => ({ ...m, timestamp: new Date(m.timestamp) })))
                        setShowAnalystHistory(false)
                      }}
                      className="w-full text-left p-2 rounded hover:bg-freya-bg-tertiary text-xs"
                    >
                      <div className="font-medium text-freya-text-primary">{h.projectName}</div>
                      <div className="text-freya-text-muted truncate">
                        {h.messages.length} messages • {new Date(h.updatedAt).toLocaleDateString()}
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Left - Pipeline Visualization */}
        <div className={clsx(
          'border-r border-freya-border bg-freya-bg-secondary p-4 overflow-y-auto transition-all',
          mode === 'brainstorm' ? 'w-64' : 'w-80',
          pipelineViewMode === 'compact' && 'w-20'
        )}>
          <div className="flex items-center justify-between mb-4">
            <h3 className={clsx(
              "font-semibold text-freya-text-primary flex items-center gap-2",
              pipelineViewMode === 'compact' && 'hidden'
            )}>
              <GitBranch className="w-5 h-5 text-freya-accent-cyan" />
              Agent Pipeline
            </h3>
            <button
              onClick={() => setPipelineViewMode(pipelineViewMode === 'compact' ? 'expanded' : 'compact')}
              className="p-1.5 rounded hover:bg-freya-bg-tertiary"
              title={pipelineViewMode === 'compact' ? 'Expand pipeline' : 'Collapse pipeline'}
            >
              {pipelineViewMode === 'compact' ? (
                <Maximize2 className="w-4 h-4 text-freya-text-muted" />
              ) : (
                <Minimize2 className="w-4 h-4 text-freya-text-muted" />
              )}
            </button>
          </div>
          
          {/* Quick Progress Overview (always visible) */}
          {pipelineViewMode === 'compact' ? (
            <div className="space-y-2">
              {AGENTS.map((agent) => {
                const Icon = agent.icon
                const agentStatus = getAgentStatus(agent.id)
                return (
                  <div
                    key={agent.id}
                    className={clsx(
                      'w-12 h-12 rounded-lg flex items-center justify-center transition-all cursor-pointer',
                      agentStatus === 'completed' && 'bg-freya-accent-green/20 border border-freya-accent-green/50',
                      agentStatus === 'running' && 'bg-freya-accent-blue/20 border border-freya-accent-blue/50 animate-pulse',
                      agentStatus === 'error' && 'bg-freya-accent-red/20 border border-freya-accent-red/50',
                      agentStatus === 'pending' && 'bg-freya-bg-tertiary border border-freya-border'
                    )}
                    onClick={() => {
                      setPipelineViewMode('expanded')
                      setExpandedAgent(agent.id)
                    }}
                    title={`${agent.name}: ${agentStatus}`}
                  >
                    {agentStatus === 'running' ? (
                      <RefreshCw className="w-5 h-5 text-freya-accent-blue animate-spin" />
                    ) : agentStatus === 'completed' ? (
                      <CheckCircle2 className="w-5 h-5 text-freya-accent-green" />
                    ) : agentStatus === 'error' ? (
                      <AlertCircle className="w-5 h-5 text-freya-accent-red" />
                    ) : (
                      <Icon className={clsx('w-5 h-5', agent.color)} />
                    )}
                  </div>
                )
              })}
            </div>
          ) : (
            /* Full pipeline view */
            <>

          <div className="space-y-2">
            {AGENTS.map((agent, index) => {
              const Icon = agent.icon
              const agentStatus = getAgentStatus(agent.id)
              const isExpanded = expandedAgent === agent.id
              const agentErrors = pipelineErrors.filter(e => e.agent === agent.id)
              
              return (
                <div key={agent.id}>
                  {/* Agent Card */}
                  <button
                    onClick={() => setExpandedAgent(isExpanded ? null : agent.id)}
                    className={clsx(
                      'w-full relative p-4 rounded-lg border transition-all text-left',
                      agentStatus === 'completed' && 'bg-freya-accent-green/10 border-freya-accent-green/30',
                      agentStatus === 'running' && 'bg-freya-accent-blue/10 border-freya-accent-blue/30',
                      agentStatus === 'error' && 'bg-freya-accent-red/10 border-freya-accent-red/30',
                      agentStatus === 'pending' && 'bg-freya-bg-primary border-freya-border opacity-60'
                    )}
                  >
                    <div className="flex items-start gap-3">
                      {/* Status Icon */}
                      <div className={clsx(
                        'w-10 h-10 rounded-full flex items-center justify-center',
                        agentStatus === 'completed' && 'bg-freya-accent-green/20',
                        agentStatus === 'running' && 'bg-freya-accent-blue/20',
                        agentStatus === 'error' && 'bg-freya-accent-red/20',
                        agentStatus === 'pending' && 'bg-freya-bg-tertiary'
                      )}>
                        {agentStatus === 'running' ? (
                          <RefreshCw className="w-5 h-5 text-freya-accent-blue animate-spin" />
                        ) : agentStatus === 'completed' ? (
                          <CheckCircle2 className="w-5 h-5 text-freya-accent-green" />
                        ) : agentStatus === 'error' ? (
                          <AlertCircle className="w-5 h-5 text-freya-accent-red" />
                        ) : (
                          <Icon className={clsx('w-5 h-5', agent.color)} />
                        )}
                      </div>

                      {/* Agent Info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <div className="font-medium text-freya-text-primary">
                            {agent.name}
                          </div>
                          {agentErrors.length > 0 && (
                            <span className="badge badge-red text-xs">
                              {agentErrors.length} error{agentErrors.length > 1 ? 's' : ''}
                            </span>
                          )}
                        </div>
                        <div className="text-xs text-freya-text-muted truncate">
                          {agent.description}
                        </div>
                        <div className="text-xs text-freya-text-secondary mt-1 font-mono">
                          {agent.output}
                        </div>
                      </div>

                      <ChevronDown className={clsx(
                        'w-4 h-4 text-freya-text-muted transition-transform',
                        isExpanded && 'rotate-180'
                      )} />
                    </div>
                  </button>

                  {/* Expanded Details */}
                  {isExpanded && (
                    <div className="mt-2 ml-4 p-3 bg-freya-bg-primary rounded-lg border border-freya-border animate-fade-in">
                      <h4 className="text-xs font-medium text-freya-text-secondary mb-2">Agent Logs</h4>
                      {agentLogs.filter(l => l.agent === agent.id).length > 0 ? (
                        <div className="space-y-1 max-h-40 overflow-y-auto">
                          {agentLogs.filter(l => l.agent === agent.id).map((log, i) => (
                            <div key={i} className="text-xs">
                              <span className="text-freya-text-muted">{format(log.timestamp, 'HH:mm:ss')}</span>
                              <span className="text-freya-text-primary ml-2">{log.message}</span>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-xs text-freya-text-muted">No logs yet</p>
                      )}
                      
                      {agentErrors.length > 0 && (
                        <div className="mt-2 pt-2 border-t border-freya-border">
                          <h4 className="text-xs font-medium text-freya-accent-red mb-1">Errors</h4>
                          {agentErrors.map((err, i) => (
                            <div key={i} className="text-xs text-freya-accent-red">
                              {err.error}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Connector */}
                  {index < AGENTS.length - 1 && (
                    <div className="flex justify-center py-1">
                      <ArrowRight className="w-4 h-4 text-freya-border rotate-90" />
                    </div>
                  )}
                </div>
              )
            })}
          </div>

          {/* Error Summary & Export */}
          {pipelineErrors.length > 0 && (
            <div className="mt-4 p-3 rounded-lg bg-freya-accent-red/10 border border-freya-accent-red/30">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2 text-freya-accent-red">
                  <AlertTriangle className="w-4 h-4" />
                  <span className="font-medium text-sm">{pipelineErrors.length} Errors</span>
                </div>
                <button
                  onClick={exportErrorsJSON}
                  className="text-xs text-freya-accent-red hover:underline flex items-center gap-1"
                >
                  <FileJson className="w-3 h-3" />
                  Export JSON
                </button>
              </div>
            </div>
          )}
          
          {/* Live Pipeline Logs */}
          {bmadProgress?.logs && bmadProgress.logs.length > 0 && (
            <div className="mt-4 p-3 rounded-lg bg-freya-bg-primary border border-freya-border">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2 text-freya-accent-cyan">
                  <Activity className="w-4 h-4" />
                  <span className="font-medium text-sm">Live Logs ({bmadProgress.logs.length})</span>
                </div>
                {bmadProgress.running && (
                  <span className="badge badge-green text-xs animate-pulse">Running</span>
                )}
              </div>
              <div className="max-h-48 overflow-y-auto space-y-1 font-mono text-xs">
                {bmadProgress.logs.slice(-20).map((log, i) => (
                  <div 
                    key={i} 
                    className={clsx(
                      'flex gap-2 py-0.5',
                      log.level === 'error' && 'text-freya-accent-red',
                      log.level === 'success' && 'text-freya-accent-green',
                      log.level === 'info' && 'text-freya-text-primary'
                    )}
                  >
                    <span className="text-freya-text-muted w-16 flex-shrink-0">{log.timestamp}</span>
                    <span className="text-freya-accent-blue w-16 flex-shrink-0">{log.agent || '-'}</span>
                    <span className="flex-1 break-words">{log.message}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
            </>
          )}
        </div>

        {/* Center - Artifacts List */}
        <div className="w-72 border-r border-freya-border p-4 overflow-y-auto">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-freya-text-primary flex items-center gap-2">
              <FileText className="w-5 h-5 text-freya-accent-purple" />
              Artifacts
            </h3>
            <button
              onClick={() => refetchArtifacts()}
              className="p-1 hover:bg-freya-bg-tertiary rounded"
            >
              <RefreshCw className="w-4 h-4 text-freya-text-muted" />
            </button>
          </div>

          {artifacts && artifacts.length > 0 ? (
            <div className="space-y-2">
              {artifacts.map((artifact) => (
                <button
                  key={artifact.path}
                  onClick={() => setSelectedArtifact(artifact.path)}
                  className={clsx(
                    'w-full text-left p-3 rounded-lg border transition-all',
                    selectedArtifact === artifact.path
                      ? 'bg-freya-accent-blue/10 border-freya-accent-blue/30'
                      : 'bg-freya-bg-primary border-freya-border hover:border-freya-border-light'
                  )}
                >
                  <div className="flex items-center gap-2">
                    <FileText className={clsx(
                      'w-4 h-4',
                      selectedArtifact === artifact.path
                        ? 'text-freya-accent-blue'
                        : 'text-freya-text-muted'
                    )} />
                    <span className="font-medium text-freya-text-primary text-sm truncate">
                      {artifact.name}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 mt-1 text-xs text-freya-text-muted">
                    <span>{(artifact.size_bytes / 1024).toFixed(1)} KB</span>
                    <span>{new Date(artifact.modified_at).toLocaleDateString()}</span>
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-freya-text-muted">
              <BookOpen className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p>No artifacts yet</p>
              <p className="text-sm mt-1">Run the pipeline to generate artifacts</p>
            </div>
          )}
        </div>

        {/* Right - Artifact Preview */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {selectedArtifact ? (
            <>
              {/* Preview Header */}
              <div className="flex items-center justify-between p-4 border-b border-freya-border bg-freya-bg-secondary">
                <div className="flex items-center gap-2">
                  <Eye className="w-5 h-5 text-freya-text-muted" />
                  <span className="font-medium text-freya-text-primary">
                    {selectedArtifact.split('/').pop()}
                  </span>
                </div>
                <button 
                  onClick={() => {
                    const blob = new Blob([artifactContent], { type: 'text/markdown' })
                    const url = URL.createObjectURL(blob)
                    const a = document.createElement('a')
                    a.href = url
                    a.download = selectedArtifact.split('/').pop() || 'artifact.md'
                    a.click()
                    URL.revokeObjectURL(url)
                  }}
                  className="btn-secondary text-sm flex items-center gap-2"
                >
                  <Download className="w-4 h-4" />
                  Download
                </button>
              </div>

              {/* Preview Content */}
              <div className="flex-1 overflow-y-auto p-6">
                <div className="max-w-4xl mx-auto prose-freya">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {artifactContent}
                  </ReactMarkdown>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-freya-text-muted">
              <div className="text-center">
                <ChevronRight className="w-16 h-16 mx-auto mb-4 opacity-20" />
                <h3 className="text-lg font-medium text-freya-text-secondary mb-2">
                  Select an artifact to preview
                </h3>
                <p className="text-sm">
                  Click on an artifact from the list to view its contents
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
