import { useState, useEffect } from 'react'
import { AnimatePresence } from 'framer-motion'
import { Moon, Sun, PanelLeftClose, PanelLeft, Settings, X } from 'lucide-react'
import ChatContainer from './components/Chat/ChatContainer'
import Sidebar from './components/Layout/Sidebar'

function App() {
  const [darkMode, setDarkMode] = useState(true)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [settingsOpen, setSettingsOpen] = useState(false)

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [darkMode])

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)] transition-colors duration-200">
      <div className="flex h-screen">
        {/* Sidebar */}
        <AnimatePresence>
          {sidebarOpen && (
            <div
              className="h-full overflow-hidden flex-shrink-0"
              style={{ width: 260 }}
            >
              <Sidebar
                currentSessionId={currentSessionId}
                onSessionSelect={setCurrentSessionId}
                onNewSession={() => setCurrentSessionId(null)}
                onClose={() => setSidebarOpen(false)}
              />
            </div>
          )}
        </AnimatePresence>

        {/* Main Content */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Header - minimal */}
          <header className="h-12 px-3 flex items-center justify-between border-b border-[var(--border-subtle)]">
            <div className="flex items-center gap-2">
              {!sidebarOpen && (
                <button
                  onClick={() => setSidebarOpen(true)}
                  className="p-2 rounded-lg hover:bg-[var(--bg-hover)] transition-colors"
                  title="Open sidebar"
                >
                  <PanelLeft size={18} className="text-[var(--text-secondary)]" />
                </button>
              )}
              <span className="text-sm font-semibold text-[var(--text-secondary)] tracking-wide">ODAOS</span>
            </div>

            <div className="flex items-center gap-1">
              <button
                onClick={() => setDarkMode(!darkMode)}
                className="p-2 rounded-lg hover:bg-[var(--bg-hover)] transition-colors"
                title={darkMode ? 'Light mode' : 'Dark mode'}
              >
                {darkMode ? (
                  <Sun size={16} className="text-[var(--text-secondary)]" />
                ) : (
                  <Moon size={16} className="text-[var(--text-secondary)]" />
                )}
              </button>
              <button
                onClick={() => setSettingsOpen(true)}
                className="p-2 rounded-lg hover:bg-[var(--bg-hover)] transition-colors"
                title="Settings"
              >
                <Settings size={16} className="text-[var(--text-secondary)]" />
              </button>
            </div>
          </header>

          {/* Chat Area */}
          <main className="flex-1 overflow-hidden">
            <ChatContainer
              sessionId={currentSessionId}
              onSessionCreated={setCurrentSessionId}
            />
          </main>
        </div>
      </div>

      {/* Settings Modal */}
      <AnimatePresence>
        {settingsOpen && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
            onClick={() => setSettingsOpen(false)}
          >
            <div
              onClick={(e) => e.stopPropagation()}
              className="bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded-2xl p-6 w-full max-w-sm mx-4 shadow-xl"
            >
              <div className="flex items-center justify-between mb-5">
                <h2 className="text-base font-semibold">Settings</h2>
                <button
                  onClick={() => setSettingsOpen(false)}
                  className="p-1.5 rounded-lg hover:bg-[var(--bg-hover)] transition-colors"
                >
                  <X size={16} className="text-[var(--text-secondary)]" />
                </button>
              </div>

              <div className="space-y-3">
                {/* Theme */}
                <div className="flex items-center justify-between p-3 rounded-xl bg-[var(--bg-secondary)]">
                  <span className="text-sm font-medium">Dark Mode</span>
                  <button
                    onClick={() => setDarkMode(!darkMode)}
                    className={`w-10 h-5 rounded-full transition-colors relative ${darkMode ? 'bg-[var(--accent-success)]' : 'bg-[var(--bg-tertiary)]'
                      }`}
                  >
                    <div
                      className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow-sm transition-transform ${darkMode ? 'translate-x-5' : 'translate-x-0.5'
                        }`}
                    />
                  </button>
                </div>

                {/* API Status */}
                <div className="p-3 rounded-xl bg-[var(--bg-secondary)]">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">API</span>
                    <span className="flex items-center gap-1.5 text-xs text-[var(--accent-success)]">
                      <span className="w-1.5 h-1.5 rounded-full bg-current" />
                      Connected
                    </span>
                  </div>
                  <p className="text-xs text-[var(--text-muted)] mt-1">
                    http://localhost:8000
                  </p>
                </div>

                {/* Version */}
                <div className="flex items-center justify-between p-3 rounded-xl bg-[var(--bg-secondary)]">
                  <span className="text-sm font-medium">Version</span>
                  <span className="text-xs text-[var(--text-muted)]">1.0.0</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default App
