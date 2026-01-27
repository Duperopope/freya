/**
 * Freya API Client
 * 
 * Type-safe API calls to the Freya backend.
 */

const API_BASE = '/api'

interface ApiError {
  error: string
  type?: string
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error: ApiError = await response.json().catch(() => ({
      error: `HTTP ${response.status}: ${response.statusText}`
    }))
    throw new Error(error.error || 'API request failed')
  }
  return response.json()
}

// -----------------------------------------------------------------------------
// Health & System
// -----------------------------------------------------------------------------
export interface HealthResponse {
  status: string
  ready: boolean
  ollama: {
    connected: boolean
    models_count: number
    base_url: string | null
  }
  config: {
    managed_root: string | null
    output_root: string | null
  }
}

export interface SystemInfo {
  cpu_percent: number
  ram_percent: number
  disk_free_gb: number
  disk_total_gb: number
}

export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/health`)
  return handleResponse(res)
}

export async function getSystemInfo(): Promise<SystemInfo> {
  const res = await fetch(`${API_BASE}/system`)
  return handleResponse(res)
}

// -----------------------------------------------------------------------------
// Chat
// -----------------------------------------------------------------------------
export interface ChatRequest {
  message: string
  model?: string
  system_prompt?: string
  hat?: string
  temperature?: number
  max_tokens?: number
  web_search?: boolean
}

export interface ChatResponse {
  content: string
  model: string
  duration_ms: number
  tokens_estimated?: number
  search_results?: SearchResult[]
}

export interface HatPreset {
  name: string
  description: string
  system_prompt: string
}

export interface SearchResult {
  title: string
  url: string
  snippet: string
  source: string
}

export async function generateChat(request: ChatRequest): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })
  return handleResponse(res)
}

export async function getHats(): Promise<HatPreset[]> {
  const res = await fetch(`${API_BASE}/chat/hats`)
  return handleResponse(res)
}

export async function webSearch(query: string, count = 5, provider = 'duckduckgo'): Promise<SearchResult[]> {
  const res = await fetch(`${API_BASE}/chat/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, count, provider }),
  })
  return handleResponse(res)
}

// -----------------------------------------------------------------------------
// Bench
// -----------------------------------------------------------------------------
export interface BenchStatus {
  running: boolean
  program: string
  phase: string
  role: string
  model: string
  model_index: number
  total_models: number
  step_index: number
  total_steps: number
  last_event: string
  progress_percent: number
}

export interface BenchResult {
  role: string
  phase: string
  model: string
  score: number
  latency_ms: number
  status: string
  details?: Record<string, unknown>
}

export interface BillboardEntry {
  role: string
  model: string
  score: number
  latency_ms: number
  options: Record<string, unknown>
}

export async function getBenchStatus(): Promise<BenchStatus> {
  const res = await fetch(`${API_BASE}/bench/status`)
  return handleResponse(res)
}

