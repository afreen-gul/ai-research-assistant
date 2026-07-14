import { useState } from 'react'
import { ChevronDown, ChevronRight, Loader2, Search, FileText, Globe, Youtube, Database } from 'lucide-react'
import type { ToolEvent } from '@/services/api'
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/components/ui/tooltip'

const TOOL_LABELS: Record<string, { label: string; icon: typeof Search }> = {
  web_search: { label: 'Searching the web', icon: Search },
  academic_search: { label: 'Searching academic sources', icon: Search },
  read_url: { label: 'Reading web page', icon: Globe },
  read_youtube: { label: 'Reading YouTube transcript', icon: Youtube },
  retrieve_documents: { label: 'Retrieving relevant sections', icon: Database },
  extract_pdf_info: { label: 'Reading PDF', icon: FileText },
}

interface ToolStatusProps {
  events: ToolEvent[]
}

export function ToolStatus({ events }: ToolStatusProps) {
  const [expanded, setExpanded] = useState(false)
  if (!events || events.length === 0) return null

  return (
    <div className="mb-2">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
      >
        {expanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
        <Loader2 className="w-3 h-3 animate-spin" />
        Agent used {events.length} tool{events.length > 1 ? 's' : ''}
      </button>
      {expanded && (
        <div className="mt-1.5 space-y-1 pl-4">
          {events.map((ev, i) => {
            const info = TOOL_LABELS[ev.tool] || { label: ev.tool, icon: Search }
            const Icon = info.icon
            return (
              <div key={i} className="tool-status">
                <Icon className="w-3 h-3" />
                <span>{info.label}{ev.args?.query ? `: "${String(ev.args.query).slice(0, 60)}"` : ''}</span>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

interface CitationProps {
  index: number
  source?: { title: string; url: string; authors?: string }
}

export function CitationRef({ index, source }: CitationProps) {
  if (!source) {
    return <sup className="citation-ref">{index}</sup>
  }
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <sup className="citation-ref">{index}</sup>
        </TooltipTrigger>
        <TooltipContent side="top" className="max-w-xs bg-card text-card-foreground border border-border shadow-md">
          <p className="font-medium">{source.title}</p>
          {source.authors && <p className="text-muted-foreground mt-0.5">{source.authors}</p>}
          <a href={source.url} target="_blank" rel="noopener" className="text-primary text-[10px] mt-1 block truncate">
            {source.url}
          </a>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

interface MessageContentProps {
  content: string
  sources?: { title: string; url: string; authors?: string }[]
}

export function MessageContent({ content, sources = [] }: MessageContentProps) {
  const parts = content.split(/(\[\d+\])/g)
  return (
    <div className="text-sm leading-relaxed whitespace-pre-wrap">
      {parts.map((part, i) => {
        const match = part.match(/\[(\d+)\]/)
        if (match) {
          const idx = parseInt(match[1])
          return <CitationRef key={i} index={idx} source={sources[idx - 1]} />
        }
        return <span key={i}>{part}</span>
      })}
    </div>
  )
}
