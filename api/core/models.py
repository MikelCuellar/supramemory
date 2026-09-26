"""Pydantic schemas compartidos."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class NoteBase(BaseModel):
    title: str
    content: str
    source: str = "manual"
    tags: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)  # títulos destino


class NoteCreate(NoteBase):
    id: str | None = None


class NoteUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    tags: list[str] | None = None
    links: list[str] | None = None


class Note(NoteBase):
    id: str
    path: str | None = None
    created_at: datetime
    updated_at: datetime
    backlinks: list[str] = Field(default_factory=list)


class GraphNode(BaseModel):
    id: str
    label: str
    source: str
    tags: list[str] = Field(default_factory=list)
    degree: int = 0  # número de conexiones


class GraphEdge(BaseModel):
    source: str
    target: str | None = None
    target_title: str
    weight: float = 1.0
    kind: Literal["wikilink", "semantic", "temporal", "entity"] = "wikilink"


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class ContextItem(BaseModel):
    note_id: str
    title: str
    snippet: str
    source: str
    score: float
    tags: list[str] = Field(default_factory=list)


class ContextResponse(BaseModel):
    query: str
    items: list[ContextItem]


class HealthResponse(BaseModel):
    status: str
    version: str
    notes_count: int
    links_count: int


class NoteRenameRequest(BaseModel):
    new_title: str
    new_path: str | None = None


class NoteRenameResponse(BaseModel):
    status: str
    old_id: str
    new_id: str
    old_title: str
    new_title: str
    updated_files_count: int
    updated_links_count: int


class UnlinkedMentionItem(BaseModel):
    source_id: str
    source_title: str
    snippet: str
    match_text: str


class UnlinkedMentionsResponse(BaseModel):
    note_id: str
    note_title: str
    mentions: list[UnlinkedMentionItem]


class LinkMentionRequest(BaseModel):
    source_id: str
    target_title: str


class FileTreeNode(BaseModel):
    name: str
    type: Literal["file", "directory"]
    path: str  # relative to vault
    id: str | None = None
    title: str | None = None
    children: list["FileTreeNode"] = Field(default_factory=list)


class CreateFolderRequest(BaseModel):
    path: str


class MoveNoteRequest(BaseModel):
    note_id: str
    target_folder: str  # relative folder path, e.g. "Projects" or ""


class DailyNoteResponse(BaseModel):
    note: Note
    created: bool


class LocalGraphResponse(BaseModel):
    root_id: str
    depth: int
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class DynamicQueryRequest(BaseModel):
    query: str
    limit: int = 50


class DynamicQueryResponse(BaseModel):
    columns: list[str]
    rows: list[list]