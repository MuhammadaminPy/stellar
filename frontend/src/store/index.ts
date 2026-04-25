import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type Language = 'ru' | 'en'
export type Theme = 'dark' | 'light'
export type GameScreen = 'home' | 'inventory' | 'shop' | 'neighbors' | 'pet'

interface AppStore {
  // Navigation
  activeTab: string
  setActiveTab: (tab: string) => void
  gameScreen: GameScreen
  setGameScreen: (screen: GameScreen) => void

  // Auth
  token: string | null
  setToken: (t: string | null) => void

  // User
  user: any
  setUser: (u: any) => void

  // Theme
  theme: Theme
  setTheme: (t: Theme) => void
  toggleTheme: () => void

  // Language
  lang: Language
  setLang: (l: Language) => void
  toggleLang: () => void

  // Room edit mode
  roomEditMode: boolean
  setRoomEditMode: (v: boolean) => void
}

export const useAppStore = create<AppStore>()(
  persist(
    (set, get) => ({
      activeTab: 'games',
      setActiveTab: (tab) => set({ activeTab: tab }),

      gameScreen: 'home',
      setGameScreen: (screen) => set({ gameScreen: screen }),

      token: null,
      setToken: (t) => set({ token: t }),

      user: null,
      setUser: (u) => set({ user: u }),

      theme: 'dark',
      setTheme: (t) => set({ theme: t }),
      toggleTheme: () => set((s) => ({ theme: s.theme === 'dark' ? 'light' : 'dark' })),

      lang: 'ru',
      setLang: (l) => set({ lang: l }),
      toggleLang: () => set((s) => ({ lang: s.lang === 'ru' ? 'en' : 'ru' })),

      roomEditMode: false,
      setRoomEditMode: (v) => set({ roomEditMode: v }),
    }),
    {
      name: 'df-app-store',
      partialize: (state) => ({
        token: state.token,
        theme: state.theme,
        lang: state.lang,
      }),
    }
  )
)
