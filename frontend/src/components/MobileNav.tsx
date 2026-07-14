import { MessageSquare, FileText, Bookmark, Moon, Sun } from 'lucide-react'
import { cn } from '@/lib/utils'

interface MobileNavProps {
  active: 'chat' | 'document' | 'saved'
  onChange: (tab: 'chat' | 'document' | 'saved') => void
  dark: boolean
  onToggleTheme: () => void
}

export function MobileNav({ active, onChange, dark, onToggleTheme }: MobileNavProps) {
  const tabs = [
    { id: 'chat' as const, label: 'Chat', icon: MessageSquare },
    { id: 'document' as const, label: 'Document', icon: FileText },
    { id: 'saved' as const, label: 'Saved', icon: Bookmark },
  ]

  return (
    <nav className="lg:hidden fixed bottom-0 inset-x-0 bg-card border-t border-border z-50">
      <div className="flex items-center justify-around py-2">
        {tabs.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => onChange(id)}
            className={cn(
              'flex flex-col items-center gap-0.5 px-4 py-1 text-[10px] transition-colors',
              active === id ? 'text-primary' : 'text-muted-foreground'
            )}
          >
            <Icon className="w-5 h-5" />
            {label}
          </button>
        ))}
        <button
          onClick={onToggleTheme}
          className="flex flex-col items-center gap-0.5 px-4 py-1 text-[10px] text-muted-foreground"
        >
          {dark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
          Theme
        </button>
      </div>
    </nav>
  )
}
