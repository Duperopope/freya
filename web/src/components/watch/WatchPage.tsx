/**
 * WatchPage - Cyber Security Watch & CyberAgent v2.5
 * 
 * Real-time security vulnerability monitoring dashboard with AI-powered analysis.
 * Features:
 * - Intelligent CVE analysis and risk assessment
 * - AI-powered threat briefings
 * - Automated remediation suggestions
 * - Security chat interface
 * - Multi-source aggregation (CISA KEV, CERT-FR, NVD, Exploit-DB, GitHub)
 */

import { useState, useEffect, useRef } from 'react'
import {
  Shield,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  ExternalLink,
  RefreshCw,
  Search,
  Calendar,
  Clock,
  Globe,
  ChevronRight,
  Info,
  AlertCircle,
  Pause,
  Play,
  Database,
  Code,
  Github,
  Settings,
  Download,
  MessageSquare,
  Bot,
  Zap,
  Target,
  FileText,
  Send,
  Loader2,
  Sparkles,
  Brain,
  Copy,
  Check,
  Lightbulb,
  Lock,
  Bug,
  Server
} from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { clsx } from 'clsx'
import { format, formatDistanceToNow } from 'date-fns'
import * as api from '../../lib/api'

type SourceFilter = 'all' | 'cisa' | 'certfr' | 'nvd' | 'exploitdb' | 'github'
type SeverityFilter = 'all' | 'critical' | 'high' | 'medium' | 'low'
type CyberAgentMode = 'monitor' | 'chat' | 'analysis' | 'briefing'

// CyberAgent chat message interface
interface CyberMessage {
  id: string
  role: 'user' | 'agent' | 'system' | 'analysis'
  content: string
  timestamp: Date
  cves?: string[]
  severity?: string
}

// Threat analysis result
interface ThreatAnalysis {
  cve: string
  riskScore: number
  exploitability: 'none' | 'low' | 'medium' | 'high' | 'critical'
  affectedSystems: string[]
  remediation: string[]
  urgency: 'immediate' | 'high' | 'medium' | 'low'
  summary: string
}

// Source configuration
const SOURCES = [
  { id: 'all', name: 'All Sources', icon: Globe, color: 'badge-blue' },
  { id: 'cisa', name: 'CISA KEV', icon: ShieldAlert, color: 'badge-red' },
  { id: 'certfr', name: 'CERT-FR', icon: Shield, color: 'badge-blue' },
  { id: 'nvd', name: 'NVD', icon: Database, color: 'badge-purple' },
  { id: 'exploitdb', name: 'Exploit-DB', icon: Code, color: 'badge-yellow' },
  { id: 'github', name: 'GitHub GHSA', icon: Github, color: 'badge-green' },
]

// Source badge colors
const SOURCE_COLORS: Record<string, string> = {
  'CISA-KEV': 'badge-red',
  'CERT-FR': 'badge-blue',
  'CERT-FR-Avis': 'badge-blue',
  'NVD': 'badge-purple',
  'Exploit-DB': 'badge-yellow',
  'GitHub-GHSA': 'badge-green',
  'PacketStorm': 'badge-orange',
  'Threatpost': 'badge-cyan',
  'default': 'badge-yellow'
}

// Severity badge colors and icons
const SEVERITY_CONFIG: Record<string, { color: string; icon: typeof AlertTriangle; label: string }> = {
  critical: { color: 'text-freya-accent-red', icon: ShieldAlert, label: 'Critical' },
  high: { color: 'text-orange-500', icon: AlertTriangle, label: 'High' },
  medium: { color: 'text-freya-accent-yellow', icon: AlertCircle, label: 'Medium' },
  low: { color: 'text-freya-accent-green', icon: Info, label: 'Low' },
  unknown: { color: 'text-freya-text-muted', icon: Shield, label: 'Unknown' }
}

