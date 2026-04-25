import { useMutation, useQuery, useQueryClient } from 'react-query'
import { useAppStore } from '../../store'
import api from '../../utils/api'

export default function InventoryPanel() {
  const { lang } = useAppStore()
  const qc = useQueryClient()
  const isRu = lang === 'ru'

  const { data, isLoading } = useQuery(
    'inventory',
    () => api.get('/shop/inventory').then((r) => r.data),
    { staleTime: 15000 }
  )

  const toggleMutation = useMutation(
    (inventory_id: number) => api.post('/shop/inventory/toggle', { inventory_id }),
    { onSuccess: () => qc.invalidateQueries('inventory') }
  )

  if (isLoading) return <div className="p-4 text-df-muted text-center">{isRu ? 'Загрузка...' : 'Loading...'}</div>

  const items = data?.inventory || []

  if (items.length === 0) {
    return (
      <div className="p-4 text-center space-y-2">
        <div className="text-4xl">🎒</div>
        <p className="text-df-muted">{isRu ? 'Инвентарь пуст' : 'Inventory is empty'}</p>
      </div>
    )
  }

  return (
    <div className="p-4 space-y-3">
      {items.map((inv: any) => (
        <div
          key={inv.id}
          className={`card p-3 flex items-center gap-3 ${inv.is_active ? 'border border-df-accent/40' : ''}`}
        >
          {/* Photo or emoji */}
          <div className="w-12 h-12 rounded-xl bg-df-surface flex items-center justify-center text-2xl shrink-0 overflow-hidden">
            {inv.item?.photo_url
              ? <img src={inv.item.photo_url} alt={inv.item.name} className="w-full h-full object-cover" />
              : '📦'}
          </div>

          {/* Info */}
          <div className="flex-1 min-w-0">
            <p className="text-df-text font-bold text-sm truncate">{inv.item?.name || '?'}</p>
            <p className="text-df-muted text-xs">
              {isRu ? 'Тип' : 'Type'}: {inv.item?.type || '—'}
            </p>
            {/* Serial UID */}
            {inv.serial_uid && (
              <p className="text-df-accent text-xs font-mono mt-0.5">
                ID: {inv.serial_uid}
              </p>
            )}
          </div>

          {/* Toggle button */}
          <button
            onClick={() => toggleMutation.mutate(inv.id)}
            disabled={toggleMutation.isLoading}
            className={`shrink-0 px-3 py-1.5 rounded-lg text-xs font-bold transition-colors ${
              inv.is_active
                ? 'bg-df-accent/20 text-df-accent'
                : 'bg-df-surface text-df-muted hover:text-df-text'
            }`}
          >
            {inv.is_active
              ? (isRu ? 'Убрать' : 'Remove')
              : (isRu ? 'Поставить' : 'Place')}
          </button>
        </div>
      ))}
    </div>
  )
}
