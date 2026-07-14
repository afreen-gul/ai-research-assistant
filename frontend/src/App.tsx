import { useState } from 'react'
import { Moon, Sun } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Sidebar } from '@/components/Sidebar'
import { ChatPanel } from '@/components/ChatPanel'
import { DocumentPanel } from '@/components/DocumentPanel'
import { MobileNav } from '@/components/MobileNav'
import { useSession, useSidebarData, useTheme } from '@/hooks/useApp'
import { useToast } from '@/components/ui/toast'

export default function App() {
  const { toast } = useToast()
  const { dark, toggle: toggleTheme } = useTheme()
  const sidebar = useSidebarData()
  const session = useSession(sidebar.refresh)
  const [mobileTab, setMobileTab] = useState<'chat' | 'document' | 'saved'>('chat')

  const handleUpload = async (file: File) => {
    try {
      const result = await session.uploadPDF(file)
      toast(`"${file.name}" uploaded and indexed.`, 'success')
      session.sendMessage(
        `I've uploaded a PDF (${file.name}). File ID: ${result.file_id}. ` +
        `Please extract and summarize its contents. Abstract: ${result.structured?.abstract?.slice(0, 200) || 'N/A'}`
      )
    } catch (err) {
      toast(err instanceof Error ? err.message : 'PDF upload failed.', 'error')
    }
  }

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      <header className="h-12 border-b border-border flex items-center justify-between px-4 shrink-0 lg:hidden">
        <span className="text-sm font-semibold">Research Assistant</span>
        <Button variant="ghost" size="icon" onClick={toggleTheme}>
          {dark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </Button>
      </header>

      <div className="flex-1 flex min-h-0 pb-14 lg:pb-0">
        <div className={`${mobileTab === 'saved' ? 'flex' : 'hidden'} lg:flex h-full w-full lg:w-auto`}>
          <Sidebar
            sessions={sidebar.sessions}
            notes={sidebar.notes}
            papers={sidebar.papers}
            searchHistory={sidebar.searchHistory}
            onNewSession={session.newSession}
            onAddNote={(title, content) => sidebar.addNote(title, content, session.sessionId ?? undefined)}
            activeSessionId={session.sessionId}
          />
        </div>

        <div className={`${mobileTab === 'chat' ? 'flex' : 'hidden'} lg:flex flex-1 min-w-0 h-full`}>
          <ChatPanel
            messages={session.messages}
            isLoading={session.isLoading}
            onSend={session.sendMessage}
            onUploadPDF={handleUpload}
            onSavePaper={sidebar.addPaper}
            citationStyle={session.citationStyle}
            onCitationStyleChange={session.setCitationStyle}
          />
        </div>

        <div className={`${mobileTab === 'document' ? 'flex' : 'hidden'} lg:flex h-full w-full lg:w-auto`}>
          <DocumentPanel document={session.document} />
        </div>

        <div className="hidden lg:flex absolute top-3 right-4">
          <Button variant="ghost" size="icon" onClick={toggleTheme}>
            {dark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </Button>
        </div>
      </div>

      <MobileNav active={mobileTab} onChange={setMobileTab} dark={dark} onToggleTheme={toggleTheme} />
    </div>
  )
}
