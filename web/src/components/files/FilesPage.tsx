/**
 * FilesPage - File Browser & Editor v2.2
 * 
 * Professional file management interface with directory tree navigation,
 * file preview, integrated editor, and modern context menus.
 */

import { useState, useCallback, useRef, useEffect } from 'react'
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
  Code2,
  Copy,
  Trash2,
  ExternalLink,
  Clipboard,
  MoreVertical
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

// Context menu state
interface ContextMenuState {
  show: boolean
  x: number
  y: number
  entry: api.FileEntry | null
}

export function FilesPage() {
  const queryClient = useQueryClient()
  const [currentPath, setCurrentPath] = useState('')
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const [fileContent, setFileContent] = useState('')
  const [originalContent, setOriginalContent] = useState('')
  const [isEditing, setIsEditing] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [expandedDirs, setExpandedDirs] = useState<Set<string>>(new Set(['']))
  
  // Context menu state
  const [contextMenu, setContextMenu] = useState<ContextMenuState>({ show: false, x: 0, y: 0, entry: null })
  const contextMenuRef = useRef<HTMLDivElement>(null)
  
  // Rename dialog state
  const [showRenameDialog, setShowRenameDialog] = useState(false)
  const [renameValue, setRenameValue] = useState('')
  const [renameEntry, setRenameEntry] = useState<api.FileEntry | null>(null)
  
  // Close context menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (contextMenuRef.current && !contextMenuRef.current.contains(e.target as Node)) {
        setContextMenu({ show: false, x: 0, y: 0, entry: null })
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])
  
  // Context menu actions
  const handleContextMenu = (e: React.MouseEvent, entry: api.FileEntry) => {
    e.preventDefault()
    setContextMenu({ show: true, x: e.clientX, y: e.clientY, entry })
  }
  
  const copyPath = () => {
    if (contextMenu.entry) {
      navigator.clipboard.writeText(contextMenu.entry.path)
      setContextMenu({ show: false, x: 0, y: 0, entry: null })
    }
  }
  
  const duplicateFile = async () => {
    if (contextMenu.entry && !contextMenu.entry.is_dir) {
      const originalPath = contextMenu.entry.path
      const ext = originalPath.split('.').pop()
      const baseName = originalPath.replace(`.${ext}`, '')
      const newPath = `${baseName}_copy.${ext}`
      
      try {
        const content = await api.readFile(originalPath)
        await api.writeFile(newPath, content.content)
        queryClient.invalidateQueries({ queryKey: ['files'] })
      } catch (error) {
        console.error('Failed to duplicate file:', error)
      }
    }
    setContextMenu({ show: false, x: 0, y: 0, entry: null })
  }
  
  const startRename = () => {
    if (contextMenu.entry) {
      setRenameEntry(contextMenu.entry)
      setRenameValue(contextMenu.entry.name)
      setShowRenameDialog(true)
    }
    setContextMenu({ show: false, x: 0, y: 0, entry: null })
  }
  
  const confirmRename = async () => {
    if (renameEntry && renameValue.trim() && renameValue !== renameEntry.name) {
      try {
        await api.renameFile(renameEntry.path, renameValue)
        queryClient.invalidateQueries({ queryKey: ['files'] })
        // If we renamed the selected file, update the selection
        if (selectedFile === renameEntry.path) {
          const newPath = renameEntry.path.replace(renameEntry.name, renameValue)
          setSelectedFile(newPath)
        }
      } catch (error) {
        console.error('Failed to rename file:', error)
        alert(`Failed to rename: ${error instanceof Error ? error.message : 'Unknown error'}`)
      }
    }
    setShowRenameDialog(false)
    setRenameEntry(null)
    setRenameValue('')
  }
  
  const handleDeleteFile = async () => {
    if (contextMenu.entry) {
      const isDir = contextMenu.entry.is_dir
      const message = isDir 
        ? `Are you sure you want to delete the folder "${contextMenu.entry.name}" and ALL its contents?`
        : `Are you sure you want to delete "${contextMenu.entry.name}"?`
      
      const confirmed = confirm(message)
      if (confirmed) {
        try {
          // Use recursive=true for directories
          await api.deleteFile(contextMenu.entry.path, isDir)
          queryClient.invalidateQueries({ queryKey: ['files'] })
          // Clear selection if we deleted the selected file
          if (selectedFile === contextMenu.entry.path || 
              (isDir && selectedFile?.startsWith(contextMenu.entry.path + '/'))) {
            setSelectedFile(null)
            setFileContent('')
          }
        } catch (error) {
          console.error('Failed to delete:', error)
          alert(`Failed to delete: ${error instanceof Error ? error.message : 'Unknown error'}`)
        }
      }
    }
    setContextMenu({ show: false, x: 0, y: 0, entry: null })
  }

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
    if (listing?.parent !== undefined && listing?.parent !== null) {
      setCurrentPath(listing.parent)
    } else if (currentPath) {
      // Fallback: compute parent from current path
      const parts = currentPath.split('/').filter(Boolean)
      parts.pop()
      setCurrentPath(parts.join('/'))
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
              {/* Go up button - always show if not at root */}
              {currentPath && (
                <button
                  onClick={navigateUp}
                  className="w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-freya-text-muted hover:text-freya-text-primary hover:bg-freya-bg-tertiary transition-colors"
                >
                  <ArrowLeft className="w-4 h-4" />
                  <span className="text-sm">.. (Parent Directory)</span>
                </button>
              )}

              {sortedEntries.map((entry) => {
                const Icon = getFileIcon(entry.name, entry.is_dir)
                const isSelected = selectedFile === entry.path
                
                return (
                  <button
                    key={entry.path}
                    onClick={() => handleFileSelect(entry)}
                    onContextMenu={(e) => handleContextMenu(e, entry)}
                    className={clsx(
                      'w-full flex items-center gap-2 px-2 py-1.5 rounded-md transition-colors group',
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
                    {/* Context menu trigger */}
                    <button
                      onClick={(e) => { e.stopPropagation(); handleContextMenu(e, entry) }}
                      className="p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-freya-bg-tertiary"
                    >
                      <MoreVertical className="w-3 h-3" />
                    </button>
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
            
            {/* File dates from listing */}
            {listing?.entries.find(e => e.path === selectedFile)?.modified_at && (
              <div>
                <div className="text-sm text-freya-text-muted mb-1">Last Modified</div>
                <div className="text-freya-text-primary text-sm">
                  {new Date(listing.entries.find(e => e.path === selectedFile)!.modified_at!).toLocaleString()}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
      
      {/* Context Menu */}
      {contextMenu.show && contextMenu.entry && (
        <div
          ref={contextMenuRef}
          className="fixed z-50 bg-freya-bg-secondary border border-freya-border rounded-lg shadow-xl py-1 min-w-[180px]"
          style={{ left: contextMenu.x, top: contextMenu.y }}
        >
          <button
            onClick={copyPath}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-freya-text-primary hover:bg-freya-bg-tertiary"
          >
            <Clipboard className="w-4 h-4" />
            Copy Path
            <span className="ml-auto text-xs text-freya-text-muted">Ctrl+Shift+C</span>
          </button>
          
          {!contextMenu.entry.is_dir && (
            <button
              onClick={duplicateFile}
              className="w-full flex items-center gap-2 px-3 py-2 text-sm text-freya-text-primary hover:bg-freya-bg-tertiary"
            >
              <Copy className="w-4 h-4" />
              Duplicate
              <span className="ml-auto text-xs text-freya-text-muted">Ctrl+D</span>
            </button>
          )}
          
          <button
            onClick={startRename}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-freya-text-primary hover:bg-freya-bg-tertiary"
          >
            <Edit3 className="w-4 h-4" />
            Rename
            <span className="ml-auto text-xs text-freya-text-muted">F2</span>
          </button>
          
          <div className="border-t border-freya-border my-1" />
          
          <button
            onClick={() => {
              // Open in external explorer (logs for now)
              console.log(`Open in explorer: ${contextMenu.entry?.path}`)
              setContextMenu({ show: false, x: 0, y: 0, entry: null })
            }}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-freya-text-primary hover:bg-freya-bg-tertiary"
          >
            <ExternalLink className="w-4 h-4" />
            Show in Explorer
          </button>
          
          <div className="border-t border-freya-border my-1" />
          
          <button
            onClick={handleDeleteFile}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-freya-accent-red hover:bg-freya-accent-red/10"
          >
            <Trash2 className="w-4 h-4" />
            Delete
            <span className="ml-auto text-xs text-freya-text-muted">Del</span>
          </button>
        </div>
      )}
      
      {/* Rename Dialog */}
      {showRenameDialog && renameEntry && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-freya-bg-secondary rounded-lg p-6 max-w-md w-full mx-4 shadow-xl">
            <h3 className="text-lg font-semibold text-freya-text-primary mb-4">
              Rename {renameEntry.is_dir ? 'Folder' : 'File'}
            </h3>
            <input
              type="text"
              value={renameValue}
              onChange={(e) => setRenameValue(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && confirmRename()}
              className="input w-full"
              autoFocus
            />
            <div className="flex gap-3 mt-6">
              <button onClick={confirmRename} className="btn-primary flex-1">
                Rename
              </button>
              <button onClick={() => setShowRenameDialog(false)} className="btn-ghost">
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
