import { useRef, useState } from 'react'
import { Send, Paperclip, Loader2, BookmarkPlus, ExternalLink } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { ToolStatus, MessageContent } from '@/components/CitationRenderer'
import type { ChatMessage, Source } from '@/services/api'

interface ChatPanelProps {
  messages: ChatMessage[]
  isLoading: boolean
  onSend: (message: string) => void
  onUploadPDF: (file: File) => void
  onSavePaper: (source: Source) => void
  citationStyle: string
  onCitationStyleChange: (style: string) => void
}

function SourceList({ sources, onSavePaper }: { sources: Source[]; onSavePaper: (s: Source) => void }) {
  if (!sources || sources.length === 0) return null
  const seen = new Set<string>()
  const unique = sources.filter((s) => {
    const key = s.url || s.title
    if (!key || seen.has(key)) return false
    seen.add(key)
    return true
  })
  return (
    <div className="mt-3 border-t border-border/60 pt-2.5">
      <p className="text-[10px] uppercase tracking-wide text-muted-foreground mb-1.5">Sources</p>
      <ol className="space-y-1">
        {unique.map((s, i) => (
          <li key={i} className="flex items-start gap-1.5 text-xs group">
            <span className="text-primary font-medium shrink-0">[{i + 1}]</span>
            <div className="min-w-0 flex-1">
              <a
                href={s.url}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-primary transition-colors inline-flex items-center gap-1"
              >
                <span className="truncate align-middle">{s.title || s.url}</span>
                {s.url && <ExternalLink className="w-3 h-3 shrink-0 opacity-50" />}
              </a>
            </div>
            <button
              onClick={() => onSavePaper(s)}
              title="Save to library"
              className="opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-primary shrink-0"
            >
              <BookmarkPlus className="w-3.5 h-3.5" />
            </button>
          </li>
        ))}
      </ol>
    </div>
  )
}

export function ChatPanel({
  messages,
  isLoading,
  onSend,
  onUploadPDF,
  onSavePaper,
  citationStyle,
  onCitationStyleChange,
}: ChatPanelProps) {
  const [input, setInput] = useState('')
  const fileRef = useRef<HTMLInputElement>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return
    onSend(input.trim())
    setInput('')
  }

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) onUploadPDF(file)
    e.target.value = ''
  }

  return (
    <div className="flex flex-col h-full min-w-0 flex-1">
      <div className="px-4 py-3 border-b border-border flex items-center justify-between">
        <h2 className="text-sm font-medium">Research Chat</h2>
        <select
          value={citationStyle}
          onChange={(e) => onCitationStyleChange(e.target.value)}
          className="text-xs bg-background border border-border rounded-md px-2 py-1"
        >
          <option value="apa">APA</option>
          <option value="ieee">IEEE</option>
          <option value="mla">MLA</option>
        </select>
      </div>

      <ScrollArea className="flex-1 px-4">
        <div className="py-4 space-y-6 max-w-3xl mx-auto">
          {messages.length === 0 && (
            <div className="text-center py-16">
              <h3 className="text-lg font-medium text-foreground/80 mb-2">What would you like to research?</h3>
              <p className="text-sm text-muted-foreground max-w-md mx-auto">
                Ask a research question, request a literature review, upload a PDF, or paste a URL.
                The agent will decide which tools to use.
              </p>
              <div className="mt-6 flex flex-wrap gap-2 justify-center">
                {[
                  'Summarize recent advances in transformer architectures',
                  'Literature review on RAG systems for legal documents',
                  'Compare BERT vs GPT for text classification',
                ].map((suggestion) => (
                  <button
                    key={suggestion}
                    disabled={isLoading}
                    onClick={() => onSend(suggestion)}
                    className="text-xs px-3 py-1.5 rounded-full border border-border hover:bg-accent transition-colors text-muted-foreground hover:text-foreground disabled:opacity-50 disabled:pointer-events-none"
                  >
                    {suggestion.slice(0, 50)}…
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={msg.role === 'user' ? 'flex justify-end' : ''}>
              <div
                className={
                  msg.role === 'user'
                    ? 'bg-primary text-primary-foreground rounded-2xl rounded-br-md px-4 py-2.5 max-w-[85%]'
                    : 'max-w-[95%]'
                }
              >
                {msg.role === 'assistant' && msg.tool_events && (
                  <ToolStatus events={msg.tool_events} />
                )}
                {msg.role === 'user' ? (
                  <p className="text-sm">{msg.content}</p>
                ) : (
                  <>
                    <MessageContent content={msg.content} sources={msg.sources} />
                    {msg.sources && msg.sources.length > 0 && (
                      <SourceList sources={msg.sources} onSavePaper={onSavePaper} />
                    )}
                  </>
                )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="w-4 h-4 animate-spin" />
              Agent is thinking…
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      </ScrollArea>

      <form onSubmit={handleSubmit} className="p-4 border-t border-border">
        <div className="flex items-end gap-2 max-w-3xl mx-auto">
          <input ref={fileRef} type="file" accept=".pdf" className="hidden" onChange={handleFile} />
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={() => fileRef.current?.click()}
            title="Upload PDF"
          >
            <Paperclip className="w-4 h-4" />
          </Button>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSubmit(e)
              }
            }}
            placeholder="Ask a research question…"
            rows={1}
            className="flex-1 resize-none rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring min-h-[40px] max-h-32"
          />
          <Button type="submit" size="icon" disabled={!input.trim() || isLoading}>
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </form>
    </div>
  )
}
