import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { useAppStore } from '../../store'
import api from '../../utils/api'
import WebApp from '@twa-dev/sdk'

const TYPES = [
  { id: '', label: 'Все' },
  { id: 'sofa', label: '🛋 Диван' },
  { id: 'window', label: '🪟 Окна' },
  { id: 'sill', label: '🪴 Подоконник' },
  { id: 'flowers', label: '🌸 Цветы' },
  { id: 'character', label: '👤 Персонаж' },
  { id: 'carpet', label: '🟫 Ковёр' },
  { id: 'wallpaper', label: '🖼 Обои' },
  { id: 'pet', label: '🐾 Питомец' },
]

const SORTS = [
  { id: 'id', label: 'По новизне' },
  { id: 'price_asc', label: 'Дешевле' },
  { id: 'price_desc', label: 'Дороже' },
]

export default function ShopPanel() {
  const { setGameScreen } = useAppStore()
  const [filterType, setFilterType] = useState('')
  const [sortBy, setSortBy] = useState('id')
  const [page, setPage] = useState(1)
  const [showFilters, setShowFilters] = useState(false)
  const qc = useQueryClient()

  const { data, isLoading } = useQuery(
    ['shop', filterType, sortBy, page],
    () => api.get('/shop/items', {
      params: { item_type: filterType || undefined, sort_by: sortBy, page },
    }).then((r: any) => r.data),
    { keepPreviousData: true }
  )

  const buy = useMutation(
    (item_id: number) => api.post('/shop/buy', { item_id }),
    {
      onSuccess: () => {
        qc.invalidateQueries('inventory')
        WebApp.HapticFeedback.notificationOccurred('success')
        WebApp.showAlert('✅ Куплено! Предмет в инвентаре.')
      },
    }
  )

  const handleBuy = (item: any) => {
    WebApp.showConfirm(`Купить "${item.name}" за ${item.price} $DF?`, (confirmed: boolean) => {
      if (confirmed) buy.mutate(item.id)
    })
  }

  const totalPages = data ? Math.ceil(data.total / 20) : 1

  return (
    <div className="flex flex-col animate-fade-in" style={{ minHeight: '100vh' }}>
      <div className="flex items-center justify-between px-4 pt-3 pb-2">
        <button onClick={() => setGameScreen('home')} className="text-df-muted active:text-df-text transition-colors">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} strokeLinecap="round">
            <path d="M15 18l-6-6 6-6" />
          </svg>
        </button>
        <h2 className="text-df-text font-black text-base">Магазин</h2>
        <button onClick={() => setShowFilters(!showFilters)} className="text-df-muted active:text-df-accent transition-colors">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round">
            <line x1="4" y1="6" x2="20" y2="6" /><line x1="8" y1="12" x2="16" y2="12" /><line x1="11" y1="18" x2="13" y2="18" />
          </svg>
        </button>
      </div>

      {showFilters && (
        <div className="px-4 pb-3 space-y-2 animate-fade-in">
          <div className="flex gap-2 overflow-x-auto pb-1 -mx-1 px-1">
            {TYPES.map((t) => (
              <button
                key={t.id}
                onClick={() => { setFilterType(t.id); setPage(1) }}
                className={`flex-shrink-0 px-3 py-1.5 rounded-full text-xs font-bold border transition-colors ${
                  filterType === t.id
                    ? 'bg-df-accent text-white border-df-accent'
                    : 'bg-df-surface text-df-muted border-df-border'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
          <div className="flex gap-2">
            {SORTS.map((s) => (
              <button
                key={s.id}
                onClick={() => setSortBy(s.id)}
                className={`flex-1 py-1.5 rounded-lg text-xs font-bold border transition-colors ${
                  sortBy === s.id
                    ? 'bg-df-accent/20 text-df-accent border-df-accent/40'
                    : 'bg-df-surface text-df-muted border-df-border'
                }`}
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="flex-1 px-4">
        {isLoading ? (
          <div className="grid grid-cols-2 gap-3">
            {Array(6).fill(0).map((_, i) => <div key={i} className="shimmer h-48" />)}
          </div>
        ) : data?.items?.length === 0 ? (
          <div className="text-center py-16 text-df-muted">
            <div className="text-4xl mb-3">🛒</div>
            <p className="font-semibold">Товаров нет</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-3">
            {data?.items?.map((item: any) => {
              const initialStock = item.initial_stock
              const remaining = item.stock
              const hasLimit = initialStock !== null && initialStock !== undefined
              const isSoldOut = item.stock === 0

              return (
                <div
                  key={item.id}
                  className={`card flex flex-col overflow-hidden ${isSoldOut ? 'opacity-60' : ''}`}
                >
                  <div className="relative bg-df-surface aspect-square flex items-center justify-center overflow-hidden">
                    {item.photo_url ? (
                      <img src={item.photo_url} alt={item.name} className="w-full h-full object-cover" />
                    ) : (
                      <span className="text-4xl">📦</span>
                    )}
                    {isSoldOut && (
                      <div className="absolute inset-0 flex items-center justify-center bg-df-bg/70">
                        <span className="text-xs font-black text-df-muted rotate-[-20deg] border-2 border-df-muted rounded px-1">
                          ПРОДАНО
                        </span>
                      </div>
                    )}
                    {hasLimit && !isSoldOut && remaining <= 5 && (
                      <span className="absolute top-1.5 right-1.5 badge-red">
                        {remaining} шт
                      </span>
                    )}
                  </div>
                  <div className="p-2.5 flex flex-col gap-1">
                    <p className="text-df-text text-xs font-bold leading-tight line-clamp-2">{item.name}</p>

                    {/* Счётчик остатка */}
                    {hasLimit && (
                      <div className="flex items-center gap-1.5">
                        <div className="flex-1 h-1 rounded-full bg-df-border overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all ${isSoldOut ? 'bg-df-muted' : remaining <= 5 ? 'bg-df-red' : 'bg-df-green'}`}
                            style={{ width: `${Math.max(0, (remaining / initialStock) * 100)}%` }}
                          />
                        </div>
                        <span className={`text-[10px] font-bold flex-shrink-0 ${isSoldOut ? 'text-df-muted' : remaining <= 5 ? 'text-df-red' : 'text-df-muted'}`}>
                          {remaining}/{initialStock}
                        </span>
                      </div>
                    )}

                    <div className="flex items-center justify-between mt-auto">
                      <span className="text-df-gold font-black text-sm">{item.price} $DF</span>
                      <button
                        onClick={() => handleBuy(item)}
                        disabled={isSoldOut || buy.isLoading}
                        className="bg-df-accent/20 text-df-accent text-xs font-bold px-2.5 py-1 rounded-lg active:scale-95 transition-transform disabled:opacity-40"
                      >
                        Купить
                      </button>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-3 py-4">
            <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1} className="btn-secondary py-2 px-4 text-sm disabled:opacity-40">←</button>
            <span className="text-df-muted text-sm">{page} / {totalPages}</span>
            <button onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page === totalPages} className="btn-secondary py-2 px-4 text-sm disabled:opacity-40">→</button>
          </div>
        )}
      </div>
    </div>
  )
}