export async function startBench(program: string, resume = true): Promise<{ started: boolean }> {
  const res = await fetch(`${API_BASE}/bench/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ program, resume }),
  })
  return handleResponse(res)
}

export async function stopBench(): Promise<{ message: string }> {
  const res = await fetch(`${API_BASE}/bench/stop`, { method: 'POST' })
  return handleResponse(res)
}

export async function getBillboard(): Promise<BillboardEntry[]> {
  const res = await fetch(`${API_BASE}/bench/billboard`)
  return handleResponse(res)
}

export async function getBenchHistory(program = 'bench-fast', limit = 100): Promise<BenchResult[]> {
  const res = await fetch(`${API_BASE}/bench/history?program=${program}&limit=${limit}`)
  return handleResponse(res)
}

export async function applyRouting(): Promise<{ success: boolean }> {
  const res = await fetch(`${API_BASE}/bench/apply-routing`, { method: 'POST' })
  return handleResponse(res)
}

// -----------------------------------------------------------------------------
// Models
// -----------------------------------------------------------------------------
export interface ModelInfo {
  name: string
  size_bytes?: number
  size_gb?: number
  modified_at?: string
  is_freya_pulled: boolean
}

export interface RoutingConfig {
  role: string
  model: string
  options: Record<string, unknown>
}

export async function getModels(): Promise<ModelInfo[]> {
  const res = await fetch(`${API_BASE}/models/`)
  return handleResponse(res)
}

export async function pullModel(model: string): Promise<{ started: boolean }> {
  const res = await fetch(`${API_BASE}/models/pull`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model }),
  })
  return handleResponse(res)
}

export async function getRouting(): Promise<RoutingConfig[]> {
  const res = await fetch(`${API_BASE}/models/routing`)
  return handleResponse(res)
}

export async function setRouting(configs: RoutingConfig[]): Promise<{ saved: boolean }> {
  const res = await fetch(`${API_BASE}/models/routing`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(configs),
  })
  return handleResponse(res)
}

// -----------------------------------------------------------------------------
// BMAD
// -----------------------------------------------------------------------------
export interface BMADStatus {
  running: boolean
  current_agent: string | null
  agents_completed: string[]
  artifacts_generated: string[]
  error: string | null
}

export interface ArtifactInfo {
  name: string
  path: string
  size_bytes: number
  modified_at: string
}

export async function getBMADStatus(): Promise<BMADStatus> {
  const res = await fetch(`${API_BASE}/bmad/status`)
  return handleResponse(res)
}

export async function runBMAD(goal: string, projectName = 'FreyaProject'): Promise<{ started: boolean }> {
  const res = await fetch(`${API_BASE}/bmad/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ goal, project_name: projectName }),
  })
  return handleResponse(res)
}

export async function getArtifacts(project?: string): Promise<ArtifactInfo[]> {
  const url = project 
    ? `${API_BASE}/bmad/artifacts?project=${encodeURIComponent(project)}`
    : `${API_BASE}/bmad/artifacts`
  const res = await fetch(url)
  return handleResponse(res)
}

export async function getArtifact(path: string): Promise<{ name: string; path: string; content: string }> {
  const res = await fetch(`${API_BASE}/bmad/artifact?path=${encodeURIComponent(path)}`)
  return handleResponse(res)
}

// -----------------------------------------------------------------------------
// Files
// -----------------------------------------------------------------------------
export interface FileEntry {
  name: string
  path: string
  is_dir: boolean
  size_bytes?: number
  modified_at?: string
  mime_type?: string
}

export interface DirectoryListing {
  path: string
  parent: string | null
  entries: FileEntry[]
}

export interface FileContent {
  path: string
  name: string
  content: string
  size_bytes: number
  mime_type?: string
}

export async function browseDirectory(path = ''): Promise<DirectoryListing> {
  const res = await fetch(`${API_BASE}/files/browse?path=${encodeURIComponent(path)}`)
  return handleResponse(res)
}

export async function readFile(path: string): Promise<FileContent> {
  const res = await fetch(`${API_BASE}/files/read?path=${encodeURIComponent(path)}`)
  return handleResponse(res)
}

export async function writeFile(path: string, content: string): Promise<{ success: boolean }> {
  const res = await fetch(`${API_BASE}/files/write`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path, content }),
  })
  return handleResponse(res)
}

export async function getFileTree(maxDepth = 3): Promise<Record<string, unknown>> {
  const res = await fetch(`${API_BASE}/files/tree?max_depth=${maxDepth}`)
  return handleResponse(res)
}

export async function deleteFile(path: string): Promise<{ deleted: boolean }> {
  const res = await fetch(`${API_BASE}/files/?path=${encodeURIComponent(path)}`, {
    method: 'DELETE',
  })
  return handleResponse(res)
}

export async function renameFile(path: string, newName: string): Promise<{ success: boolean; new_path: string }> {
  const res = await fetch(`${API_BASE}/files/rename`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path, new_name: newName }),
  })
  return handleResponse(res)
}

