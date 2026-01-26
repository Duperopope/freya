# src/freya/api/routes/files.py
"""
Files API Routes

Endpoints for file management:
- Browse directory tree
- Read file contents
- Write/create files
- File search
"""

from __future__ import annotations

import mimetypes
import os
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter()


# -----------------------------------------------------------------------------
# Request/Response Models
# -----------------------------------------------------------------------------
class FileEntry(BaseModel):
    """File or directory entry."""
    name: str
    path: str
    is_dir: bool
    size_bytes: int | None = None
    modified_at: str | None = None
    mime_type: str | None = None


class DirectoryListing(BaseModel):
    """Directory listing result."""
    path: str
    parent: str | None
    entries: list[FileEntry]


class FileContent(BaseModel):
    """File content response."""
    path: str
    name: str
    content: str
    size_bytes: int
    mime_type: str | None
    encoding: str = "utf-8"


class WriteRequest(BaseModel):
    """Request to write a file."""
    path: str = Field(..., description="Relative path from output root")
    content: str = Field(..., description="File content")
    create_dirs: bool = Field(default=True, description="Create parent directories if needed")


class SearchRequest(BaseModel):
    """File search request."""
    query: str = Field(..., description="Search query (filename pattern or content)")
    search_content: bool = Field(default=False, description="Search file contents")
    extensions: list[str] = Field(default_factory=list, description="File extensions to include")
    max_results: int = Field(default=50, ge=1, le=200)


class SearchResult(BaseModel):
    """File search result."""
    path: str
    name: str
    match_type: str  # "filename" or "content"
    preview: str | None = None


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def _validate_path(base: Path, rel_path: str) -> Path:
    """Validate and resolve a path, ensuring it's within base."""
    full_path = (base / rel_path).resolve()
    base_resolved = base.resolve()
    
    if base_resolved not in full_path.parents and full_path != base_resolved:
        raise HTTPException(status_code=403, detail="Access denied: path outside allowed directory")
    
    return full_path


def _get_mime_type(path: Path) -> str | None:
    """Get MIME type for a file."""
    mime, _ = mimetypes.guess_type(str(path))
    return mime


def _is_text_file(path: Path) -> bool:
    """Check if a file is likely a text file."""
    text_extensions = {
        ".txt", ".md", ".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".yaml", ".yml",
        ".toml", ".ini", ".cfg", ".conf", ".xml", ".html", ".htm", ".css", ".scss",
        ".sass", ".less", ".sql", ".sh", ".bash", ".zsh", ".ps1", ".bat", ".cmd",
        ".c", ".cpp", ".h", ".hpp", ".java", ".kt", ".swift", ".go", ".rs", ".rb",
        ".php", ".pl", ".lua", ".r", ".R", ".m", ".mm", ".vue", ".svelte"
    }
    return path.suffix.lower() in text_extensions


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------
@router.get("/browse", response_model=DirectoryListing)
async def browse_directory(request: Request, path: str = "") -> DirectoryListing:
    """
    Browse a directory.
    
    Path is relative to output_root (artifacts/projects).
    """
    state = request.app.state.freya
    
    if not state.ready:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    base = state.config.output_root.resolve()
    
    if path:
        dir_path = _validate_path(base, path)
    else:
        dir_path = base
    
    if not dir_path.exists():
        raise HTTPException(status_code=404, detail="Directory not found")
    
    if not dir_path.is_dir():
        raise HTTPException(status_code=400, detail="Path is not a directory")
    
    entries = []
    try:
        for item in sorted(dir_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            try:
                stat = item.stat()
                entries.append(FileEntry(
                    name=item.name,
                    path=str(item.relative_to(base)),
                    is_dir=item.is_dir(),
                    size_bytes=stat.st_size if item.is_file() else None,
                    modified_at=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)),
                    mime_type=_get_mime_type(item) if item.is_file() else None
                ))
            except (PermissionError, OSError):
                continue
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    parent = None
    if dir_path != base:
        parent_path = dir_path.parent
        if base in parent_path.parents or parent_path == base:
            parent = str(parent_path.relative_to(base)) if parent_path != base else ""
    
    return DirectoryListing(
        path=str(dir_path.relative_to(base)) if dir_path != base else "",
        parent=parent,
        entries=entries
    )


