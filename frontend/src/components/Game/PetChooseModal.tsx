import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from 'react-query'
import { useAppStore } from '../../store'
import api from '../../utils/api'

export default function PetChooseModal() {
  const { user, token, setUser, lang } = useAppStore()
  const qc = useQueryClient()
  const [selected, setSelected] = useState<'cat' | 'dog' | null>(null)
  const [done, setDone] = useState(false)

  const { data: petData } = useQuery(
    'pet',
    () => api.get('/pets/me').then((r) => r.data),
    { enabled: !!token, staleTime: 10000 }
  )

  const chooseMutation = useMutation(
    (pet_type: string) => api.post('/pets/choose', { pet_type }),
    {
      onSuccess: () => {
        qc.invalidateQueries('pet')
        api.get('/wallet/profile').then((r) => setUser(r.data))
        setDone(true)
      },
    }
  )

  // Show only if: logged in, user loaded, has no pet chosen
  if (!token || !user || user.has_chosen_pet || done) return null
  if (petData?.has_pet) return null

  const isRu = lang === 'ru'

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <div className="card p-6 w-full max-w-sm space-y-5 animate-fade-in">
        <div className="text-center">
          <div className="text-5xl mb-3">🐾</div>
          <h2 className="text-xl font-black text-df-text">
            {isRu ? 'Выбери питомца' : 'Choose your pet'}
          </h2>
          <p className="text-df-muted text-sm mt-1">
            {isRu
              ? 'Он будет жить в твоей квартире. Ухаживай за ним!'
              : 'They will live in your apartment. Take care of them!'}
          </p>
        </div>

        <div className="grid grid-cols-2 gap-3">
          {(['cat', 'dog'] as const).map((type) => (
            <button
              key={type}
              onClick={() => setSelected(type)}
              className={`card p-4 flex flex-col items-center gap-2 transition-all border-2 ${
                selected === type ? 'border-df-accent' : 'border-transparent'
              }`}
            >
              <span className="text-4xl">{type === 'cat' ? '🐱' : '🐶'}</span>
              <span className="text-df-text font-bold text-sm">
                {isRu ? (type === 'cat' ? 'Кошка' : 'Собака') : (type === 'cat' ? 'Cat' : 'Dog')}
              </span>
            </button>
          ))}
        </div>

        {chooseMutation.isError && (
          <p className="text-df-red text-sm text-center">
            {(chooseMutation.error as any)?.response?.data?.detail || 'Ошибка'}
          </p>
        )}

        <button
          onClick={() => selected && chooseMutation.mutate(selected)}
          disabled={!selected || chooseMutation.isLoading}
          className="w-full btn-primary py-3 rounded-xl font-bold disabled:opacity-50"
        >
          {chooseMutation.isLoading
            ? (isRu ? 'Создаём...' : 'Creating...')
            : (isRu ? 'Выбрать!' : 'Choose!')}
        </button>
      </div>
    </div>
  )
}