// -----------------------------------------------------------------------------
// Watch
// -----------------------------------------------------------------------------
export interface WatchItem {
  source: string
  title: string
  url: string
  published: string
  cve?: string
  severity?: string
  description?: string
  tags?: string[]
}

export interface WatchFeed {
  source: string
  items: WatchItem[]
  fetched_at: string
  cached: boolean
  item_count: number
}

export interface CVEInfo {
  cve_id: string
  description: string
  severity?: string
  cvss_score?: number
  references: string[]
  affected_products: string[]
}

export interface WatchStats {
  cache_dir: string
  config: {
    auto_refresh: boolean
    refresh_interval_minutes: number
    enabled_sources: string[]
  }
  sources: Record<string, {
    last_fetch: string | null
    item_count: number
    cache_age_minutes: number
    is_stale: boolean
  }>
}

export async function getWatchFeed(limit = 50, sources?: string): Promise<WatchItem[]> {
  let url = `${API_BASE}/watch/?limit=${limit}`
  if (sources) {
    url += `&sources=${encodeURIComponent(sources)}`
  }
  const res = await fetch(url)
  return handleResponse(res)
}

export async function getCISAKEV(limit = 50): Promise<WatchFeed> {
  const res = await fetch(`${API_BASE}/watch/cisa-kev?limit=${limit}`)
  return handleResponse(res)
}

export async function getCERTFR(limit = 30): Promise<WatchFeed> {
  const res = await fetch(`${API_BASE}/watch/cert-fr?limit=${limit}`)
  return handleResponse(res)
}

export async function getNVDRecent(limit = 50, days = 7): Promise<WatchFeed> {
  const res = await fetch(`${API_BASE}/watch/nvd?limit=${limit}&days=${days}`)
  return handleResponse(res)
}

export async function getExploitDB(limit = 30): Promise<WatchFeed> {
  const res = await fetch(`${API_BASE}/watch/exploitdb?limit=${limit}`)
  return handleResponse(res)
}

export async function getGitHubAdvisories(limit = 30): Promise<WatchFeed> {
  const res = await fetch(`${API_BASE}/watch/github?limit=${limit}`)
  return handleResponse(res)
}

export async function lookupCVE(cveId: string): Promise<CVEInfo> {
  const res = await fetch(`${API_BASE}/watch/cve/${encodeURIComponent(cveId)}`)
  return handleResponse(res)
}

export async function getWatchStats(): Promise<WatchStats> {
  const res = await fetch(`${API_BASE}/watch/stats`)
  return handleResponse(res)
}

export async function forceRefreshWatch(sources?: string): Promise<{ status: string; cleared_caches: string[] }> {
  let url = `${API_BASE}/watch/refresh`
  if (sources) {
    url += `?sources=${encodeURIComponent(sources)}`
  }
  const res = await fetch(url, { method: 'POST' })
  return handleResponse(res)
}

// -----------------------------------------------------------------------------
// Settings
// -----------------------------------------------------------------------------
export interface PathsConfig {
  managed_root: string
  cache_root: string
  artifacts_root: string
  output_root: string
  prompts_root: string
  workspace_root: string
  routing_path: string
}

export interface PromptInfo {
  name: string
  path: string
  size_bytes: number
  preview?: string
}

export async function getPaths(): Promise<PathsConfig> {
  const res = await fetch(`${API_BASE}/settings/paths`)
  return handleResponse(res)
}

export async function getPrompts(): Promise<PromptInfo[]> {
  const res = await fetch(`${API_BASE}/settings/prompts`)
  return handleResponse(res)
}

export async function getPrompt(name: string): Promise<{ name: string; content: string }> {
  const res = await fetch(`${API_BASE}/settings/prompts/${encodeURIComponent(name)}`)
  return handleResponse(res)
}

