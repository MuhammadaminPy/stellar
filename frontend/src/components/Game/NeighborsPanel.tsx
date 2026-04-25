import { useState } from 'react'
import { useQuery } from 'react-query'
import { useAppStore } from '../../store'
import api from '../../utils/api'

type SortMode = 'likes' | 'pet_level'

export default function NeighborsPanel() {
  const { lang } = useAppStore()
  const isRu = lang === 'ru'
  const [sort, setSort] = useState<SortMode>('likes')
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery(
    ['neighbors', sort, page],
    () => api.get(`/neighbors?sort_by=${sort}&page=${page}`).then((r) => r.data),
    { keepPreviousData: true, staleTime: 30000 }
  )

  const neighbors = data?.rooms || []
  const total = data?.total || 0

  return (
    <div className="p-4 space-y-3 animate-fade-in">
      {/* Sort filter */}
      <div className="flex gap-2">
        <button
          onClick={() => { setSort('likes'); setPage(1) }}
          className={`flex-1 py-2 rounded-xl text-sm font-bold transition-colors ${
            sort === 'likes' ? 'bg-df-accent text-white' : 'bg-df-surface text-df-muted'
          }`}
        >
          ❤️ {isRu ? 'По лайкам' : 'By likes'}
        </button>
        <button
          onClick={() => { setSort('pet_level'); setPage(1) }}
          className={`flex-1 py-2 rounded-xl text-sm font-bold transition-colors ${
            sort === 'pet_level' ? 'bg-df-accent text-white' : 'bg-df-surface text-df-muted'
          }`}
        >
          🐾 {isRu ? 'По питомцу' : 'By pet'}
        </button>
      </div>

      {isLoading && (
        <div className="text-center text-df-muted py-8">{isRu ? 'Загрузка...' : 'Loading...'}</div>
      )}

      {!isLoading && neighbors.length === 0 && (
        <div className="text-center text-df-muted py-8">
          {isRu ? 'Соседей пока нет' : 'No neighbors yet'}
        </div>
      )}

      {neighbors.map((n: any) => (
        <div key={n.room_id} className="card p-4 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-2xl">{n.pet_emoji || '🏠'}</span>
              <div>
                <p className="text-df-text font-bold text-sm">{n.owner_name || 'Игрок'}</p>
                {n.pet_level != null && (
                  <p className="text-df-muted text-xs">
                    🐾 {isRu ? 'Уровень питомца' : 'Pet level'}: <b className="text-df-accent">{n.pet_level}</b>
                  </p>
                )}
              </div>
            </div>
            <div className="text-center">
              <p className="text-df-gold font-bold">{n.likes_count}</p>
              <p className="text-df-muted text-xs">❤️</p>
            </div>
          </div>
        </div>
      ))}

      {/* Pagination */}
      {total > 10 && (
        <div className="flex justify-center gap-3 pt-2">
          <button
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
            className="px-4 py-2 bg-df-surface text-df-muted rounded-xl text-sm disabled:opacity-40"
          >
            ← {isRu ? 'Назад' : 'Prev'}
          </button>
          <span className="text-df-muted text-sm py-2">{page}</span>
          <button
            disabled={neighbors.length < 10}
            onClick={() => setPage((p) => p + 1)}
            className="px-4 py-2 bg-df-surface text-df-muted rounded-xl text-sm disabled:opacity-40"
          >
            {isRu ? 'Далее' : 'Next'} →
          </button>
        </div>
      )}
    </div>
  )
}
