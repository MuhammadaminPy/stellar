import { useState, useEffect } from 'react'
import { useAppStore } from '../store'
import api from '../utils/api'

export default function RefCodeGate() {
  const { user, token, lang } = useAppStore()
  const [code, setCode] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [show, setShow] = useState(false)

  useEffect(() => {
    // Показываем только если пользователь ещё не активировал реф код
    // Если уже активирован — никогда не показываем снова
    if (user && token && !user.ref_code_used) {
      // Проверяем, не закрыл ли пользователь в этой сессии
      const dismissed = sessionStorage.getItem('ref_code_dismissed')
      if (!dismissed) {
        setShow(true)
      }
    } else {
      setShow(false)
    }
  }, [user, token])

  if (!show) return null

  const handleSkip = () => {
    // Сохраняем в сессии — в этот раз пользователь пропустил
    // При следующем открытии мини-апп предложение появится снова
    sessionStorage.setItem('ref_code_dismissed', '1')
    setShow(false)
  }

  const handleSubmit = async () => {
    if (!code.trim() || code.trim().length < 6) return
    setLoading(true)
    setError('')
    try {
      await api.post('/wallet/activate_ref', { ref_code: code.trim().toUpperCase() })
      // Обновляем данные пользователя
      const r = await api.get('/wallet/profile')
      useAppStore.getState().setUser(r.data)
      // ref_code_used теперь true — модал больше никогда не появится
      setShow(false)
    } catch (e: any) {
      setError(e.response?.data?.detail || (lang === 'ru' ? 'Неверный код' : 'Invalid code'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <div className="card p-6 w-full max-w-sm space-y-4 animate-fade-in">
        {/* Кнопка закрытия */}
        <div className="flex justify-end">
          <button
            onClick={handleSkip}
            className="text-df-muted hover:text-df-text transition-colors text-xl leading-none"
            aria-label="Закрыть"
          >
            ✕
          </button>
        </div>

        <div className="text-center">
          <div className="text-4xl mb-3">🔑</div>
          <h2 className="text-xl font-black text-df-text">
            {lang === 'ru' ? 'Есть реф код?' : 'Have a referral code?'}
          </h2>
          <p className="text-df-muted text-sm mt-1">
            {lang === 'ru'
              ? 'Если друг дал тебе код — введи его. Это необязательно, но связывает вас как рефералов навсегда.'
              : 'If a friend gave you a code, enter it. Optional, but links you as referrals permanently.'}
          </p>
        </div>

        <input
          type="text"
          value={code}
          onChange={(e) => setCode(e.target.value.toUpperCase())}
          placeholder={lang === 'ru' ? 'Реф код (8 символов)' : 'Ref code (8 chars)'}
          maxLength={10}
          className="w-full bg-df-surface border border-df-border rounded-xl px-4 py-3 text-df-text text-center text-lg font-mono tracking-widest focus:outline-none focus:border-df-accent"
          onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
        />

        {error && <p className="text-df-red text-sm text-center">{error}</p>}

        <button
          onClick={handleSubmit}
          disabled={loading || code.trim().length < 6}
          className="w-full btn-primary py-3 rounded-xl font-bold disabled:opacity-50"
        >
          {loading
            ? (lang === 'ru' ? 'Проверяем...' : 'Checking...')
            : (lang === 'ru' ? 'Активировать' : 'Activate')}
        </button>

        <button
          onClick={handleSkip}
          className="w-full text-df-muted text-sm py-2 hover:text-df-text transition-colors"
        >
          {lang === 'ru' ? 'Пропустить — введу позже' : 'Skip — I\'ll enter later'}
        </button>

        <p className="text-df-muted text-xs text-center">
          {lang === 'ru'
            ? '⚠️ Реф код можно ввести только один раз и изменить его нельзя'
            : '⚠️ The referral code can only be entered once and cannot be changed'}
        </p>
      </div>
    </div>
  )
}