export async function savePrompt(name: string, content: string): Promise<{ saved: boolean }> {
  const res = await fetch(`${API_BASE}/settings/prompts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, content }),
  })
  return handleResponse(res)
}

export async function getVersion(): Promise<{ version: string; api_version: string }> {
  const res = await fetch(`${API_BASE}/settings/version`)
  return handleResponse(res)
}

// -----------------------------------------------------------------------------
// Cyber Intelligence Query
// -----------------------------------------------------------------------------
export interface CyberQueryRequest {
  query: string
  include_cves?: boolean
  include_alerts?: boolean
  max_results?: number
}

export async function cyberQuery(request: CyberQueryRequest): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat/cyber-query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })
  return handleResponse(res)
}

// -----------------------------------------------------------------------------
// Hybrid Routing (v2.2)
// -----------------------------------------------------------------------------
export interface HybridRoutingConfig {
  enabled: boolean
  percent_threshold: number
  local_min_score: number
  fallback_chain: string[]
  health_timeout_sec: number
  health_check_interval_min: number
  max_retries: number
  quota_cache_sec: number
}

export interface ProviderConfig {
  name: string
  base_url: string
  enabled: boolean
  priority: number
  models: string[]
  rate_limits: {
    rpm?: number
    tpm?: number
    rpd?: number
    tpd?: number
  }
  free_tier: {
    credits_usd?: number
    requests_per_day?: number
    tokens_per_day?: number
  }
  has_api_key: boolean
}

export interface LocalRuntime {
  name: string
  port: number
  is_running: boolean
  models_count: number
  last_check: string
}

export interface UsageStats {
  total_requests: number
  local_requests: number
  remote_requests: number
  by_provider: Record<string, {
    requests: number
    tokens_used: number
    estimated_cost: number
  }>
  quotas: Record<string, {
    used: number
    limit: number
    reset_at: string
  }>
}

export interface ConsumptionPrediction {
  role: string
  provider: string
  estimated_output_tokens: number
  estimated_cost_usd: number
  within_free_tier: boolean
  recommendation: string
}

export async function getHybridRoutingConfig(): Promise<HybridRoutingConfig> {
  const res = await fetch(`${API_BASE}/settings/hybrid-routing`)
  return handleResponse(res)
}

export async function updateHybridRoutingConfig(config: Partial<HybridRoutingConfig>): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE}/settings/hybrid-routing`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  })
  return handleResponse(res)
}

export async function getProviders(): Promise<Record<string, ProviderConfig>> {
  const res = await fetch(`${API_BASE}/settings/providers`)
  return handleResponse(res)
}

export async function getProviderHealth(): Promise<Record<string, { healthy: boolean; latency_ms: number; last_check: string }>> {
  const res = await fetch(`${API_BASE}/settings/provider-health`)
  return handleResponse(res)
}

export async function getLocalRuntimes(): Promise<Record<string, LocalRuntime>> {
  const res = await fetch(`${API_BASE}/settings/local-runtimes`)
  return handleResponse(res)
}

export async function detectLocalRuntimes(): Promise<Record<string, LocalRuntime>> {
  const res = await fetch(`${API_BASE}/settings/local-runtimes/detect`, { method: 'POST' })
  return handleResponse(res)
}

export async function getUsageStats(): Promise<UsageStats> {
  const res = await fetch(`${API_BASE}/settings/usage-stats`)
  return handleResponse(res)
}

export async function predictConsumption(role: string, promptTokens = 500, provider = 'local'): Promise<ConsumptionPrediction> {
  const res = await fetch(`${API_BASE}/settings/predict-consumption`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ role, prompt_tokens: promptTokens, provider }),
  })
  return handleResponse(res)
}

export async function updateProviderKey(provider: string, apiKey: string): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE}/settings/provider-key`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ provider, api_key: apiKey }),
  })
  return handleResponse(res)
}

export async function syncBMAD(): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE}/settings/sync-bmad`, { method: 'POST' })
  return handleResponse(res)
}
