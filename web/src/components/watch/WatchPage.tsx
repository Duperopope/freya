/**
 * WatchPage - Cyber Security Watch
 * 
 * Real-time security vulnerability monitoring dashboard.
 * Aggregates data from CISA KEV, CERT-FR, and other security feeds.
 */

import { useState } from 'react'
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
  Bug,
  ChevronRight,
  Info,
  AlertCircle
} from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { clsx } from 'clsx'
import { format, formatDistanceToNow } from 'date-fns'
import * as api from '../../lib/api'

type SourceFilter = 'all' | 'cisa' | 'certfr'
type SeverityFilter = 'all' | 'critical' | 'high' | 'medium' | 'low'

// Source badge colors
const SOURCE_COLORS: Record<string, string> = {
  'CISA-KEV': 'badge-red',
  'CERT-FR': 'badge-blue',
  'NVD': 'badge-purple',
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
  const [sourceFilter, setSourceFilter] = useState<SourceFilter>('all')
  const [severityFilter, setSeverityFilter] = useState<SeverityFilter>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedItem, setSelectedItem] = useState<api.WatchItem | null>(null)
  // Fetch watch feed
  const { data: feed, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['watchFeed'],
    queryFn: () => api.getWatchFeed(50),
    refetchInterval: 5 * 60 * 1000, // 5 minutes
  })

  // CVE lookup function (reserved for future detailed view)
  const lookupCVE = async (cveId: string) => {
    try {
      await api.lookupCVE(cveId)
      // Future: show CVE details in a modal
    } catch (e) {
      console.error('CVE lookup failed:', e)
    }
  }

  // Filter items
  const filteredItems = feed?.filter(item => {
    // Source filter
    if (sourceFilter === 'cisa' && item.source !== 'CISA-KEV') return false
    if (sourceFilter === 'certfr' && item.source !== 'CERT-FR') return false
    
    // Severity filter
    if (severityFilter !== 'all' && item.severity?.toLowerCase() !== severityFilter) return false
    
    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      return (
        item.title.toLowerCase().includes(query) ||
        item.cve?.toLowerCase().includes(query) ||
        item.source.toLowerCase().includes(query)
      )
    }
    
    return true
  }) || []

  // Stats
  const stats = {
    total: feed?.length || 0,
    cisa: feed?.filter(i => i.source === 'CISA-KEV').length || 0,
    certfr: feed?.filter(i => i.source === 'CERT-FR').length || 0,
    critical: feed?.filter(i => i.severity?.toLowerCase() === 'critical').length || 0,
    high: feed?.filter(i => i.severity?.toLowerCase() === 'high').length || 0,
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
                <h2 className="text-lg font-semibold text-freya-text-primary">Security Watch</h2>
                <p className="text-sm text-freya-text-muted">
                  Real-time vulnerability monitoring
                </p>
              </div>
            </div>

            <button
              onClick={() => refetch()}
              disabled={isRefetching}
              className="btn-secondary flex items-center gap-2"
            >
              <RefreshCw className={clsx('w-4 h-4', isRefetching && 'animate-spin')} />
              Refresh
            </button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-5 gap-3">
            <div className="bg-freya-bg-primary rounded-lg p-3 border border-freya-border">
              <div className="text-2xl font-bold text-freya-text-primary">{stats.total}</div>
              <div className="text-xs text-freya-text-muted">Total Items</div>
            </div>
            <div className="bg-freya-bg-primary rounded-lg p-3 border border-freya-border">
              <div className="text-2xl font-bold text-freya-accent-red">{stats.cisa}</div>
              <div className="text-xs text-freya-text-muted">CISA KEV</div>
            </div>
            <div className="bg-freya-bg-primary rounded-lg p-3 border border-freya-border">
              <div className="text-2xl font-bold text-freya-accent-blue">{stats.certfr}</div>
              <div className="text-xs text-freya-text-muted">CERT-FR</div>
            </div>
            <div className="bg-freya-bg-primary rounded-lg p-3 border border-freya-border">
              <div className="text-2xl font-bold text-freya-accent-red">{stats.critical}</div>
              <div className="text-xs text-freya-text-muted">Critical</div>
            </div>
            <div className="bg-freya-bg-primary rounded-lg p-3 border border-freya-border">
              <div className="text-2xl font-bold text-orange-500">{stats.high}</div>
              <div className="text-xs text-freya-text-muted">High</div>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="p-4 border-b border-freya-border flex items-center gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-freya-text-muted" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search CVEs, titles, sources..."
              className="input pl-9"
            />
          </div>

          {/* Source Filter */}
          <div className="flex items-center gap-2 bg-freya-bg-primary rounded-lg p-1">
            {[
              { id: 'all', label: 'All' },
              { id: 'cisa', label: 'CISA' },
              { id: 'certfr', label: 'CERT-FR' },
            ].map((opt) => (
              <button
                key={opt.id}
                onClick={() => setSourceFilter(opt.id as SourceFilter)}
                className={clsx(
                  'px-3 py-1.5 rounded-md text-sm transition-colors',
                  sourceFilter === opt.id
                    ? 'bg-freya-bg-tertiary text-freya-text-primary'
                    : 'text-freya-text-secondary hover:text-freya-text-primary'
                )}
              >
                {opt.label}
              </button>
            ))}
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

        {/* Vulnerability List */}
        <div className="flex-1 overflow-y-auto">
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <RefreshCw className="w-8 h-8 text-freya-text-muted animate-spin" />
            </div>
          ) : filteredItems.length > 0 ? (
            <div className="divide-y divide-freya-border">
              {filteredItems.map((item, idx) => {
                const severity = item.severity?.toLowerCase() || 'unknown'
                const severityConfig = SEVERITY_CONFIG[severity] || SEVERITY_CONFIG.unknown
                const SeverityIcon = severityConfig.icon
                const isSelected = selectedItem === item

                return (
                  <div
                    key={idx}
                    onClick={() => setSelectedItem(isSelected ? null : item)}
                    className={clsx(
                      'p-4 cursor-pointer transition-colors',
                      isSelected
                        ? 'bg-freya-bg-tertiary'
                        : 'hover:bg-freya-bg-secondary'
                    )}
                  >
                    <div className="flex items-start gap-4">
                      {/* Severity Icon */}
                      <div className={clsx(
                        'w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0',
                        severity === 'critical' && 'bg-freya-accent-red/20',
                        severity === 'high' && 'bg-orange-500/20',
                        severity === 'medium' && 'bg-freya-accent-yellow/20',
                        severity === 'low' && 'bg-freya-accent-green/20',
                        severity === 'unknown' && 'bg-freya-bg-tertiary'
                      )}>
                        <SeverityIcon className={clsx('w-5 h-5', severityConfig.color)} />
                      </div>

                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          {item.cve && (
                            <span className="font-mono text-freya-accent-cyan text-sm">
                              {item.cve}
                            </span>
                          )}
                          <span className={clsx(
                            'badge',
                            SOURCE_COLORS[item.source] || SOURCE_COLORS.default
                          )}>
                            {item.source}
                          </span>
                        </div>

                        <h4 className="font-medium text-freya-text-primary mb-1 line-clamp-2">
                          {item.title}
                        </h4>

                        <div className="flex items-center gap-4 text-xs text-freya-text-muted">
                          <span className="flex items-center gap-1">
                            <Calendar className="w-3 h-3" />
                            {format(new Date(item.published), 'MMM d, yyyy')}
                          </span>
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {formatDistanceToNow(new Date(item.published), { addSuffix: true })}
                          </span>
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex items-center gap-2">
                        <a
                          href={item.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          className="p-2 rounded hover:bg-freya-bg-elevated transition-colors"
                          title="Open in new tab"
                        >
                          <ExternalLink className="w-4 h-4 text-freya-text-muted" />
                        </a>
                        <ChevronRight className={clsx(
                          'w-5 h-5 text-freya-text-muted transition-transform',
                          isSelected && 'rotate-90'
                        )} />
                      </div>
                    </div>

                    {/* Expanded Details */}
                    {isSelected && (
                      <div className="mt-4 pt-4 border-t border-freya-border animate-slide-up">
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <div className="text-freya-text-muted mb-1">Source</div>
                            <div className="text-freya-text-primary">{item.source}</div>
                          </div>
                          <div>
                            <div className="text-freya-text-muted mb-1">Published</div>
                            <div className="text-freya-text-primary">
                              {format(new Date(item.published), 'PPPp')}
                            </div>
                          </div>
                          {item.cve && (
                            <div className="col-span-2">
                              <div className="text-freya-text-muted mb-1">CVE ID</div>
                              <a
                                href={`https://nvd.nist.gov/vuln/detail/${item.cve}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-freya-accent-blue hover:underline flex items-center gap-1"
                              >
                                {item.cve}
                                <ExternalLink className="w-3 h-3" />
                              </a>
                            </div>
                          )}
                        </div>

                        <div className="mt-4 flex items-center gap-2">
                          <a
                            href={item.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn-primary text-sm flex items-center gap-2"
                          >
                            <Globe className="w-4 h-4" />
                            View Full Advisory
                          </a>
                          {item.cve && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                lookupCVE(item.cve!)
                              }}
                              className="btn-secondary text-sm flex items-center gap-2"
                            >
                              <Bug className="w-4 h-4" />
                              CVE Details
                            </button>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-64 text-freya-text-muted">
              <ShieldCheck className="w-16 h-16 mb-4 opacity-30" />
              <p className="text-lg font-medium text-freya-text-secondary">No vulnerabilities found</p>
              <p className="text-sm mt-1">
                {searchQuery ? 'Try a different search query' : 'All clear for now'}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Right Sidebar - Quick Links & Info */}
      <div className="w-72 border-l border-freya-border bg-freya-bg-secondary p-4 overflow-y-auto hidden lg:block">
        <h3 className="font-semibold text-freya-text-primary mb-4">Quick Links</h3>

        <div className="space-y-3">
          <a
            href="https://www.cisa.gov/known-exploited-vulnerabilities-catalog"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-3 p-3 rounded-lg bg-freya-bg-primary border border-freya-border hover:border-freya-border-light transition-colors"
          >
            <div className="w-8 h-8 rounded bg-freya-accent-red/20 flex items-center justify-center">
              <ShieldAlert className="w-4 h-4 text-freya-accent-red" />
            </div>
            <div className="flex-1">
              <div className="font-medium text-freya-text-primary text-sm">CISA KEV</div>
              <div className="text-xs text-freya-text-muted">Known Exploited Vulns</div>
            </div>
            <ExternalLink className="w-4 h-4 text-freya-text-muted" />
          </a>

          <a
            href="https://www.cert.ssi.gouv.fr/alerte/"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-3 p-3 rounded-lg bg-freya-bg-primary border border-freya-border hover:border-freya-border-light transition-colors"
          >
            <div className="w-8 h-8 rounded bg-freya-accent-blue/20 flex items-center justify-center">
              <Globe className="w-4 h-4 text-freya-accent-blue" />
            </div>
            <div className="flex-1">
              <div className="font-medium text-freya-text-primary text-sm">CERT-FR</div>
              <div className="text-xs text-freya-text-muted">French CERT Alerts</div>
            </div>
            <ExternalLink className="w-4 h-4 text-freya-text-muted" />
          </a>

          <a
            href="https://nvd.nist.gov/"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-3 p-3 rounded-lg bg-freya-bg-primary border border-freya-border hover:border-freya-border-light transition-colors"
          >
            <div className="w-8 h-8 rounded bg-freya-accent-purple/20 flex items-center justify-center">
              <Bug className="w-4 h-4 text-freya-accent-purple" />
            </div>
            <div className="flex-1">
              <div className="font-medium text-freya-text-primary text-sm">NVD</div>
              <div className="text-xs text-freya-text-muted">National Vuln Database</div>
            </div>
            <ExternalLink className="w-4 h-4 text-freya-text-muted" />
          </a>

          <a
            href="https://www.exploit-db.com/"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-3 p-3 rounded-lg bg-freya-bg-primary border border-freya-border hover:border-freya-border-light transition-colors"
          >
            <div className="w-8 h-8 rounded bg-freya-accent-yellow/20 flex items-center justify-center">
              <AlertTriangle className="w-4 h-4 text-freya-accent-yellow" />
            </div>
            <div className="flex-1">
              <div className="font-medium text-freya-text-primary text-sm">Exploit-DB</div>
              <div className="text-xs text-freya-text-muted">Exploits Database</div>
            </div>
            <ExternalLink className="w-4 h-4 text-freya-text-muted" />
          </a>
        </div>

        {/* Info Box */}
        <div className="mt-6 p-4 rounded-lg bg-freya-bg-tertiary border border-freya-border">
          <div className="flex items-start gap-2">
            <Info className="w-4 h-4 text-freya-accent-blue mt-0.5" />
            <div className="text-xs text-freya-text-secondary">
              <p className="font-medium text-freya-text-primary mb-1">Auto-Refresh</p>
              <p>
                This feed automatically refreshes every 5 minutes. 
                Click the refresh button for immediate updates.
              </p>
            </div>
          </div>
        </div>

        {/* Severity Legend */}
        <div className="mt-6">
          <h4 className="font-medium text-freya-text-primary mb-3">Severity Levels</h4>
          <div className="space-y-2">
            {Object.entries(SEVERITY_CONFIG).map(([key, config]) => {
              const Icon = config.icon
              return (
                <div key={key} className="flex items-center gap-2 text-sm">
                  <Icon className={clsx('w-4 h-4', config.color)} />
                  <span className="text-freya-text-secondary capitalize">{config.label}</span>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
