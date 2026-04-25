import { useAppStore } from '../../store'
import HomeGame from './HomeGame'

export default function GamesPage() {
  const { gameScreen, setGameScreen } = useAppStore()

  if (gameScreen === 'home' || gameScreen === 'inventory' || gameScreen === 'shop' || gameScreen === 'neighbors') {
    return <HomeGame />
  }

  return (
    <div className="p-4 space-y-4 animate-fade-in">
      <div className="pt-2">
        <h1 className="text-2xl font-black text-df-text">Игры</h1>
        <p className="text-df-muted text-sm">Зарабатывай $DF играя</p>
      </div>

      {/* Главная игра — Мой уютный дом */}
      <button
        onClick={() => setGameScreen('home')}
        className="w-full card p-0 overflow-hidden active:scale-95 transition-transform"
      >
        <div
          className="h-40 relative flex items-end"
          style={{ background: 'linear-gradient(135deg, #1a1f35 0%, #2a1f4a 50%, #1a2535 100%)' }}
        >
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-6xl select-none">🏠</div>
          </div>
          <div className="relative w-full p-4 bg-gradient-to-t from-df-card to-transparent">
            <div className="flex items-end justify-between">
              <div>
                <h2 className="text-white font-black text-xl">Мой уютный дом</h2>
                <p className="text-df-muted text-sm">Украшай, торгуй, соревнуйся</p>
              </div>
              <span className="badge-gold">Новинка</span>
            </div>
          </div>
        </div>
      </button>

      {/* Скоро — красивый блок */}
      <div
        className="card p-8 flex flex-col items-center justify-center gap-3 opacity-60"
        style={{ minHeight: 140 }}
      >
        <p
          className="text-df-muted tracking-[0.35em] uppercase"
          style={{
            fontFamily: "'Georgia', 'Times New Roman', serif",
            fontSize: '2rem',
            fontWeight: 900,
            letterSpacing: '0.3em',
            background: 'linear-gradient(90deg, #a0aec0 0%, #e2e8f0 50%, #a0aec0 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}
        >
          soon
        </p>
        <p className="text-df-muted text-xs text-center">
          Новые игры уже в разработке
        </p>
      </div>
    </div>
  )
}