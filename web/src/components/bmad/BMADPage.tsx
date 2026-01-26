/**
 * BMADPage - BMAD Studio
 * 
 * Professional interface for managing the BMAD (Business Model - Architecture - Development)
 * workflow. Visualizes the agent pipeline and generated artifacts.
 */

import { useState, useEffect } from 'react'
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
  ArrowRight
} from 'lucide-react'
import { useQuery, useMutation } from '@tanstack/react-query'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { clsx } from 'clsx'
import * as api from '../../lib/api'
import { useAppStore } from '../../stores/appStore'

// BMAD Agent definitions
interface AgentDef {
  id: string
  name: string
  role: string
  icon: typeof FileText
  color: string
  output: string
  description: string
}

const AGENTS: AgentDef[] = [
  {
    id: 'analyst',
    name: 'Analyst',
    role: 'analyst',
    icon: Target,
    color: 'text-freya-accent-blue',
    output: 'project-brief.md',
    description: 'Analyzes goals and creates project brief'
  },
  {
    id: 'pm',
    name: 'Product Manager',
    role: 'pm',
    icon: ClipboardList,
    color: 'text-freya-accent-purple',
    output: 'PRD.md',
    description: 'Creates Product Requirements Document'
  },
  {
    id: 'architect',
    name: 'Architect',
    role: 'architect',
    icon: Building2,
    color: 'text-freya-accent-cyan',
    output: 'architecture.md',
    description: 'Designs system architecture'
  },
  {
    id: 'po',
    name: 'Product Owner',
    role: 'po',
    icon: Layers,
    color: 'text-freya-accent-yellow',
    output: 'epics/',
    description: 'Breaks down into epics'
  },
  {
    id: 'sm',
    name: 'Scrum Master',
    role: 'sm',
    icon: Users,
    color: 'text-freya-accent-green',
    output: 'stories/',
    description: 'Creates user stories'
  },
  {
    id: 'dev',
    name: 'Developer',
    role: 'dev',
    icon: Code2,
    color: 'text-freya-accent-red',
    output: 'code/',
    description: 'Implements the code'
  },
  {
    id: 'qa',
    name: 'QA Engineer',
    role: 'qa',
    icon: TestTube2,
    color: 'text-freya-accent-purple',
    output: 'QA.md',
    description: 'Runs quality assurance'
  }
]

export function BMADPage() {
  const { bmadProgress, setBMADProgress } = useAppStore()
  const [goal, setGoal] = useState('')
  const [projectName, setProjectName] = useState('FreyaProject')
  const [selectedArtifact, setSelectedArtifact] = useState<string | null>(null)
  const [artifactContent, setArtifactContent] = useState<string>('')

  // Fetch BMAD status
  const { data: status, refetch: refetchStatus } = useQuery({
    queryKey: ['bmadStatus'],
    queryFn: api.getBMADStatus,
    refetchInterval: bmadProgress?.running ? 2000 : 10000,
  })

  // Fetch artifacts
  const { data: artifacts, refetch: refetchArtifacts } = useQuery({
    queryKey: ['artifacts'],
    queryFn: () => api.getArtifacts(),
  })

  // Update store when status changes
  useEffect(() => {
    if (status) {
      setBMADProgress(status.running ? {
        running: status.running,
        current_agent: status.current_agent,
        agents_completed: status.agents_completed,
        artifacts_generated: status.artifacts_generated,
      } : null)
    }
  }, [status, setBMADProgress])

  // Start BMAD mutation
  const startMutation = useMutation({
    mutationFn: () => api.runBMAD(goal, projectName),
    onSuccess: () => {
      refetchStatus()
      refetchArtifacts()
    },
  })

  // Load artifact content
  useEffect(() => {
    if (selectedArtifact) {
      api.getArtifact(selectedArtifact)
        .then(data => setArtifactContent(data.content))
        .catch(() => setArtifactContent('Error loading artifact'))
    }
  }, [selectedArtifact])

  const isRunning = status?.running ?? false
  const completedAgents = status?.agents_completed ?? []
  const currentAgent = status?.current_agent

  // Get agent status
  const getAgentStatus = (agentId: string): 'completed' | 'running' | 'pending' | 'error' => {
    if (completedAgents.includes(agentId)) return 'completed'
    if (currentAgent === agentId) return 'running'
    if (status?.error && currentAgent === agentId) return 'error'
    return 'pending'
  }

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

          {/* Start Button */}
          {isRunning ? (
            <button
              onClick={() => {/* stopMutation.mutate() */}}
              className="btn-danger flex items-center gap-2"
            >
              <Square className="w-4 h-4" />
              Stop
            </button>
          ) : (
            <button
              onClick={() => goal.trim() && startMutation.mutate()}
              disabled={!goal.trim() || startMutation.isPending}
              className="btn-primary flex items-center gap-2"
            >
              <Play className="w-4 h-4" />
              Run BMAD Pipeline
            </button>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden flex">
        {/* Left - Pipeline Visualization */}
        <div className="w-80 border-r border-freya-border bg-freya-bg-secondary p-4 overflow-y-auto">
          <h3 className="font-semibold text-freya-text-primary mb-4 flex items-center gap-2">
            <GitBranch className="w-5 h-5 text-freya-accent-cyan" />
            Agent Pipeline
          </h3>

          <div className="space-y-2">
            {AGENTS.map((agent, index) => {
              const Icon = agent.icon
              const agentStatus = getAgentStatus(agent.id)
              
              return (
                <div key={agent.id}>
                  {/* Agent Card */}
                  <div
                    className={clsx(
                      'relative p-4 rounded-lg border transition-all',
                      agentStatus === 'completed' && 'bg-freya-accent-green/10 border-freya-accent-green/30',
                      agentStatus === 'running' && 'bg-freya-accent-blue/10 border-freya-accent-blue/30 animate-pulse',
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
                        <div className="font-medium text-freya-text-primary">
                          {agent.name}
                        </div>
                        <div className="text-xs text-freya-text-muted truncate">
                          {agent.description}
                        </div>
                        <div className="text-xs text-freya-text-secondary mt-1 font-mono">
                          {agent.output}
                        </div>
                      </div>
                    </div>
                  </div>

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

          {/* Error Display */}
          {status?.error && (
            <div className="mt-4 p-3 rounded-lg bg-freya-accent-red/10 border border-freya-accent-red/30">
              <div className="flex items-center gap-2 text-freya-accent-red mb-1">
                <AlertCircle className="w-4 h-4" />
                <span className="font-medium text-sm">Error</span>
              </div>
              <p className="text-sm text-freya-text-secondary">{status.error}</p>
            </div>
          )}
        </div>

        {/* Center - Artifacts List */}
        <div className="w-72 border-r border-freya-border p-4 overflow-y-auto">
          <h3 className="font-semibold text-freya-text-primary mb-4 flex items-center gap-2">
            <FileText className="w-5 h-5 text-freya-accent-purple" />
            Generated Artifacts
          </h3>

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
                <button className="btn-secondary text-sm flex items-center gap-2">
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
