import { useState, useEffect, useCallback, useRef } from 'react'
import type { ChatMessage, Document, Session, Note, SavedPaper, SearchHistoryItem, Source } from '@/services/api'
import * as api from '@/services/api'
import { useToast } from '@/components/ui/toast'

export function useSession(onActivity?: () => void) {
  const { toast } = useToast()
  const [sessionId, setSessionId] = useState<string | null>(
    () => localStorage.getItem('sessionId')
  )
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [document, setDocument] = useState<Document | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [citationStyle, setCitationStyle] = useState('apa')
  const inFlightRef = useRef(false)

  useEffect(() => {
    if (sessionId) {
      localStorage.setItem('sessionId', sessionId)
      api.getMessages(sessionId).then(setMessages).catch(console.error)
      api.getDocuments(sessionId).then((docs) => {
        if (docs.length > 0) setDocument(docs[0])
      }).catch(console.error)
    }
  }, [sessionId])

  const sendMessage = useCallback(async (content: string) => {
    if (inFlightRef.current || isLoading) return
    inFlightRef.current = true
    setIsLoading(true)
    const userMsg: ChatMessage = { role: 'user', content }
    setMessages((prev) => [...prev, userMsg])

    try {
      const result = await api.sendChat(content, sessionId || undefined, citationStyle)
      if (!sessionId) setSessionId(result.session_id)

      const assistantMsg: ChatMessage = {
        role: 'assistant',
        content: result.response,
        tool_events: result.tool_events,
        sources: result.sources,
      }
      setMessages((prev) => [...prev, assistantMsg])
      if (result.document) {
        setDocument(result.document)
        toast('Document generated — view it in the Document panel.', 'success')
      }
      onActivity?.()
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Something went wrong. Please try again.'
      toast(message, 'error')
    } finally {
      inFlightRef.current = false
      setIsLoading(false)
    }
  }, [sessionId, citationStyle, toast, onActivity, isLoading])

  const newSession = useCallback(async () => {
    try {
      const session = await api.createSession()
      setSessionId(session.id)
      setMessages([])
      setDocument(null)
      onActivity?.()
    } catch {
      toast('Could not start a new session.', 'error')
    }
  }, [toast, onActivity])

  const uploadPDF = useCallback(async (file: File) => {
    let sid = sessionId
    if (!sid) {
      const session = await api.createSession()
      sid = session.id
      setSessionId(sid)
    }
    return api.uploadPDF(sid, file)
  }, [sessionId])

  return {
    sessionId,
    messages,
    document,
    isLoading,
    citationStyle,
    setCitationStyle,
    sendMessage,
    newSession,
    uploadPDF,
    setDocument,
  }
}

export function useSidebarData() {
  const { toast } = useToast()
  const [sessions, setSessions] = useState<Session[]>([])
  const [notes, setNotes] = useState<Note[]>([])
  const [papers, setPapers] = useState<SavedPaper[]>([])
  const [searchHistory, setSearchHistory] = useState<SearchHistoryItem[]>([])

  const refresh = useCallback(() => {
    api.listSessions().then(setSessions).catch(console.error)
    api.listNotes().then(setNotes).catch(console.error)
    api.listPapers().then(setPapers).catch(console.error)
    api.listSearchHistory().then(setSearchHistory).catch(console.error)
  }, [])

  useEffect(() => { refresh() }, [refresh])

  const addNote = useCallback(async (title: string, content: string, sessionId?: string) => {
    try {
      await api.createNote(title || 'Untitled Note', content, sessionId)
      api.listNotes().then(setNotes).catch(console.error)
      toast('Note saved.', 'success')
    } catch {
      toast('Could not save note.', 'error')
    }
  }, [toast])

  const addPaper = useCallback(async (source: Source) => {
    try {
      await api.savePaper({
        title: source.title || 'Untitled',
        authors: source.authors || '',
        url: source.url || '',
        abstract: source.snippet || '',
      })
      api.listPapers().then(setPapers).catch(console.error)
      toast('Paper saved to your library.', 'success')
    } catch {
      toast('Could not save paper.', 'error')
    }
  }, [toast])

  return { sessions, notes, papers, searchHistory, refresh, addNote, addPaper }
}

export function useTheme() {
  const [dark, setDark] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('theme') === 'dark' ||
        (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches)
    }
    return false
  })

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
    localStorage.setItem('theme', dark ? 'dark' : 'light')
  }, [dark])

  return { dark, toggle: () => setDark((d) => !d) }
}
