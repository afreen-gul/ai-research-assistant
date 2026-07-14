import { useState } from 'react'
import { BookOpen, Clock, FileText, StickyNote, Plus, X } from 'lucide-react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Button } from '@/components/ui/button'
import type { Session, Note, SavedPaper, SearchHistoryItem } from '@/services/api'

interface SidebarProps {
  sessions: Session[]
  notes: Note[]
  papers: SavedPaper[]
  searchHistory: SearchHistoryItem[]
  onNewSession: () => void
  onAddNote: (title: string, content: string) => void
  activeSessionId?: string | null
}

export function Sidebar({ sessions, notes, papers, searchHistory, onNewSession, onAddNote, activeSessionId }: SidebarProps) {
  const [composing, setComposing] = useState(false)
  const [noteTitle, setNoteTitle] = useState('')
  const [noteContent, setNoteContent] = useState('')

  const submitNote = () => {
    if (!noteTitle.trim() && !noteContent.trim()) return
    onAddNote(noteTitle.trim(), noteContent.trim())
    setNoteTitle('')
    setNoteContent('')
    setComposing(false)
  }

  return (
    <aside className="w-full lg:w-64 border-r border-border bg-card/50 flex flex-col h-full shrink-0">
      <div className="p-4 border-b border-border">
        <div className="flex items-center gap-2 mb-1">
          <BookOpen className="w-5 h-5 text-primary" />
          <h1 className="text-sm font-semibold tracking-tight">Research Assistant</h1>
        </div>
        <p className="text-[11px] text-muted-foreground">Agentic research workspace</p>
      </div>

      <Tabs defaultValue="history" className="flex-1 flex flex-col min-h-0">
        <TabsList className="mx-3 mt-3 grid grid-cols-3 h-8">
          <TabsTrigger value="history" className="text-[10px] px-1">History</TabsTrigger>
          <TabsTrigger value="papers" className="text-[10px] px-1">Papers</TabsTrigger>
          <TabsTrigger value="notes" className="text-[10px] px-1">Notes</TabsTrigger>
        </TabsList>

        <TabsContent value="history" className="flex-1 min-h-0 mt-2">
          <ScrollArea className="h-full px-3">
            <Button variant="outline" size="sm" className="w-full mb-3" onClick={onNewSession}>
              <Plus className="w-3 h-3 mr-1.5" /> New Session
            </Button>
            <div className="space-y-1">
              {searchHistory.slice(0, 20).map((item) => (
                <div key={item.id} className="p-2 rounded-md hover:bg-accent/50 transition-colors cursor-default">
                  <div className="flex items-start gap-2">
                    <Clock className="w-3 h-3 mt-0.5 text-muted-foreground shrink-0" />
                    <div className="min-w-0">
                      <p className="text-xs truncate">{item.query}</p>
                      <p className="text-[10px] text-muted-foreground mt-0.5">
                        {new Date(item.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
              {searchHistory.length === 0 && (
                <p className="text-xs text-muted-foreground text-center py-8">No searches yet</p>
              )}
            </div>
          </ScrollArea>
        </TabsContent>

        <TabsContent value="papers" className="flex-1 min-h-0 mt-2">
          <ScrollArea className="h-full px-3">
            <div className="space-y-1">
              {papers.map((paper) => (
                <div key={paper.id} className="p-2 rounded-md hover:bg-accent/50 transition-colors">
                  <div className="flex items-start gap-2">
                    <FileText className="w-3 h-3 mt-0.5 text-primary shrink-0" />
                    <div className="min-w-0">
                      <p className="text-xs font-medium truncate">{paper.title}</p>
                      {paper.authors && (
                        <p className="text-[10px] text-muted-foreground truncate">{paper.authors}</p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              {papers.length === 0 && (
                <p className="text-xs text-muted-foreground text-center py-8">No saved papers</p>
              )}
            </div>
          </ScrollArea>
        </TabsContent>

        <TabsContent value="notes" className="flex-1 min-h-0 mt-2">
          <ScrollArea className="h-full px-3">
            {composing ? (
              <div className="mb-3 space-y-2 rounded-md border border-border p-2">
                <input
                  autoFocus
                  value={noteTitle}
                  onChange={(e) => setNoteTitle(e.target.value)}
                  placeholder="Note title"
                  className="w-full text-xs bg-background border border-border rounded px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-ring"
                />
                <textarea
                  value={noteContent}
                  onChange={(e) => setNoteContent(e.target.value)}
                  placeholder="Write a note…"
                  rows={3}
                  className="w-full text-xs bg-background border border-border rounded px-2 py-1.5 resize-none focus:outline-none focus:ring-1 focus:ring-ring"
                />
                <div className="flex gap-1.5">
                  <Button size="sm" className="h-7 text-xs flex-1" onClick={submitNote}>Save</Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-7 text-xs px-2"
                    onClick={() => { setComposing(false); setNoteTitle(''); setNoteContent('') }}
                  >
                    <X className="w-3 h-3" />
                  </Button>
                </div>
              </div>
            ) : (
              <Button variant="outline" size="sm" className="w-full mb-3" onClick={() => setComposing(true)}>
                <Plus className="w-3 h-3 mr-1.5" /> New Note
              </Button>
            )}
            <div className="space-y-1">
              {notes.map((note) => (
                <div key={note.id} className="p-2 rounded-md hover:bg-accent/50 transition-colors">
                  <div className="flex items-start gap-2">
                    <StickyNote className="w-3 h-3 mt-0.5 text-muted-foreground shrink-0" />
                    <div className="min-w-0">
                      <p className="text-xs font-medium truncate">{note.title}</p>
                      <p className="text-[10px] text-muted-foreground line-clamp-2">{note.content}</p>
                    </div>
                  </div>
                </div>
              ))}
              {notes.length === 0 && (
                <p className="text-xs text-muted-foreground text-center py-8">No notes yet</p>
              )}
            </div>
          </ScrollArea>
        </TabsContent>
      </Tabs>
    </aside>
  )
}
