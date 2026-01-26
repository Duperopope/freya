/**
 * FilesPage - File Browser & Editor
 * 
 * Professional file management interface with directory tree navigation,
 * file preview, and integrated editor for text files.
 */

import { useState, useCallback } from 'react'
import {
  Folder,
  FolderOpen,
  File,
  FileText,
  FileCode,
  FileJson,
  FileCog,
  ChevronRight,
  Home,
  RefreshCw,
  Search,
  Download,
  Edit3,
  Save,
  X,
  HardDrive,
  ArrowLeft,
  Code2
} from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { clsx } from 'clsx'
import * as api from '../../lib/api'

// File icon mapping
const getFileIcon = (name: string, isDir: boolean) => {
  if (isDir) return Folder
  
  const ext = name.split('.').pop()?.toLowerCase()
  switch (ext) {
    case 'py':
    case 'js':
    case 'ts':
    case 'tsx':
    case 'jsx':
      return FileCode
    case 'json':
      return FileJson
    case 'md':
    case 'txt':
      return FileText
    case 'yaml':
    case 'yml':
    case 'toml':
    case 'ini':
      return FileCog
    default:
      return File
  }
}

// Get syntax highlighting mode
const getLanguage = (name: string): string => {
  const ext = name.split('.').pop()?.toLowerCase()
  const mapping: Record<string, string> = {
    py: 'python',
    js: 'javascript',
    ts: 'typescript',
    tsx: 'typescript',
    jsx: 'javascript',
    json: 'json',
    md: 'markdown',
    yaml: 'yaml',
    yml: 'yaml',
    toml: 'toml',
    html: 'html',
    css: 'css',
    sh: 'bash',
    ps1: 'powershell',
  }
  return mapping[ext || ''] || 'plaintext'
}

// TreeNode interface reserved for future tree view implementation
// interface TreeNode {
//   name: string
//   path: string
//   isDir: boolean
//   children?: TreeNode[]
//   expanded?: boolean
// }

