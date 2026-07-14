import { useState } from 'react'
import { Download, FileText, BookMarked } from 'lucide-react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Button } from '@/components/ui/button'
import { exportDocument } from '@/services/api'
import type { Document } from '@/services/api'
import { useToast } from '@/components/ui/toast'

interface DocumentPanelProps {
  document: Document | null
}

export function DocumentPanel({ document }: DocumentPanelProps) {
  const { toast } = useToast()
  const [exporting, setExporting] = useState<string | null>(null)

  const handleExport = async (format: 'markdown' | 'docx' | 'pdf') => {
    if (!document) return
    setExporting(format)
    try {
      await exportDocument(document.content, document.title, format, document.citations)
      toast(`Exported as ${format.toUpperCase()}.`, 'success')
    } catch (err) {
      toast(err instanceof Error ? err.message : `Could not export as ${format.toUpperCase()}.`, 'error')
    } finally {
      setExporting(null)
    }
  }

  if (!document) {
    return (
      <aside className="w-full lg:w-96 border-l border-border bg-card/30 flex flex-col h-full shrink-0">
        <div className="p-4 border-b border-border">
          <h2 className="text-sm font-medium">Document Preview</h2>
        </div>
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="text-center">
            <FileText className="w-10 h-10 text-muted-foreground/40 mx-auto mb-3" />
            <p className="text-sm text-muted-foreground">
              Generated documents will appear here — summaries, literature reviews, reports, and more.
            </p>
          </div>
        </div>
      </aside>
    )
  }

  return (
    <aside className="w-full lg:w-96 border-l border-border bg-card/30 flex flex-col h-full shrink-0">
      <div className="p-4 border-b border-border flex items-center justify-between gap-2">
        <div className="min-w-0">
          <h2 className="text-sm font-medium truncate">{document.title}</h2>
          <p className="text-[10px] text-muted-foreground capitalize">{document.doc_type.replace('_', ' ')}</p>
        </div>
        <div className="flex gap-1 shrink-0">
          {(['markdown', 'docx', 'pdf'] as const).map((fmt) => (
            <Button
              key={fmt}
              variant="outline"
              size="sm"
              className="text-[10px] h-7 px-2"
              disabled={exporting !== null}
              onClick={() => handleExport(fmt)}
            >
              <Download className="w-3 h-3 mr-1" />
              {exporting === fmt ? '…' : fmt.toUpperCase()}
            </Button>
          ))}
        </div>
      </div>

      <Tabs defaultValue="document" className="flex-1 flex flex-col min-h-0">
        <TabsList className="mx-4 mt-2 grid grid-cols-2 h-8">
          <TabsTrigger value="document" className="text-xs">Document</TabsTrigger>
          <TabsTrigger value="bibliography" className="text-xs">
            <BookMarked className="w-3 h-3 mr-1" />
            References ({document.citations.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="document" className="flex-1 min-h-0 mt-1">
          <ScrollArea className="h-full px-4 pb-4">
            <article className="prose-document py-4">
              {document.content.split('\n\n').map((para, i) => {
                if (para.startsWith('# ')) return <h1 key={i}>{para.slice(2)}</h1>
                if (para.startsWith('## ')) return <h2 key={i}>{para.slice(3)}</h2>
                if (para.startsWith('### ')) return <h3 key={i}>{para.slice(4)}</h3>
                if (para.startsWith('|')) {
                  const rows = para.split('\n').filter(Boolean)
                  return (
                    <table key={i}>
                      <thead>
                        <tr>{rows[0]?.split('|').filter(Boolean).map((c, j) => <th key={j}>{c.trim()}</th>)}</tr>
                      </thead>
                      <tbody>
                        {rows.slice(2).map((row, ri) => (
                          <tr key={ri}>
                            {row.split('|').filter(Boolean).map((c, j) => <td key={j}>{c.trim()}</td>)}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )
                }
                return <p key={i}>{para}</p>
              })}
            </article>
          </ScrollArea>
        </TabsContent>

        <TabsContent value="bibliography" className="flex-1 min-h-0 mt-1">
          <ScrollArea className="h-full px-4 pb-4">
            <ol className="py-4 space-y-3">
              {document.citations.map((cite, i) => (
                <li key={i} className="text-xs text-muted-foreground leading-relaxed">
                  <span className="text-primary font-medium mr-1">[{i + 1}]</span>
                  {cite}
                </li>
              ))}
              {document.citations.length === 0 && (
                <p className="text-xs text-muted-foreground text-center py-8">No references yet</p>
              )}
            </ol>
          </ScrollArea>
        </TabsContent>
      </Tabs>
    </aside>
  )
}
