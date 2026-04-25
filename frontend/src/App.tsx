import { useEffect, useCallback } from 'react'
import { QueryClient, QueryClientProvider } from 'react-query'
import { useAppStore } from './store'
import TabBar from './components/TabBar'
import GamesPage from './components/Game/GamesPage'
import ProfilePage from './components/Profile/ProfilePage'
import InfoPage from './components/Info/InfoPage'
import RefCodeGate from './components/RefCodeGate'
import PetChooseModal from './components/Game/PetChooseModal'

const qc = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 30000 } },
})

declare global {
  interface Window {
    Telegram?: { WebApp?: any }
  }
}

export default function App() {
  const { activeTab, setToken, token, setUser, theme, lang } = useAppStore()

  // Apply theme class to root
  useEffect(() => {
    const root = document.documentElement
    if (theme === 'light') {
      root.classList.add('theme-light')
      root.classList.remove('theme-dark')
    } else {
      root.classList.add('theme-dark')
      root.classList.remove('theme-light')
    }
  }, [theme])

  // Telegram WebApp auth — получаем JWT через Telegram initData
  const doAuth = useCallback(async () => {
    const tg = window.Telegram?.WebApp
    if (!tg) return

    tg.ready()
    tg.expand()

    const initData = tg.initData
    if (!initData) return

    try {
      const r = await fetch('/api/auth/telegram', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ init_data: initData }),
      })
      const data = await r.json()
      if (data.access_token) {
        setToken(data.access_token)
      }
    } catch {
      // Игнорируем сетевые ошибки при авторизации
    }
  }, [setToken])

  // Запускаем авторизацию при старте
  // Если токен уже есть — используем его; при 401 api.ts сбросит token → useEffect перезапустится
  useEffect(() => {
    const tg = window.Telegram?.WebApp

    if (!token) {
      // Нет токена — ждём initData и авторизуемся
      if (tg?.initData) {
        doAuth()
      } else {
        // initData ещё не готов — ждём немного и повторяем
        const timer = setTimeout(() => {
          const tg2 = window.Telegram?.WebApp
          if (tg2?.initData) {
            tg2.ready()
            doAuth()
          }
        }, 300)
        return () => clearTimeout(timer)
      }
    } else {
      // Токен есть — проверяем что он ещё валидный (загружаем профиль)
      fetch('/api/wallet/profile', {
        headers: { Authorization: `Bearer ${token}` },
      })
        .then((r) => {
          if (r.status === 401) {
            // Токен истёк — переавторизуемся
            setToken(null)
          } else {
            return r.json()
          }
        })
        .then((data) => { if (data) setUser(data) })
        .catch(() => {})
    }
  }, [token, doAuth, setToken, setUser])

  // Apply lang to html element
  useEffect(() => {
    document.documentElement.lang = lang
  }, [lang])

  const renderPage = () => {
    switch (activeTab) {
      case 'games': return <GamesPage />
      case 'profile': return <ProfilePage />
      case 'info': return <InfoPage />
      default: return <GamesPage />
    }
  }

  return (
    <QueryClientProvider client={qc}>
      <div className={`app-root min-h-screen pb-20 ${theme === 'light' ? 'theme-light' : 'theme-dark'}`}>
        <RefCodeGate />
        <PetChooseModal />
        {renderPage()}
        <TabBar />
      </div>
    </QueryClientProvider>
  )
}