@router.get("/read", response_model=FileContent)
async def read_file(request: Request, path: str) -> FileContent:
    """Read a file's contents."""
    state = request.app.state.freya
    
    if not state.ready:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    base = state.config.output_root.resolve()
    file_path = _validate_path(base, path)
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")
    
    if not _is_text_file(file_path):
        raise HTTPException(status_code=400, detail="Cannot read binary file")
    
    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            content = file_path.read_text(encoding="latin-1")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to read file: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {e}")
    
    return FileContent(
        path=path,
        name=file_path.name,
        content=content,
        size_bytes=len(content.encode("utf-8")),
        mime_type=_get_mime_type(file_path)
    )


@router.post("/write")
async def write_file(request: Request, body: WriteRequest) -> dict[str, Any]:
    """Write content to a file."""
    state = request.app.state.freya
    
    if not state.ready:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    base = state.config.output_root.resolve()
    file_path = _validate_path(base, body.path)
    
    # Security: prevent writing to protected locations
    protected_names = {".git", ".venv", "node_modules", "__pycache__"}
    if any(p in file_path.parts for p in protected_names):
        raise HTTPException(status_code=403, detail="Cannot write to protected directory")
    
    try:
        if body.create_dirs:
            file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_path.write_text(body.content, encoding="utf-8")
        
        return {
            "success": True,
            "path": body.path,
            "size_bytes": len(body.content.encode("utf-8"))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write file: {e}")


@router.delete("/")
async def delete_file(request: Request, path: str) -> dict[str, Any]:
    """Delete a file (not directories)."""
    state = request.app.state.freya
    
    if not state.ready:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    base = state.config.output_root.resolve()
    file_path = _validate_path(base, path)
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if file_path.is_dir():
        raise HTTPException(status_code=400, detail="Cannot delete directories via this endpoint")
    
    try:
        file_path.unlink()
        return {"deleted": True, "path": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete: {e}")


@router.post("/search", response_model=list[SearchResult])
async def search_files(request: Request, body: SearchRequest) -> list[SearchResult]:
    """Search for files by name or content."""
    state = request.app.state.freya
    
    if not state.ready:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    base = state.config.output_root.resolve()
    
    if not base.exists():
        return []
    
    results = []
    query_lower = body.query.lower()
    
    for file_path in base.rglob("*"):
        if len(results) >= body.max_results:
            break
        
        if not file_path.is_file():
            continue
        
        # Filter by extension if specified
        if body.extensions and file_path.suffix.lower() not in [f".{e.lstrip('.')}" for e in body.extensions]:
            continue
        
        rel_path = str(file_path.relative_to(base))
        
        # Filename match
        if query_lower in file_path.name.lower():
            results.append(SearchResult(
                path=rel_path,
                name=file_path.name,
                match_type="filename",
                preview=None
            ))
            continue
        
        # Content search
        if body.search_content and _is_text_file(file_path):
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                if query_lower in content.lower():
                    # Find context around match
                    idx = content.lower().find(query_lower)
                    start = max(0, idx - 50)
                    end = min(len(content), idx + len(body.query) + 50)
                    preview = content[start:end]
                    if start > 0:
                        preview = "..." + preview
                    if end < len(content):
                        preview = preview + "..."
                    
                    results.append(SearchResult(
                        path=rel_path,
                        name=file_path.name,
                        match_type="content",
                        preview=preview
                    ))
            except Exception:
                continue
    
    return results


@router.get("/tree")
async def get_file_tree(request: Request, max_depth: int = 3) -> dict[str, Any]:
    """Get file tree structure (for tree view component)."""
    state = request.app.state.freya
    
    if not state.ready:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    base = state.config.output_root.resolve()
    
    def build_tree(path: Path, depth: int = 0) -> dict[str, Any]:
        if depth > max_depth:
            return {"name": path.name, "type": "directory", "truncated": True}
        
        result: dict[str, Any] = {
            "name": path.name,
            "path": str(path.relative_to(base)) if path != base else "",
        }
        
        if path.is_file():
            result["type"] = "file"
            result["size"] = path.stat().st_size
        else:
            result["type"] = "directory"
            children = []
            try:
                for item in sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                    if item.name.startswith("."):
                        continue
                    children.append(build_tree(item, depth + 1))
            except PermissionError:
                pass
            result["children"] = children
        
        return result
    
    if not base.exists():
        base.mkdir(parents=True, exist_ok=True)
    
    tree = build_tree(base)
    tree["name"] = "projects"  # Root display name
    return tree
