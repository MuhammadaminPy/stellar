import { useMutation, useQuery, useQueryClient } from 'react-query'
import { useAppStore } from '../../store'
import api from '../../utils/api'
import { useEffect, useState } from 'react'

function useCountdown(targetIso: string | null): string {
  const [remaining, setRemaining] = useState('')
  useEffect(() => {
    if (!targetIso) return
    const update = () => {
      const diff = new Date(targetIso).getTime() - Date.now()
      if (diff <= 0) { setRemaining(''); return }
      const h = Math.floor(diff / 3600000)
      const m = Math.floor((diff % 3600000) / 60000)
      const s = Math.floor((diff % 60000) / 1000)
      setRemaining(h > 0 ? `${h}ч ${m}м` : `${m}м ${s}с`)
    }
    update()
    const id = setInterval(update, 1000)
    return () => clearInterval(id)
  }, [targetIso])
  return remaining
}

export default function PetPanel() {
  const { lang } = useAppStore()
  const qc = useQueryClient()
  const isRu = lang === 'ru'

  const { data, isLoading, refetch } = useQuery(
    'pet',
    () => api.get('/pets/me').then((r) => r.data),
    { refetchInterval: 30000 }
  )

  const feedMutation = useMutation(() => api.post('/pets/feed'), {
    onSuccess: () => { qc.invalidateQueries('pet'); qc.invalidateQueries('profile') },
  })
  const feedBulkMutation = useMutation(() => api.post('/pets/feed_bulk'), {
    onSuccess: () => { qc.invalidateQueries('pet'); qc.invalidateQueries('profile') },
  })
  const petMutation = useMutation(() => api.post('/pets/pet'), {
    onSuccess: () => { qc.invalidateQueries('pet') },
  })

  const feedCountdown = useCountdown(data?.pet?.next_feed_at ?? null)
  const petCountdown = useCountdown(data?.pet?.next_pet_at ?? null)

  if (isLoading) return <div className="p-4 text-df-muted text-center">{isRu ? 'Загрузка...' : 'Loading...'}</div>

  const pet = data?.pet
  if (!pet) return (
    <div className="p-4 text-center text-df-muted">
      {isRu ? 'Питомец не найден' : 'No pet found'}
    </div>
  )

  const petEmoji = pet.pet_type === 'cat' ? '🐱' : '🐶'
  const petName = isRu
    ? (pet.pet_type === 'cat' ? 'Кошка' : 'Собака')
    : (pet.pet_type === 'cat' ? 'Cat' : 'Dog')
  const xpPercent = pet.xp_for_next > 0 ? Math.floor((pet.xp / pet.xp_for_next) * 100) : 0

  if (!pet.is_alive) {
    return (
      <div className="p-4 space-y-4 animate-fade-in">
        <div className="card p-6 text-center space-y-3">
          <div className="text-5xl opacity-40">💀</div>
          <h2 className="text-xl font-black text-df-red">
            {isRu ? 'Питомец погиб 😢' : 'Your pet died 😢'}
          </h2>
          <p className="text-df-muted text-sm">
            {isRu
              ? 'Вы забыли покормить или погладить питомца 2 раза подряд'
              : 'You forgot to feed or pet your companion 2 times in a row'}
          </p>
          <p className="text-df-muted text-xs">
            {isRu
              ? 'Ваш опыт сброшен. Свяжитесь с поддержкой для перезапуска питомца.'
              : 'Your XP was reset. Contact support to restart your pet.'}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-4 space-y-4 animate-fade-in">
      {/* Pet card */}
      <div className="card p-5 text-center space-y-3">
        <div className="text-6xl">{petEmoji}</div>
        <div>
          <h2 className="text-xl font-black text-df-text">{petName}</h2>
          <p className="text-df-muted text-sm">
            {isRu ? 'Уровень' : 'Level'} {pet.level}
          </p>
        </div>

        {/* XP bar */}
        <div className="space-y-1">
          <div className="flex justify-between text-xs text-df-muted">
            <span>XP: {pet.xp} / {pet.xp_for_next}</span>
            <span>{xpPercent}%</span>
          </div>
          <div className="h-2 bg-df-surface rounded-full overflow-hidden">
            <div
              className="h-full bg-df-accent rounded-full transition-all"
              style={{ width: `${xpPercent}%` }}
            />
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-2 text-xs text-df-muted pt-1">
          <div className="bg-df-surface rounded-lg p-2">
            🍖 {isRu ? 'Покормлен' : 'Fed'}: <b className="text-df-text">{pet.total_feeds}</b>
          </div>
          <div className="bg-df-surface rounded-lg p-2">
            🤝 {isRu ? 'Поглажен' : 'Petted'}: <b className="text-df-text">{pet.total_pets}</b>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="space-y-3">
        {/* Feed */}
        <div className="card p-4 space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-df-text font-bold">
              🍖 {isRu ? 'Покормить' : 'Feed'}
            </span>
            <span className="text-df-gold font-bold text-sm">{pet.feed_price} $DF</span>
          </div>

          {pet.can_feed ? (
            <button
              onClick={() => feedMutation.mutate()}
              disabled={feedMutation.isLoading}
              className="w-full btn-primary py-2 rounded-xl text-sm font-bold disabled:opacity-50"
            >
              {feedMutation.isLoading
                ? (isRu ? 'Кормим...' : 'Feeding...')
                : (isRu ? 'Покормить' : 'Feed now')}
            </button>
          ) : (
            <div className="text-center text-df-muted text-sm py-1">
              ⏰ {isRu ? 'Следующий корм через' : 'Next feed in'}: <b>{feedCountdown}</b>
            </div>
          )}

          {feedMutation.isError && (
            <p className="text-df-red text-xs text-center">
              {(feedMutation.error as any)?.response?.data?.detail}
            </p>
          )}
        </div>

        {/* Bulk feed */}
        <div className="card p-4 space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-df-text font-bold text-sm">
              📦 {isRu ? `Корм на ${pet.feed_bulk_hours} ч.` : `Food for ${pet.feed_bulk_hours}h`}
            </span>
            <span className="text-df-gold font-bold text-sm">{pet.feed_bulk_price} $DF</span>
          </div>
          <button
            onClick={() => feedBulkMutation.mutate()}
            disabled={feedBulkMutation.isLoading}
            className="w-full bg-df-gold/10 text-df-gold border border-df-gold/30 py-2 rounded-xl text-sm font-bold disabled:opacity-50 hover:bg-df-gold/20 transition-colors"
          >
            {feedBulkMutation.isLoading
              ? (isRu ? 'Покупаем...' : 'Buying...')
              : (isRu ? 'Купить корм со скидкой' : 'Buy bulk food')}
          </button>
          {feedBulkMutation.isError && (
            <p className="text-df-red text-xs text-center">
              {(feedBulkMutation.error as any)?.response?.data?.detail}
            </p>
          )}
        </div>

        {/* Pet action */}
        <div className="card p-4 space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-df-text font-bold">
              🤝 {isRu ? 'Погладить' : 'Pet'}{' '}
              <span className="text-df-green text-xs font-normal">
                {isRu ? '(бесплатно)' : '(free)'}
              </span>
            </span>
          </div>

          {pet.can_pet ? (
            <button
              onClick={() => petMutation.mutate()}
              disabled={petMutation.isLoading}
              className="w-full bg-df-green/10 text-df-green border border-df-green/30 py-2 rounded-xl text-sm font-bold disabled:opacity-50 hover:bg-df-green/20 transition-colors"
            >
              {petMutation.isLoading
                ? (isRu ? 'Гладим...' : 'Petting...')
                : (isRu ? 'Погладить' : 'Pet now')}
            </button>
          ) : (
            <div className="text-center text-df-muted text-sm py-1">
              ⏰ {isRu ? 'Следующее через' : 'Next in'}: <b>{petCountdown}</b>
            </div>
          )}

          {petMutation.isSuccess && (
            <p className="text-df-green text-xs text-center">
              ✅ +5 XP!
            </p>
          )}
        </div>
      </div>

      {/* Info box */}
      <div className="bg-df-surface rounded-xl p-3 text-xs text-df-muted space-y-1">
        <p>⚠️ {isRu
          ? `Пропустишь 2 раза корм или поглаживание — питомец погибнет!`
          : `Miss feeding or petting 2 times in a row — your pet will die!`}</p>
      </div>
    </div>
  )
}
