import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { useAppStore } from '../../store'
import api from '../../utils/api'
import WalletConnect from './WalletConnect'

export default function ProfilePage() {
  const { lang, theme, toggleTheme, toggleLang } = useAppStore()
  const isRu = lang === 'ru'
  const qc = useQueryClient()

  const { data: profile, isLoading } = useQuery(
    'profile',
    () => api.get('/wallet/profile').then((r) => r.data),
    { staleTime: 30000 }
  )

  const { data: txs } = useQuery(
    'transactions',
    () => api.get('/wallet/transactions').then((r) => r.data),
    { staleTime: 60000 }
  )

  const [copied, setCopied] = useState(false)

  const copyRef = async (text: string) => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  if (isLoading) return <div className="p-4 text-df-muted text-center">
    {isRu ? 'Загрузка...' : 'Loading...'}
  </div>

  return (
    <div className="p-4 space-y-4 animate-fade-in">
      <div className="pt-2 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-df-text">
            {isRu ? 'Профиль' : 'Profile'}
          </h1>
          <p className="text-df-muted text-sm">@{profile?.username || '—'}</p>
        </div>

        {/* Theme & lang toggles */}
        <div className="flex gap-2">
          <button
            onClick={toggleTheme}
            className="w-9 h-9 bg-df-surface rounded-xl flex items-center justify-center text-lg"
            title={theme === 'dark' ? (isRu ? 'Светлая тема' : 'Light mode') : (isRu ? 'Тёмная тема' : 'Dark mode')}
          >
            {theme === 'dark' ? '☀️' : '🌙'}
          </button>
          <button
            onClick={toggleLang}
            className="px-2 h-9 bg-df-surface rounded-xl flex items-center justify-center text-xs font-bold text-df-muted"
          >
            {lang === 'ru' ? 'EN' : 'RU'}
          </button>
        </div>
      </div>

      {/* Balance */}
      <div className="card p-4 text-center space-y-1">
        <p className="text-df-muted text-sm">{isRu ? 'Баланс' : 'Balance'}</p>
        <p className="text-3xl font-black text-df-gold">{profile?.balance || '0'} <span className="text-lg">$DF</span></p>
      </div>

      {/* Wallet Connect */}
      <WalletConnect />

      {/* Referral */}
      <div className="card p-4 space-y-3">
        <h3 className="font-bold text-df-text">👥 {isRu ? 'Реферальная программа' : 'Referral program'}</h3>

        <div className="bg-df-surface rounded-xl p-3 space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-df-muted text-sm">{isRu ? 'Мой реф-код' : 'My ref code'}</span>
            <span className="font-mono font-bold text-df-accent">{profile?.ref_code || '—'}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-df-muted text-sm">{isRu ? 'Рефералов' : 'Referrals'}</span>
            <span className="font-bold text-df-text">{profile?.ref_count || 0}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-df-muted text-sm">{isRu ? 'Заработано' : 'Earned'}</span>
            <span className="font-bold text-df-green">{profile?.ref_earnings || '0'} $DF</span>
          </div>
        </div>

        {profile?.ref_link && (
          <button
            onClick={() => copyRef(profile.ref_link)}
            className="w-full bg-df-surface text-df-muted text-xs rounded-xl py-2 px-3 text-left truncate hover:text-df-text transition-colors"
          >
            {copied ? (isRu ? '✅ Скопировано!' : '✅ Copied!') : `🔗 ${profile.ref_link}`}
          </button>
        )}
      </div>

      {/* Tx history */}
      {txs?.transactions?.length > 0 && (
        <div className="card p-4 space-y-2">
          <h3 className="font-bold text-df-text">📜 {isRu ? 'История' : 'History'}</h3>
          {txs.transactions.slice(0, 10).map((tx: any) => (
            <div key={tx.id} className="flex justify-between items-center py-1.5 border-b border-df-border last:border-0">
              <div>
                <p className="text-df-text text-sm font-semibold">{tx.tx_type}</p>
                <p className="text-df-muted text-xs">{new Date(tx.created_at).toLocaleDateString()}</p>
              </div>
              <span className={`font-bold text-sm ${
                ['deposit', 'admin_add', 'referral_bonus'].includes(tx.tx_type)
                  ? 'text-df-green'
                  : 'text-df-red'
              }`}>
                {['deposit', 'admin_add', 'referral_bonus'].includes(tx.tx_type) ? '+' : '-'}{tx.amount} $DF
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