export function FilesPage() {
  const queryClient = useQueryClient()
  const [currentPath, setCurrentPath] = useState('')
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const [fileContent, setFileContent] = useState('')
  const [originalContent, setOriginalContent] = useState('')
  const [isEditing, setIsEditing] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [expandedDirs, setExpandedDirs] = useState<Set<string>>(new Set(['']))

  // Fetch directory listing
  const { data: listing, isLoading } = useQuery({
    queryKey: ['files', currentPath],
    queryFn: () => api.browseDirectory(currentPath),
  })

  // Read file mutation
  const readFileMutation = useMutation({
    mutationFn: (path: string) => api.readFile(path),
    onSuccess: (data) => {
      setFileContent(data.content)
      setOriginalContent(data.content)
      setIsEditing(false)
    },
  })

  // Write file mutation
  const writeFileMutation = useMutation({
    mutationFn: () => api.writeFile(selectedFile!, fileContent),
    onSuccess: () => {
      setOriginalContent(fileContent)
      setIsEditing(false)
      queryClient.invalidateQueries({ queryKey: ['files'] })
    },
  })

  // Handle file selection
  const handleFileSelect = useCallback((entry: api.FileEntry) => {
    if (entry.is_dir) {
      setCurrentPath(entry.path)
      setExpandedDirs(prev => new Set([...prev, entry.path]))
    } else {
      setSelectedFile(entry.path)
      readFileMutation.mutate(entry.path)
    }
  }, [readFileMutation])

  // Navigate up
  const navigateUp = () => {
    if (listing?.parent) {
      setCurrentPath(listing.parent)
    }
  }

  // Navigate to root
  const navigateToRoot = () => {
    setCurrentPath('')
  }

  // Toggle directory expansion (reserved for tree view)
  // const toggleDir = (path: string) => {
  //   setExpandedDirs(prev => {
  //     const next = new Set(prev)
  //     if (next.has(path)) {
  //       next.delete(path)
  //     } else {
  //       next.add(path)
  //     }
  //     return next
  //   })
  // }

  // Check if content has changed
  const hasChanges = fileContent !== originalContent

  // Filter entries by search
  const filteredEntries = listing?.entries.filter(entry =>
    entry.name.toLowerCase().includes(searchQuery.toLowerCase())
  ) || []

  // Sort entries: directories first, then by name
  const sortedEntries = [...filteredEntries].sort((a, b) => {
    if (a.is_dir !== b.is_dir) return a.is_dir ? -1 : 1
    return a.name.localeCompare(b.name)
  })

  // Breadcrumb parts
  const pathParts = currentPath ? currentPath.split('/').filter(Boolean) : []

  return (
    <div className="h-full flex overflow-hidden">
      {/* File Tree Sidebar */}
      <div className="w-72 border-r border-freya-border bg-freya-bg-secondary flex flex-col">
        {/* Toolbar */}
        <div className="p-3 border-b border-freya-border">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-freya-text-muted" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search files..."
              className="input pl-9 py-2 text-sm"
            />
          </div>
        </div>

        {/* Breadcrumb */}
        <div className="px-3 py-2 border-b border-freya-border flex items-center gap-1 text-sm overflow-x-auto">
          <button
            onClick={navigateToRoot}
            className="p-1 rounded hover:bg-freya-bg-tertiary text-freya-text-muted hover:text-freya-text-primary"
          >
            <Home className="w-4 h-4" />
          </button>
          {pathParts.length > 0 && (
            <>
              <ChevronRight className="w-4 h-4 text-freya-text-muted flex-shrink-0" />
              {pathParts.map((part, idx) => (
                <div key={idx} className="flex items-center gap-1">
                  <button
                    onClick={() => setCurrentPath(pathParts.slice(0, idx + 1).join('/'))}
                    className="px-1 rounded hover:bg-freya-bg-tertiary text-freya-text-secondary hover:text-freya-text-primary truncate max-w-[100px]"
                  >
                    {part}
                  </button>
                  {idx < pathParts.length - 1 && (
                    <ChevronRight className="w-4 h-4 text-freya-text-muted flex-shrink-0" />
                  )}
                </div>
              ))}
            </>
          )}
        </div>

        {/* File List */}
        <div className="flex-1 overflow-y-auto p-2">
          {isLoading ? (
            <div className="flex items-center justify-center h-32">
              <RefreshCw className="w-5 h-5 text-freya-text-muted animate-spin" />
            </div>
          ) : sortedEntries.length > 0 ? (
            <div className="space-y-0.5">
              {/* Go up button */}
              {listing?.parent !== null && (
                <button
                  onClick={navigateUp}
                  className="w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-freya-text-muted hover:text-freya-text-primary hover:bg-freya-bg-tertiary transition-colors"
                >
                  <ArrowLeft className="w-4 h-4" />
                  <span className="text-sm">..</span>
                </button>
              )}

              {sortedEntries.map((entry) => {
                const Icon = getFileIcon(entry.name, entry.is_dir)
                const isSelected = selectedFile === entry.path
                
                return (
                  <button
                    key={entry.path}
                    onClick={() => handleFileSelect(entry)}
                    className={clsx(
                      'w-full flex items-center gap-2 px-2 py-1.5 rounded-md transition-colors',
                      isSelected
                        ? 'bg-freya-accent-blue/10 text-freya-accent-blue'
                        : 'text-freya-text-secondary hover:text-freya-text-primary hover:bg-freya-bg-tertiary'
                    )}
                  >
                    {entry.is_dir ? (
                      expandedDirs.has(entry.path) ? (
                        <FolderOpen className="w-4 h-4 text-freya-accent-yellow" />
                      ) : (
                        <Folder className="w-4 h-4 text-freya-accent-yellow" />
                      )
                    ) : (
                      <Icon className={clsx('w-4 h-4', isSelected ? 'text-freya-accent-blue' : 'text-freya-text-muted')} />
                    )}
                    <span className="text-sm truncate flex-1 text-left">{entry.name}</span>
                    {!entry.is_dir && entry.size_bytes !== undefined && (
                      <span className="text-xs text-freya-text-muted">
                        {entry.size_bytes < 1024
                          ? `${entry.size_bytes} B`
                          : entry.size_bytes < 1024 * 1024
                            ? `${(entry.size_bytes / 1024).toFixed(1)} KB`
                            : `${(entry.size_bytes / 1024 / 1024).toFixed(1)} MB`}
                      </span>
                    )}
                  </button>
                )
              })}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-32 text-freya-text-muted">
              <Folder className="w-10 h-10 mb-2 opacity-30" />
              <p className="text-sm">No files found</p>
            </div>
          )}
        </div>

        {/* Stats */}
        {listing && (
          <div className="px-3 py-2 border-t border-freya-border text-xs text-freya-text-muted">
            {listing.entries.filter(e => e.is_dir).length} folders,{' '}
            {listing.entries.filter(e => !e.is_dir).length} files
          </div>
        )}
      </div>

      {/* File Preview/Editor */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {selectedFile ? (
          <>
            {/* File Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-freya-border bg-freya-bg-secondary">
              <div className="flex items-center gap-3">
                <Code2 className="w-5 h-5 text-freya-accent-purple" />
                <div>
                  <div className="font-medium text-freya-text-primary">
                    {selectedFile.split('/').pop()}
                  </div>
                  <div className="text-xs text-freya-text-muted">
                    {getLanguage(selectedFile)} • {fileContent.split('\n').length} lines
                  </div>
                </div>
                {hasChanges && (
                  <span className="badge badge-yellow">Modified</span>
                )}
              </div>

              <div className="flex items-center gap-2">
                {isEditing ? (
                  <>
                    <button
                      onClick={() => {
                        setFileContent(originalContent)
                        setIsEditing(false)
                      }}
                      className="btn-ghost text-sm flex items-center gap-2"
                    >
                      <X className="w-4 h-4" />
                      Cancel
                    </button>
                    <button
                      onClick={() => writeFileMutation.mutate()}
                      disabled={!hasChanges || writeFileMutation.isPending}
                      className="btn-primary text-sm flex items-center gap-2"
                    >
                      <Save className="w-4 h-4" />
                      Save
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      onClick={() => setIsEditing(true)}
                      className="btn-secondary text-sm flex items-center gap-2"
                    >
                      <Edit3 className="w-4 h-4" />
                      Edit
                    </button>
                    <button className="btn-ghost p-2">
                      <Download className="w-4 h-4" />
                    </button>
                  </>
                )}
              </div>
            </div>

            {/* File Content */}
            <div className="flex-1 overflow-hidden">
              {readFileMutation.isPending ? (
                <div className="flex items-center justify-center h-full">
                  <RefreshCw className="w-6 h-6 text-freya-text-muted animate-spin" />
                </div>
              ) : isEditing ? (
                <textarea
                  value={fileContent}
                  onChange={(e) => setFileContent(e.target.value)}
                  className="w-full h-full p-4 bg-freya-bg-primary text-freya-text-primary font-mono text-sm resize-none focus:outline-none"
                  spellCheck={false}
                />
              ) : (
                <div className="h-full overflow-auto">
                  <pre className="p-4 text-sm font-mono">
                    <code className="text-freya-text-primary whitespace-pre-wrap break-all">
                      {fileContent.split('\n').map((line, idx) => (
                        <div key={idx} className="flex hover:bg-freya-bg-tertiary/30">
                          <span className="w-12 pr-4 text-right text-freya-text-muted select-none">
                            {idx + 1}
                          </span>
                          <span className="flex-1">{line || ' '}</span>
                        </div>
                      ))}
                    </code>
                  </pre>
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-freya-text-muted">
            <div className="text-center">
              <FileText className="w-16 h-16 mx-auto mb-4 opacity-20" />
              <h3 className="text-lg font-medium text-freya-text-secondary mb-2">
                No file selected
              </h3>
              <p className="text-sm">
                Select a file from the sidebar to view or edit its contents
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Right Sidebar - File Info (optional) */}
      {selectedFile && !isEditing && (
        <div className="w-64 border-l border-freya-border bg-freya-bg-secondary p-4 hidden lg:block">
          <h4 className="font-medium text-freya-text-primary mb-4">File Information</h4>
          
          <div className="space-y-4">
            <div>
              <div className="text-sm text-freya-text-muted mb-1">Name</div>
              <div className="text-freya-text-primary text-sm font-mono break-all">
                {selectedFile.split('/').pop()}
              </div>
            </div>

            <div>
              <div className="text-sm text-freya-text-muted mb-1">Path</div>
              <div className="text-freya-text-secondary text-xs font-mono break-all">
                {selectedFile}
              </div>
            </div>

            <div>
              <div className="text-sm text-freya-text-muted mb-1">Type</div>
              <div className="text-freya-text-primary text-sm">
                {getLanguage(selectedFile).charAt(0).toUpperCase() + getLanguage(selectedFile).slice(1)}
              </div>
            </div>

            <div>
              <div className="text-sm text-freya-text-muted mb-1">Size</div>
              <div className="flex items-center gap-2 text-freya-text-primary text-sm">
                <HardDrive className="w-4 h-4 text-freya-text-muted" />
                {new Blob([fileContent]).size < 1024
                  ? `${new Blob([fileContent]).size} bytes`
                  : `${(new Blob([fileContent]).size / 1024).toFixed(1)} KB`}
              </div>
            </div>

            <div>
              <div className="text-sm text-freya-text-muted mb-1">Lines</div>
              <div className="text-freya-text-primary text-sm">
                {fileContent.split('\n').length}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