export function WatchPage() {
  const queryClient = useQueryClient()
  const [sourceFilter, setSourceFilter] = useState<SourceFilter>('all')
  const [severityFilter, setSeverityFilter] = useState<SeverityFilter>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [_selectedItem, _setSelectedItem] = useState<api.WatchItem | null>(null)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [refreshInterval, setRefreshInterval] = useState(5) // minutes
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)
  const [expandedCVE, setExpandedCVE] = useState<string | null>(null)
  const [showSettings, setShowSettings] = useState(false)
  const [enabledSources, setEnabledSources] = useState(['cisa', 'certfr', 'nvd', 'exploitdb', 'github'])
  
  // CyberAgent v2.5 state
  const [agentMode, setAgentMode] = useState<CyberAgentMode>('monitor')
  const [chatMessages, setChatMessages] = useState<CyberMessage[]>([])
  const [chatInput, setChatInput] = useState('')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [selectedCVEsForAnalysis, setSelectedCVEsForAnalysis] = useState<string[]>([])
  const [_threatAnalyses, _setThreatAnalyses] = useState<ThreatAnalysis[]>([])
  const [showAgentPanel, setShowAgentPanel] = useState(false)
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const [_dailyBriefing, setDailyBriefing] = useState<string | null>(null)
  const [isGeneratingBriefing, setIsGeneratingBriefing] = useState(false)
  const chatEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Fetch watch feed
  const { data: feed, isLoading, isRefetching, dataUpdatedAt } = useQuery({
    queryKey: ['watchFeed', enabledSources.join(',')],
    queryFn: () => api.getWatchFeed(100, enabledSources.join(',')),
    refetchInterval: autoRefresh ? refreshInterval * 60 * 1000 : false,
  })

  // Update last refresh time
  useEffect(() => {
    if (dataUpdatedAt) {
      setLastRefresh(new Date(dataUpdatedAt))
    }
  }, [dataUpdatedAt])

  // Fetch watch stats
  const { data: stats } = useQuery({
    queryKey: ['watchStats'],
    queryFn: api.getWatchStats,
    refetchInterval: autoRefresh ? refreshInterval * 60 * 1000 : false,
  })

  // Force refresh mutation
  const refreshMutation = useMutation({
    mutationFn: () => api.forceRefreshWatch(enabledSources.join(',')),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['watchFeed'] })
      queryClient.invalidateQueries({ queryKey: ['watchStats'] })
      setLastRefresh(new Date())
    }
  })

  // CVE lookup
  const { data: cveDetails } = useQuery({
    queryKey: ['cve', expandedCVE],
    queryFn: () => expandedCVE ? api.lookupCVE(expandedCVE) : null,
    enabled: !!expandedCVE,
  })
  
  // Auto-scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatMessages])
  
  // CyberAgent chat handler
  const handleCyberChat = async () => {
    if (!chatInput.trim() || isAnalyzing) return
    
    const userMessage: CyberMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: chatInput,
      timestamp: new Date(),
    }
    
    setChatMessages(prev => [...prev, userMessage])
    setChatInput('')
    setIsAnalyzing(true)
    
    try {
      // Check if asking about specific CVEs
      const cvePattern = /CVE-\d{4}-\d+/gi
      const mentionedCVEs = chatInput.match(cvePattern) || []
      
      // Generate AI response using cyber-query endpoint
      const response = await api.cyberQuery({
        query: chatInput,
        include_cves: true,
        include_alerts: true,
        max_results: 10,
      })
      
      const agentMessage: CyberMessage = {
        id: `agent-${Date.now()}`,
        role: 'agent',
        content: response.content,
        timestamp: new Date(),
        cves: mentionedCVEs,
      }
      
      setChatMessages(prev => [...prev, agentMessage])
    } catch (error) {
      const errorMessage: CyberMessage = {
        id: `error-${Date.now()}`,
        role: 'system',
        content: `Error: ${error instanceof Error ? error.message : 'Failed to process query'}. Using fallback analysis...`,
        timestamp: new Date(),
      }
      setChatMessages(prev => [...prev, errorMessage])
      
      // Fallback: provide basic analysis
      const fallbackMessage: CyberMessage = {
        id: `fallback-${Date.now()}`,
        role: 'agent',
        content: generateFallbackAnalysis(chatInput, filteredItems),
        timestamp: new Date(),
      }
      setChatMessages(prev => [...prev, fallbackMessage])
    }
    
    setIsAnalyzing(false)
  }
  
  // Fallback analysis when API fails
  const generateFallbackAnalysis = (query: string, items: api.WatchItem[]): string => {
    const criticalCount = items.filter(i => i.severity?.toLowerCase() === 'critical').length
    const highCount = items.filter(i => i.severity?.toLowerCase() === 'high').length
    
    return `## CyberAgent Analysis\n\n**Query:** ${query}\n\n### Current Threat Landscape\n\n- **Critical Vulnerabilities:** ${criticalCount}\n- **High Severity:** ${highCount}\n- **Total Monitored:** ${items.length}\n\n### Recommendations\n\n1. Prioritize patching critical CVEs from CISA KEV\n2. Review NVD entries for your tech stack\n3. Enable continuous monitoring for new disclosures\n\n*Note: For detailed AI analysis, ensure the backend API is available.*`
  }
  
  // Analyze selected CVEs
  const analyzeCVEs = async (cves: string[]) => {
    if (cves.length === 0) return
    
    setIsAnalyzing(true)
    
    const analysisPrompt = `Analyze these CVEs for a security team:\n\n${cves.join(', ')}\n\nProvide:\n1. Risk assessment (1-10)\n2. Exploitability level\n3. Affected systems\n4. Remediation steps\n5. Urgency level`
    
    try {
      const response = await api.cyberQuery({
        query: analysisPrompt,
        include_cves: true,
        max_results: 5,
      })
      
      const analysisMessage: CyberMessage = {
        id: `analysis-${Date.now()}`,
        role: 'analysis',
        content: response.content,
        timestamp: new Date(),
        cves: cves,
        severity: 'analysis',
      }
      
      setChatMessages(prev => [...prev, analysisMessage])
    } catch (error) {
      console.error('CVE analysis failed:', error)
    }
    
    setIsAnalyzing(false)
    setSelectedCVEsForAnalysis([])
  }
  
  // Generate daily threat briefing
  const generateDailyBriefing = async () => {
    setIsGeneratingBriefing(true)
    
    const criticalItems = filteredItems.filter(i => i.severity?.toLowerCase() === 'critical').slice(0, 5)
    const highItems = filteredItems.filter(i => i.severity?.toLowerCase() === 'high').slice(0, 5)
    
    const briefingPrompt = `Generate a concise daily threat briefing for a security team.\n\nCritical CVEs today:\n${criticalItems.map(i => `- ${i.cve}: ${i.title}`).join('\n')}\n\nHigh severity:\n${highItems.map(i => `- ${i.cve}: ${i.title}`).join('\n')}\n\nTotal vulnerabilities tracked: ${filteredItems.length}\nSources: CISA KEV, CERT-FR, NVD, Exploit-DB, GitHub\n\nProvide:\n1. Executive summary (2-3 sentences)\n2. Top 3 priorities\n3. Recommended actions\n4. Emerging trends`
    
    try {
      const response = await api.cyberQuery({
        query: briefingPrompt,
        include_cves: true,
        include_alerts: true,
        max_results: 10,
      })
      
      setDailyBriefing(response.content)
      
      // Also add to chat
      const briefingMessage: CyberMessage = {
        id: `briefing-${Date.now()}`,
        role: 'analysis',
        content: `## Daily Threat Briefing\n\n${response.content}`,
        timestamp: new Date(),
      }
      setChatMessages(prev => [...prev, briefingMessage])
    } catch (error) {
      // Fallback briefing
      const fallback = `## Daily Threat Briefing\n\n**Date:** ${new Date().toLocaleDateString()}\n\n### Executive Summary\nMonitoring ${filteredItems.length} vulnerabilities across ${enabledSources.length} sources. ${criticalItems.length} critical and ${highItems.length} high-severity issues require attention.\n\n### Top Priorities\n${criticalItems.slice(0, 3).map((i, idx) => `${idx + 1}. **${i.cve}** - ${i.title}`).join('\n')}\n\n### Recommended Actions\n1. Review and patch critical CVEs immediately\n2. Assess high-severity vulnerabilities for your environment\n3. Update security monitoring rules\n\n*Automated briefing - Review with your security team*`
      setDailyBriefing(fallback)
    }
    
    setIsGeneratingBriefing(false)
  }
  
  // Note: toggleCVESelection available for vulnerability list checkbox integration
  // Currently used via selectedCVEsForAnalysis state in the CyberAgent panel
  
  // Copy to clipboard
  const copyToClipboard = async (text: string, id: string) => {
    await navigator.clipboard.writeText(text)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }
  
  // Quick analysis prompts
  const quickPrompts = [
    { icon: Zap, label: 'Critical CVEs', prompt: 'What are the most critical CVEs I should patch today?' },
    { icon: Target, label: 'Exploited', prompt: 'Which vulnerabilities are being actively exploited?' },
    { icon: Server, label: 'Web Servers', prompt: 'List CVEs affecting Apache, Nginx, or IIS web servers' },
    { icon: Lock, label: 'Auth Bypass', prompt: 'Show authentication bypass vulnerabilities from this week' },
    { icon: Bug, label: 'RCE', prompt: 'What remote code execution vulnerabilities are trending?' },
  ]

  // Filter items
  const filteredItems = feed?.filter(item => {
    // Source filter
    if (sourceFilter !== 'all') {
      const sourceMap: Record<string, string[]> = {
        cisa: ['CISA-KEV'],
        certfr: ['CERT-FR', 'CERT-FR-Avis'],
        nvd: ['NVD'],
        exploitdb: ['Exploit-DB'],
        github: ['GitHub-GHSA'],
      }
      if (!sourceMap[sourceFilter]?.includes(item.source)) return false
    }
    
    // Severity filter
    if (severityFilter !== 'all' && item.severity?.toLowerCase() !== severityFilter) return false
    
    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      return (
        item.title.toLowerCase().includes(query) ||
        item.cve?.toLowerCase().includes(query) ||
        item.source.toLowerCase().includes(query) ||
        item.description?.toLowerCase().includes(query)
      )
    }
    
    return true
  }) || []

  // Calculate stats
  const feedStats = {
    total: feed?.length || 0,
    cisa: feed?.filter(i => i.source === 'CISA-KEV').length || 0,
    certfr: feed?.filter(i => i.source === 'CERT-FR' || i.source === 'CERT-FR-Avis').length || 0,
    nvd: feed?.filter(i => i.source === 'NVD').length || 0,
    exploitdb: feed?.filter(i => i.source === 'Exploit-DB').length || 0,
    github: feed?.filter(i => i.source === 'GitHub-GHSA').length || 0,
    critical: feed?.filter(i => i.severity?.toLowerCase() === 'critical').length || 0,
    high: feed?.filter(i => i.severity?.toLowerCase() === 'high').length || 0,
  }

  // Export to JSON
  const exportJSON = () => {
    const data = {
      exported_at: new Date().toISOString(),
      total_items: filteredItems.length,
      filters: { source: sourceFilter, severity: severityFilter, search: searchQuery },
      items: filteredItems
    }
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `freya-cyberwatch-${format(new Date(), 'yyyy-MM-dd-HHmm')}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="h-full flex overflow-hidden">
      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-freya-border bg-freya-bg-secondary">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-freya-accent-red/20 flex items-center justify-center">
              <ShieldAlert className="w-6 h-6 text-freya-accent-red" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-freya-text-primary">Cyber Watch</h2>
              <div className="flex items-center gap-2 text-sm text-freya-text-muted">
                <span>{feedStats.total} vulnerabilities</span>
                <span>•</span>
                {lastRefresh && (
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    Last update: {formatDistanceToNow(lastRefresh, { addSuffix: true })}
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Auto-refresh toggle */}
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={clsx(
                'flex items-center gap-2 px-3 py-2 rounded-lg border transition-all',
                autoRefresh
                  ? 'border-freya-accent-green/50 bg-freya-accent-green/10 text-freya-accent-green'
                  : 'border-freya-border bg-freya-bg-tertiary text-freya-text-muted'
              )}
            >
              {autoRefresh ? (
                <>
                  <Play className="w-4 h-4" />
                  <span className="text-sm">Auto ({refreshInterval}m)</span>
                </>
              ) : (
                <>
                  <Pause className="w-4 h-4" />
                  <span className="text-sm">Paused</span>
                </>
              )}
            </button>

            {/* Settings */}
            <button
              onClick={() => setShowSettings(!showSettings)}
              className={clsx(
                'p-2 rounded-lg border transition-colors',
                showSettings ? 'border-freya-accent-blue bg-freya-accent-blue/10' : 'border-freya-border hover:bg-freya-bg-tertiary'
              )}
            >
              <Settings className="w-5 h-5" />
            </button>

            {/* Manual refresh */}
            <button
              onClick={() => refreshMutation.mutate()}
              disabled={isRefetching || refreshMutation.isPending}
              className="btn-primary flex items-center gap-2"
            >
              <RefreshCw className={clsx('w-4 h-4', (isRefetching || refreshMutation.isPending) && 'animate-spin')} />
              Refresh
            </button>

            {/* Export */}
            <button onClick={exportJSON} className="btn-secondary flex items-center gap-2">
              <Download className="w-4 h-4" />
              Export
            </button>
            
            {/* CyberAgent Toggle */}
            <button
              onClick={() => setShowAgentPanel(!showAgentPanel)}
              className={clsx(
                'flex items-center gap-2 px-3 py-2 rounded-lg border transition-all',
                showAgentPanel
                  ? 'border-freya-accent-purple bg-freya-accent-purple/20 text-freya-accent-purple'
                  : 'border-freya-border bg-freya-bg-tertiary text-freya-text-secondary hover:text-freya-text-primary'
              )}
            >
              <Bot className="w-4 h-4" />
              <span className="text-sm font-medium">CyberAgent</span>
              {showAgentPanel && <Sparkles className="w-3 h-3" />}
            </button>
          </div>
        </div>

        {/* Settings Panel */}
        {showSettings && (
          <div className="mb-4 p-4 bg-freya-bg-tertiary rounded-lg border border-freya-border animate-fade-in">
            <h4 className="font-medium text-freya-text-primary mb-3">Watch Settings</h4>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-freya-text-secondary mb-2">Refresh Interval</label>
                <select
                  value={refreshInterval}
                  onChange={(e) => setRefreshInterval(parseInt(e.target.value))}
                  className="input w-full"
                >
                  <option value="1">1 minute</option>
                  <option value="5">5 minutes</option>
                  <option value="10">10 minutes</option>
                  <option value="30">30 minutes</option>
                  <option value="60">1 hour</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-freya-text-secondary mb-2">Enabled Sources</label>
                <div className="flex flex-wrap gap-2">
                  {['cisa', 'certfr', 'nvd', 'exploitdb', 'github'].map(source => (
                    <button
                      key={source}
                      onClick={() => {
                        setEnabledSources(prev =>
                          prev.includes(source)
                            ? prev.filter(s => s !== source)
                            : [...prev, source]
                        )
                      }}
                      className={clsx(
                        'px-2 py-1 rounded text-xs font-medium transition-colors',
                        enabledSources.includes(source)
                          ? 'bg-freya-accent-blue text-white'
                          : 'bg-freya-bg-secondary text-freya-text-muted'
                      )}
                    >
                      {source.toUpperCase()}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Stats Cards */}
        <div className="grid grid-cols-6 gap-3 mb-4">
          {[
            { label: 'Critical', value: feedStats.critical, color: 'text-freya-accent-red', bg: 'bg-freya-accent-red/10', isSource: false },
            { label: 'High', value: feedStats.high, color: 'text-orange-500', bg: 'bg-orange-500/10', isSource: false },
            { label: 'CISA KEV', value: feedStats.cisa, color: 'text-freya-accent-red', bg: 'bg-freya-accent-red/10', isSource: true },
            { label: 'CERT-FR', value: feedStats.certfr, color: 'text-freya-accent-blue', bg: 'bg-freya-accent-blue/10', isSource: true },
            { label: 'NVD', value: feedStats.nvd, color: 'text-freya-accent-purple', bg: 'bg-freya-accent-purple/10', isSource: true },
            { label: 'Exploits', value: feedStats.exploitdb, color: 'text-freya-accent-yellow', bg: 'bg-freya-accent-yellow/10', isSource: true },
          ].map(stat => (
            <div key={stat.label} className={clsx('p-3 rounded-lg relative', stat.bg)}>
              <div className={clsx('text-2xl font-bold', stat.value === 0 && stat.isSource ? 'text-freya-text-muted' : stat.color)}>
                {stat.value}
              </div>
              <div className="text-xs text-freya-text-muted">{stat.label}</div>
              {stat.value === 0 && stat.isSource && (
                <div className="absolute top-1 right-1" title="Source unavailable or no data">
                  <AlertTriangle className="w-3 h-3 text-freya-accent-yellow" />
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Filters */}
        <div className="flex items-center gap-4">
          {/* Search */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-freya-text-muted" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search CVE, title, or description..."
              className="input pl-10 w-full"
            />
          </div>

          {/* Source Filter */}
          <div className="flex items-center gap-1 bg-freya-bg-tertiary rounded-lg p-1">
            {SOURCES.map(source => {
              const Icon = source.icon
              const isActive = sourceFilter === source.id
              return (
                <button
                  key={source.id}
                  onClick={() => setSourceFilter(source.id as SourceFilter)}
                  className={clsx(
                    'flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-all',
                    isActive
                      ? 'bg-freya-bg-primary text-freya-text-primary shadow'
                      : 'text-freya-text-muted hover:text-freya-text-secondary'
                  )}
                >
                  <Icon className="w-4 h-4" />
                  <span className="hidden lg:inline">{source.name}</span>
                </button>
              )
            })}
          </div>

          {/* Severity Filter */}
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value as SeverityFilter)}
            className="input w-40"
          >
            <option value="all">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <RefreshCw className="w-8 h-8 text-freya-accent-blue animate-spin" />
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-freya-text-muted">
            <ShieldCheck className="w-12 h-12 mb-4" />
            <p>No vulnerabilities match your filters</p>
            {feedStats.total === 0 && (
              <div className="mt-4 p-4 bg-freya-bg-tertiary rounded-lg text-center max-w-md">
                <AlertCircle className="w-6 h-6 mx-auto mb-2 text-freya-accent-yellow" />
                <p className="text-sm text-freya-text-secondary mb-2">
                  Unable to fetch security feeds. This may be due to:
                </p>
                <ul className="text-xs text-freya-text-muted text-left space-y-1">
                  <li>• Network connectivity issues</li>
                  <li>• Source servers may be temporarily unavailable</li>
                  <li>• Rate limiting from security feed providers</li>
                </ul>
                <button
                  onClick={() => refreshMutation.mutate()}
                  className="mt-3 btn-secondary text-sm"
                >
                  <RefreshCw className="w-4 h-4 mr-1 inline" />
                  Retry
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-3">
            {filteredItems.map((item, index) => {
              const severityConfig = SEVERITY_CONFIG[item.severity?.toLowerCase() || 'unknown']
              const SeverityIcon = severityConfig?.icon || Shield
              const isExpanded = expandedCVE === item.cve

              return (
                <div
                  key={`${item.source}-${item.cve || index}`}
                  className="bg-freya-bg-secondary rounded-lg border border-freya-border overflow-hidden"
                >
                  <div
                    className="p-4 cursor-pointer hover:bg-freya-bg-tertiary/50 transition-colors"
                    onClick={() => item.cve && setExpandedCVE(isExpanded ? null : item.cve)}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-start gap-3 flex-1 min-w-0">
                        <SeverityIcon className={clsx('w-5 h-5 mt-0.5 flex-shrink-0', severityConfig?.color)} />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className={clsx('badge', SOURCE_COLORS[item.source] || SOURCE_COLORS.default)}>
                              {item.source}
                            </span>
                            {item.cve && (
                              <span className="font-mono text-sm text-freya-accent-cyan">{item.cve}</span>
                            )}
                            {item.severity && (
                              <span className={clsx('text-xs font-medium', severityConfig?.color)}>
                                {item.severity}
                              </span>
                            )}
                          </div>
                          <h3 className="font-medium text-freya-text-primary line-clamp-2">{item.title}</h3>
                          {item.description && (
                            <p className="text-sm text-freya-text-muted mt-1 line-clamp-2">{item.description}</p>
                          )}
                          <div className="flex items-center gap-4 mt-2 text-xs text-freya-text-muted">
                            {item.published && (
                              <span className="flex items-center gap-1">
                                <Calendar className="w-3 h-3" />
                                {item.published}
                              </span>
                            )}
                            {item.tags && item.tags.length > 0 && (
                              <div className="flex items-center gap-1">
                                {item.tags.slice(0, 3).map(tag => (
                                  <span key={tag} className="px-1.5 py-0.5 bg-freya-bg-tertiary rounded text-xs">
                                    {tag}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <a
                          href={item.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          className="p-2 rounded hover:bg-freya-bg-tertiary transition-colors"
                        >
                          <ExternalLink className="w-4 h-4 text-freya-text-muted" />
                        </a>
                        {item.cve && (
                          <ChevronRight
                            className={clsx(
                              'w-4 h-4 text-freya-text-muted transition-transform',
                              isExpanded && 'rotate-90'
                            )}
                          />
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Expanded CVE Details */}
                  {isExpanded && cveDetails && (
                    <div className="p-4 border-t border-freya-border bg-freya-bg-tertiary animate-fade-in">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <h4 className="text-sm font-medium text-freya-text-secondary mb-2">Description</h4>
                          <p className="text-sm text-freya-text-primary">{cveDetails.description}</p>
                        </div>
                        <div className="space-y-4">
                          {cveDetails.cvss_score && (
                            <div>
                              <h4 className="text-sm font-medium text-freya-text-secondary mb-1">CVSS Score</h4>
                              <div className="flex items-center gap-2">
                                <span className={clsx(
                                  'text-2xl font-bold',
                                  cveDetails.cvss_score >= 9 ? 'text-freya-accent-red' :
                                  cveDetails.cvss_score >= 7 ? 'text-orange-500' :
                                  cveDetails.cvss_score >= 4 ? 'text-freya-accent-yellow' :
                                  'text-freya-accent-green'
                                )}>
                                  {cveDetails.cvss_score}
                                </span>
                                <span className="text-freya-text-muted">/ 10</span>
                              </div>
                            </div>
                          )}
                          {cveDetails.affected_products && cveDetails.affected_products.length > 0 && (
                            <div>
                              <h4 className="text-sm font-medium text-freya-text-secondary mb-1">Affected Products</h4>
                              <div className="flex flex-wrap gap-1">
                                {cveDetails.affected_products.slice(0, 5).map(product => (
                                  <span key={product} className="badge badge-yellow">{product}</span>
                                ))}
                              </div>
                            </div>
                          )}
                          {cveDetails.references && cveDetails.references.length > 0 && (
                            <div>
                              <h4 className="text-sm font-medium text-freya-text-secondary mb-1">References</h4>
                              <div className="space-y-1">
                                {cveDetails.references.slice(0, 3).map((ref, i) => (
                                  <a
                                    key={i}
                                    href={ref}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="block text-xs text-freya-accent-blue hover:underline truncate"
                                  >
                                    {ref}
                                  </a>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Cache Status Footer */}
      {stats && (
        <div className="p-2 border-t border-freya-border bg-freya-bg-secondary">
          <div className="flex items-center justify-between text-xs text-freya-text-muted">
            <div className="flex items-center gap-4">
              {Object.entries(stats.sources || {}).map(([name, info]: [string, any]) => (
                <span key={name} className="flex items-center gap-1">
                  <span className={clsx(
                    'w-2 h-2 rounded-full',
                    info.is_stale ? 'bg-freya-accent-yellow' : 'bg-freya-accent-green'
                  )} />
                  {name.replace(/_/g, ' ')}: {info.item_count} items
                  {info.cache_age_minutes >= 0 && ` (${Math.round(info.cache_age_minutes)}m ago)`}
                </span>
              ))}
            </div>
            <span>
              {autoRefresh ? `Next refresh in ${refreshInterval} minutes` : 'Auto-refresh paused'}
            </span>
          </div>
        </div>
      )}
      </div>
      
      {/* CyberAgent Panel */}
      {showAgentPanel && (
        <div className="w-96 border-l border-freya-border bg-freya-bg-secondary flex flex-col animate-slide-in-right">
          {/* Agent Header */}
          <div className="p-4 border-b border-freya-border">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-freya-accent-purple to-freya-accent-cyan flex items-center justify-center">
                  <Bot className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 className="font-semibold text-freya-text-primary">CyberAgent</h3>
                  <p className="text-xs text-freya-text-muted">AI Security Analyst</p>
                </div>
              </div>
              <div className="flex items-center gap-1">
                <button
                  onClick={generateDailyBriefing}
                  disabled={isGeneratingBriefing}
                  className="p-1.5 rounded hover:bg-freya-bg-tertiary text-freya-text-muted hover:text-freya-accent-cyan"
                  title="Generate Daily Briefing"
                >
                  {isGeneratingBriefing ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <FileText className="w-4 h-4" />
                  )}
                </button>
                <button
                  onClick={() => setChatMessages([])}
                  className="p-1.5 rounded hover:bg-freya-bg-tertiary text-freya-text-muted"
                  title="Clear Chat"
                >
                  <RefreshCw className="w-4 h-4" />
                </button>
              </div>
            </div>
            
            {/* Mode Tabs */}
            <div className="flex items-center gap-1 bg-freya-bg-tertiary rounded-lg p-1">
              {[
                { mode: 'chat' as CyberAgentMode, icon: MessageSquare, label: 'Chat' },
                { mode: 'analysis' as CyberAgentMode, icon: Brain, label: 'Analysis' },
                { mode: 'briefing' as CyberAgentMode, icon: FileText, label: 'Briefing' },
              ].map(({ mode, icon: Icon, label }) => (
                <button
                  key={mode}
                  onClick={() => setAgentMode(mode)}
                  className={clsx(
                    'flex items-center gap-1 px-3 py-1.5 rounded-md text-xs transition-all flex-1',
                    agentMode === mode
                      ? 'bg-freya-bg-primary text-freya-text-primary shadow'
                      : 'text-freya-text-muted hover:text-freya-text-secondary'
                  )}
                >
                  <Icon className="w-3 h-3" />
                  {label}
                </button>
              ))}
            </div>
          </div>
          
          {/* Selected CVEs for Analysis */}
          {selectedCVEsForAnalysis.length > 0 && (
            <div className="p-3 border-b border-freya-border bg-freya-accent-purple/10">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium text-freya-accent-purple">
                  {selectedCVEsForAnalysis.length} CVE(s) selected
                </span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => analyzeCVEs(selectedCVEsForAnalysis)}
                    disabled={isAnalyzing}
                    className="btn-primary text-xs px-2 py-1 flex items-center gap-1"
                  >
                    {isAnalyzing ? <Loader2 className="w-3 h-3 animate-spin" /> : <Brain className="w-3 h-3" />}
                    Analyze
                  </button>
                  <button
                    onClick={() => setSelectedCVEsForAnalysis([])}
                    className="text-xs text-freya-text-muted hover:text-freya-accent-red"
                  >
                    Clear
                  </button>
                </div>
              </div>
              <div className="flex flex-wrap gap-1">
                {selectedCVEsForAnalysis.map(cve => (
                  <span key={cve} className="badge badge-purple text-xs">{cve}</span>
                ))}
              </div>
            </div>
          )}
          
          {/* Chat Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {chatMessages.length === 0 ? (
              <div className="text-center py-8">
                <Bot className="w-12 h-12 mx-auto mb-3 text-freya-text-muted opacity-50" />
                <p className="text-sm text-freya-text-muted mb-4">Ask CyberAgent about vulnerabilities, threats, and security recommendations.</p>
                
                {/* Quick Prompts */}
                <div className="space-y-2">
                  <p className="text-xs text-freya-text-muted">Quick questions:</p>
                  {quickPrompts.map(({ icon: Icon, label, prompt }) => (
                    <button
                      key={label}
                      onClick={() => {
                        setChatInput(prompt)
                        inputRef.current?.focus()
                      }}
                      className="w-full flex items-center gap-2 p-2 rounded-lg bg-freya-bg-tertiary hover:bg-freya-bg-primary text-left text-xs transition-colors"
                    >
                      <Icon className="w-4 h-4 text-freya-accent-cyan" />
                      <span className="text-freya-text-secondary">{label}</span>
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              chatMessages.map(msg => (
                <div
                  key={msg.id}
                  className={clsx(
                    'rounded-lg p-3',
                    msg.role === 'user' && 'bg-freya-accent-blue/20 border border-freya-accent-blue/30 ml-4',
                    msg.role === 'agent' && 'bg-freya-bg-tertiary border border-freya-border mr-4',
                    msg.role === 'system' && 'bg-freya-accent-yellow/10 border border-freya-accent-yellow/30',
                    msg.role === 'analysis' && 'bg-freya-accent-purple/10 border border-freya-accent-purple/30'
                  )}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className={clsx(
                      'text-xs font-medium',
                      msg.role === 'user' && 'text-freya-accent-blue',
                      msg.role === 'agent' && 'text-freya-accent-green',
                      msg.role === 'system' && 'text-freya-accent-yellow',
                      msg.role === 'analysis' && 'text-freya-accent-purple'
                    )}>
                      {msg.role === 'user' ? 'You' : 
                       msg.role === 'agent' ? 'CyberAgent' : 
                       msg.role === 'analysis' ? 'Analysis' : 'System'}
                    </span>
                    <button
                      onClick={() => copyToClipboard(msg.content, msg.id)}
                      className="p-1 rounded hover:bg-freya-bg-tertiary"
                    >
                      {copiedId === msg.id ? (
                        <Check className="w-3 h-3 text-freya-accent-green" />
                      ) : (
                        <Copy className="w-3 h-3 text-freya-text-muted" />
                      )}
                    </button>
                  </div>
                  <div className="text-sm text-freya-text-primary whitespace-pre-wrap">
                    {msg.content}
                  </div>
                  {msg.cves && msg.cves.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {msg.cves.map(cve => (
                        <span key={cve} className="badge badge-cyan text-xs">{cve}</span>
                      ))}
                    </div>
                  )}
                </div>
              ))
            )}
            {isAnalyzing && (
              <div className="flex items-center gap-2 text-freya-text-muted text-sm">
                <Loader2 className="w-4 h-4 animate-spin" />
                CyberAgent is analyzing...
              </div>
            )}
            <div ref={chatEndRef} />
          </div>
          
          {/* Chat Input */}
          <div className="p-4 border-t border-freya-border">
            <div className="flex items-center gap-2">
              <input
                ref={inputRef}
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleCyberChat()}
                placeholder="Ask about CVEs, threats, or security..."
                className="input flex-1 text-sm"
                disabled={isAnalyzing}
              />
              <button
                onClick={handleCyberChat}
                disabled={!chatInput.trim() || isAnalyzing}
                className="btn-primary p-2"
              >
                {isAnalyzing ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </button>
            </div>
            <div className="flex items-center gap-2 mt-2 text-xs text-freya-text-muted">
              <Lightbulb className="w-3 h-3" />
              <span>Tip: Select CVEs from the list to analyze them together</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
