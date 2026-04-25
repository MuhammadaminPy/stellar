import { useState, useRef, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { useAppStore } from '../../store'
import api from '../../utils/api'
import InventoryPanel from './InventoryPanel'
import ShopPanel from './ShopPanel'
import NeighborsPanel from './NeighborsPanel'
import PetPanel from './PetPanel'

// Default positions for items in the room
const DEFAULT_POSITIONS: Record<string, { x: number; y: number }> = {
  sofa: { x: 10, y: 45 },
  table: { x: 40, y: 55 },
  bed: { x: 65, y: 40 },
  plant: { x: 85, y: 55 },
  tv: { x: 10, y: 20 },
  lamp: { x: 80, y: 15 },
  cat: { x: 50, y: 60 },
  dog: { x: 50, y: 60 },
}

const ITEM_TYPE_EMOJI: Record<string, string> = {
  sofa: '🛋',
  table: '🪑',
  bed: '🛏',
  plant: '🪴',
  tv: '📺',
  lamp: '💡',
  cat: '🐱',
  dog: '🐶',
  decoration: '🖼',
  rug: '🪣',
}

function getRoomEmoji(item: any): string {
  const type = item?.item?.type || item?.pet_type || ''
  return ITEM_TYPE_EMOJI[type] || '📦'
}

interface DraggableItemProps {
  id: string
  emoji: string
  position: { x: number; y: number }
  editMode: boolean
  onMove: (id: string, x: number, y: number) => void
}

function DraggableItem({ id, emoji, position, editMode, onMove }: DraggableItemProps) {
  const ref = useRef<HTMLDivElement>(null)
  const dragging = useRef(false)
  const startPos = useRef({ mx: 0, my: 0, ix: 0, iy: 0 })
  const containerRef = useRef<Element | null>(null)

  const handleMouseDown = (e: React.MouseEvent) => {
    if (!editMode) return
    dragging.current = true
    containerRef.current = ref.current?.closest('.room-container') ?? null
    startPos.current = {
      mx: e.clientX,
      my: e.clientY,
      ix: position.x,
      iy: position.y,
    }
    e.preventDefault()
  }

  const handleTouchStart = (e: React.TouchEvent) => {
    if (!editMode) return
    const touch = e.touches[0]
    dragging.current = true
    containerRef.current = ref.current?.closest('.room-container') ?? null
    startPos.current = {
      mx: touch.clientX,
      my: touch.clientY,
      ix: position.x,
      iy: position.y,
    }
  }

  useEffect(() => {
    const handleDrag = (e: MouseEvent | TouchEvent) => {
      if (!dragging.current || !containerRef.current) return
      const container = containerRef.current.getBoundingClientRect()
      const clientX = e instanceof MouseEvent ? e.clientX : e.touches[0].clientX
      const clientY = e instanceof MouseEvent ? e.clientY : e.touches[0].clientY

      const dx = clientX - startPos.current.mx
      const dy = clientY - startPos.current.my

      const newX = Math.max(0, Math.min(90, startPos.current.ix + (dx / container.width) * 100))
      const newY = Math.max(0, Math.min(80, startPos.current.iy + (dy / container.height) * 100))

      onMove(id, newX, newY)
    }

    const handleDragEnd = () => { dragging.current = false }

    window.addEventListener('mousemove', handleDrag as any)
    window.addEventListener('mouseup', handleDragEnd)
    window.addEventListener('touchmove', handleDrag as any, { passive: false })
    window.addEventListener('touchend', handleDragEnd)
    return () => {
      window.removeEventListener('mousemove', handleDrag as any)
      window.removeEventListener('mouseup', handleDragEnd)
      window.removeEventListener('touchmove', handleDrag as any)
      window.removeEventListener('touchend', handleDragEnd)
    }
  }, [id, onMove])

  return (
    <div
      ref={ref}
      onMouseDown={handleMouseDown}
      onTouchStart={handleTouchStart}
      className={`absolute select-none transition-shadow ${
        editMode ? 'cursor-grab active:cursor-grabbing ring-2 ring-df-accent/60 rounded-lg' : ''
      }`}
      style={{
        left: `${position.x}%`,
        top: `${position.y}%`,
        transform: 'translate(-50%, -50%)',
        fontSize: '2rem',
        zIndex: editMode ? 10 : 1,
        touchAction: editMode ? 'none' : 'auto',
      }}
    >
      {emoji}
    </div>
  )
}

export default function HomeGame() {
  const { gameScreen, setGameScreen, roomEditMode, setRoomEditMode, lang } = useAppStore()
  const qc = useQueryClient()
  const isRu = lang === 'ru'

  const { data: inventoryData } = useQuery(
    'inventory',
    () => api.get('/shop/inventory').then((r) => r.data),
    { staleTime: 30000 }
  )

  const { data: petData } = useQuery(
    'pet',
    () => api.get('/pets/me').then((r) => r.data),
    { staleTime: 15000 }
  )

  const { data: positionsData } = useQuery(
    'roomPositions',
    () => api.get('/wallet/room/positions').then((r) => r.data),
    { staleTime: 60000 }
  )

  const savePositionsMutation = useMutation(
    (positions: Record<string, { x: number; y: number }>) =>
      api.post('/wallet/room/positions', { positions }),
    { onSuccess: () => qc.invalidateQueries('roomPositions') }
  )

  // Local positions state for edit mode
  const [localPositions, setLocalPositions] = useState<Record<string, { x: number; y: number }>>({})
  const [savedPositions, setSavedPositions] = useState<Record<string, { x: number; y: number }>>({})

  // Initialize positions from server or defaults
  useEffect(() => {
    const serverPos = positionsData?.positions || {}
    setSavedPositions(serverPos)
    setLocalPositions(serverPos)
  }, [positionsData])

  const getPosition = (key: string) => {
    const src = roomEditMode ? localPositions : savedPositions
    return src[key] || DEFAULT_POSITIONS[key] || { x: 50, y: 50 }
  }

  const handleItemMove = (id: string, x: number, y: number) => {
    setLocalPositions((prev) => ({ ...prev, [id]: { x, y } }))
  }

  const handleSave = () => {
    savePositionsMutation.mutate(localPositions)
    setSavedPositions(localPositions)
    setRoomEditMode(false)
  }

  const handleReset = () => {
    setLocalPositions(savedPositions)
    setRoomEditMode(false)
  }

  const handleEditStart = () => {
    setLocalPositions(savedPositions)
    setRoomEditMode(true)
  }

  // Collect items to show in room
  const activeItems = (inventoryData?.inventory || []).filter((inv: any) => inv.is_active)
  const hasPet = petData?.has_pet && petData?.pet?.is_alive

  // Sub-screens
  if (gameScreen === 'inventory') return (
    <div className="animate-fade-in">
      <div className="flex items-center gap-3 p-4 pt-6">
        <button onClick={() => setGameScreen('home')} className="text-df-muted hover:text-df-text">
          ← {isRu ? 'Назад' : 'Back'}
        </button>
        <h1 className="text-xl font-black text-df-text">
          {isRu ? 'Инвентарь' : 'Inventory'}
        </h1>
      </div>
      <InventoryPanel />
    </div>
  )

  if (gameScreen === 'shop') return (
    <div className="animate-fade-in">
      <div className="flex items-center gap-3 p-4 pt-6">
        <button onClick={() => setGameScreen('home')} className="text-df-muted hover:text-df-text">
          ← {isRu ? 'Назад' : 'Back'}
        </button>
        <h1 className="text-xl font-black text-df-text">
          {isRu ? 'Магазин' : 'Shop'}
        </h1>
      </div>
      <ShopPanel />
    </div>
  )

  if (gameScreen === 'neighbors') return (
    <div className="animate-fade-in">
      <div className="flex items-center gap-3 p-4 pt-6">
        <button onClick={() => setGameScreen('home')} className="text-df-muted hover:text-df-text">
          ← {isRu ? 'Назад' : 'Back'}
        </button>
        <h1 className="text-xl font-black text-df-text">
          {isRu ? 'Соседи' : 'Neighbors'}
        </h1>
      </div>
      <NeighborsPanel />
    </div>
  )

  if (gameScreen === 'pet') return (
    <div className="animate-fade-in">
      <div className="flex items-center gap-3 p-4 pt-6">
        <button onClick={() => setGameScreen('home')} className="text-df-muted hover:text-df-text">
          ← {isRu ? 'Назад' : 'Back'}
        </button>
        <h1 className="text-xl font-black text-df-text">
          {isRu ? 'Питомец' : 'Pet'}
        </h1>
      </div>
      <PetPanel />
    </div>
  )

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="p-4 pt-6 flex items-center justify-between">
        <h1 className="text-xl font-black text-df-text">🏠 {isRu ? 'Моя квартира' : 'My apartment'}</h1>
        {!roomEditMode ? (
          <button
            onClick={handleEditStart}
            className="text-xs bg-df-surface text-df-muted px-3 py-1.5 rounded-lg hover:text-df-text transition-colors"
          >
            ✏️ {isRu ? 'Изменить' : 'Edit'}
          </button>
        ) : (
          <div className="flex gap-2">
            <button
              onClick={handleReset}
              className="text-xs bg-df-surface text-df-muted px-3 py-1.5 rounded-lg"
            >
              {isRu ? 'Сбросить' : 'Reset'}
            </button>
            <button
              onClick={handleSave}
              disabled={savePositionsMutation.isLoading}
              className="text-xs bg-df-accent text-white px-3 py-1.5 rounded-lg font-bold disabled:opacity-50"
            >
              {savePositionsMutation.isLoading
                ? '...'
                : (isRu ? 'Сохранить' : 'Save')}
            </button>
          </div>
        )}
      </div>

      {roomEditMode && (
        <div className="mx-4 mb-2 text-center text-xs text-df-accent bg-df-accent/10 rounded-lg py-2 px-3">
          {isRu ? '✋ Перетащи предметы на нужное место' : '✋ Drag items to reposition them'}
        </div>
      )}

      {/* Room canvas */}
      <div className="mx-4 rounded-2xl overflow-hidden" style={{ height: 240 }}>
        <div
          className="room-container relative w-full h-full"
          style={{ background: 'linear-gradient(170deg, #1a2035 0%, #2a1f4a 60%, #1a2535 100%)' }}
        >
          {/* Floor */}
          <div
            className="absolute bottom-0 left-0 right-0"
            style={{
              height: '35%',
              background: 'linear-gradient(to top, rgba(0,0,0,0.3), transparent)',
              borderTop: '2px solid rgba(255,255,255,0.04)',
            }}
          />

          {/* Pet in room */}
          {hasPet && (
            <DraggableItem
              id={petData.pet.pet_type}
              emoji={petData.pet.pet_type === 'cat' ? '🐱' : '🐶'}
              position={getPosition(petData.pet.pet_type)}
              editMode={roomEditMode}
              onMove={handleItemMove}
            />
          )}

          {/* Active inventory items */}
          {activeItems.map((inv: any) => {
            const key = `${inv.item?.type || 'item'}_${inv.id}`
            return (
              <DraggableItem
                key={inv.id}
                id={key}
                emoji={ITEM_TYPE_EMOJI[inv.item?.type || ''] || '📦'}
                position={getPosition(key)}
                editMode={roomEditMode}
                onMove={handleItemMove}
              />
            )
          })}

          {activeItems.length === 0 && !hasPet && (
            <div className="absolute inset-0 flex items-center justify-center">
              <p className="text-white/20 text-sm">
                {isRu ? 'Квартира пустая' : 'Empty apartment'}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Navigation buttons */}
      <div className="p-4 grid grid-cols-2 gap-3">
        <button
          onClick={() => setGameScreen('inventory')}
          className="card p-3 flex items-center gap-2 active:scale-95 transition-transform"
        >
          <span className="text-xl">🎒</span>
          <span className="text-df-text text-sm font-bold">
            {isRu ? 'Инвентарь' : 'Inventory'}
          </span>
        </button>

        <button
          onClick={() => setGameScreen('shop')}
          className="card p-3 flex items-center gap-2 active:scale-95 transition-transform"
        >
          <span className="text-xl">🛒</span>
          <span className="text-df-text text-sm font-bold">
            {isRu ? 'Магазин' : 'Shop'}
          </span>
        </button>

        <button
          onClick={() => setGameScreen('neighbors')}
          className="card p-3 flex items-center gap-2 active:scale-95 transition-transform"
        >
          <span className="text-xl">👥</span>
          <span className="text-df-text text-sm font-bold">
            {isRu ? 'Соседи' : 'Neighbors'}
          </span>
        </button>

        <button
          onClick={() => setGameScreen('pet')}
          className="card p-3 flex items-center gap-2 active:scale-95 transition-transform relative"
        >
          <span className="text-xl">{hasPet ? (petData?.pet?.pet_type === 'cat' ? '🐱' : '🐶') : '🐾'}</span>
          <span className="text-df-text text-sm font-bold">
            {isRu ? 'Питомец' : 'Pet'}
          </span>
          {hasPet && petData?.pet?.can_feed && (
            <span className="absolute top-1 right-1 w-2 h-2 bg-df-red rounded-full" />
          )}
        </button>
      </div>
    </div>
  )
}
