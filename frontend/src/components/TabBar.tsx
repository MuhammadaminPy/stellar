import { useAppStore } from '../store'

const tabsRu = [
  { id: 'games', label: 'Игры', emoji: '🎮' },
  { id: 'profile', label: 'Профиль', emoji: '👤' },
  { id: 'info', label: 'Инфо', emoji: '📊' },
]

const tabsEn = [
  { id: 'games', label: 'Games', emoji: '🎮' },
  { id: 'profile', label: 'Profile', emoji: '👤' },
  { id: 'info', label: 'Info', emoji: '📊' },
]

export default function TabBar() {
  const { activeTab, setActiveTab, lang } = useAppStore()
  const tabs = lang === 'ru' ? tabsRu : tabsEn

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 tab-bar-bg border-t border-df-border safe-area-bottom">
      <div className="flex">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 flex flex-col items-center gap-1 py-3 transition-all ${
              activeTab === tab.id
                ? 'text-df-accent'
                : 'text-df-muted hover:text-df-text'
            }`}
          >
            <span className="text-xl leading-none">{tab.emoji}</span>
            <span className="text-[10px] font-semibold">{tab.label}</span>
          </button>
        ))}
      </div>
    </nav>
  )
}
