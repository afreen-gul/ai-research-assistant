const API_BASE = '/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

export interface ChatMessage {
  id?: string
  role: 'user' | 'assistant'
  content: string
  tool_events?: ToolEvent[]
  sources?: Source[]
}

export interface ToolEvent {
  tool: string
  status: string
  args?: Record<string, unknown>
}

export interface Source {
  title: string
  url: string
  authors?: string
  snippet?: string
}

export interface Document {
  id: string
  title: string
  doc_type: string
  content: string
  citations: string[]
}

export interface Session {
  id: string
  title: string
  created_at: string
}

export interface Note {
  id: string
  title: string
  content: string
  session_id?: string
  created_at: string
}

export interface SavedPaper {
  id: string
  title: string
  authors: string
  url: string
  abstract: string
  created_at: string
}

export interface SearchHistoryItem {
  id: string
  query: string
  results_count: string
  session_id?: string
  created_at: string
}

export async function sendChat(
  message: string,
  sessionId?: string,
  citationStyle = 'apa'
) {
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), 120_000)
  try {
    return await request<{
      session_id: string
      message_id: string
      response: string
      tool_events: ToolEvent[]
      sources: Source[]
      document: Document | null
    }>('/chat', {
      method: 'POST',
      body: JSON.stringify({ message, session_id: sessionId, citation_style: citationStyle }),
      signal: controller.signal,
    })
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new Error('Request timed out. The agent took too long — try a simpler question or wait a moment.')
    }
    throw err
  } finally {
    window.clearTimeout(timeout)
  }
}

export async function createSession(title = 'New Research Session') {
  return request<Session>('/sessions', {
    method: 'POST',
    body: JSON.stringify({ title }),
  })
}

export async function listSessions() {
  return request<Session[]>('/sessions')
}

export async function getMessages(sessionId: string) {
  return request<ChatMessage[]>(`/sessions/${sessionId}/messages`)
}

export async function getDocuments(sessionId: string) {
  return request<Document[]>(`/sessions/${sessionId}/documents`)
}

async function errorDetail(res: Response, fallback: string): Promise<string> {
  const data = await res.json().catch(() => null)
  return (data && (data.detail || data.message)) || fallback
}

export async function uploadPDF(sessionId: string, file: File) {
  const form = new FormData()
  form.append('session_id', sessionId)
  form.append('file', file)
  const res = await fetch(`${API_BASE}/documents/upload`, { method: 'POST', body: form })
  if (!res.ok) throw new Error(await errorDetail(res, 'PDF upload failed'))
  return res.json()
}

export async function exportDocument(
  content: string,
  title: string,
  format: 'markdown' | 'docx' | 'pdf',
  bibliography: string[] = []
) {
  const res = await fetch(`${API_BASE}/documents/export`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content, title, format, bibliography }),
  })
  if (!res.ok) throw new Error(await errorDetail(res, 'Export failed'))
  const blob = await res.blob()
  const ext = format === 'markdown' ? 'md' : format
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${title}.${ext}`
  a.click()
  URL.revokeObjectURL(url)
}

export async function listNotes() {
  return request<Note[]>('/notes')
}

export async function createNote(title: string, content: string, sessionId?: string) {
  return request<Note>('/notes', {
    method: 'POST',
    body: JSON.stringify({ title, content, session_id: sessionId }),
  })
}

export async function listPapers() {
  return request<SavedPaper[]>('/papers')
}

export async function savePaper(paper: Omit<SavedPaper, 'id' | 'created_at'>) {
  return request<SavedPaper>('/papers', {
    method: 'POST',
    body: JSON.stringify(paper),
  })
}

export async function listSearchHistory() {
  return request<SearchHistoryItem[]>('/search-history')
}

export async function healthCheck() {
  return request<{ status: string; gemini_configured: boolean }>('/health')
}

export async function guestLogin() {
  return request<{ token: string; user_id: string; username: string }>('/auth/guest', {
    method: 'POST',
    body: JSON.stringify({}),
  })
}
