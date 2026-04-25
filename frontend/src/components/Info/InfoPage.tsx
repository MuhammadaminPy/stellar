import { useQuery } from 'react-query'
import api from '../../utils/api'

const DF_TOKEN_ADDRESS = 'EQAp8pimeVjBHEQdJTD95sh-XRUDmmLIXui83oR5qMvD8Uy0'
const BUY_URL = `https://app.ston.fi/swap?inputCurrency=TON&outputCurrency=${DF_TOKEN_ADDRESS}`
const DEX_CHART_URL = `https://dexscreener.com/ton/${DF_TOKEN_ADDRESS}`

function StatCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="stat-card">
      <span className="text-df-muted text-xs font-semibold">{label}</span>
      <span className="text-df-text font-bold text-lg leading-tight">{value}</span>
      {sub && <span className="text-df-muted text-xs">{sub}</span>}
    </div>
  )
}

function PriceChange({ value }: { value: number | null }) {
  if (value == null) return <span className="text-df-muted text-sm">—</span>
  const pos = value >= 0
  return (
    <span className={`font-bold text-sm ${pos ? 'text-df-green' : 'text-df-red'}`}>
      {pos ? '+' : ''}{value.toFixed(2)}%
    </span>
  )
}

export default function InfoPage() {
  const { data: stats, isLoading: statsLoading } = useQuery(
    'stats',
    () => api.get('/info/stats').then((r) => r.data),
    { refetchInterval: 30000 }
  )

  const { data: holdersData, isLoading: holdersLoading } = useQuery(
    'holders',
    () => api.get('/info/holders').then((r) => r.data),
    { refetchInterval: 60000 }
  )

  const dex = stats?.dex

  return (
    <div className="p-4 space-y-5 animate-fade-in">
      <div className="flex items-center justify-between pt-2">
        <div>
          <h1 className="text-2xl font-black text-df-text">$DF Token</h1>
          <p className="text-df-muted text-sm">Живая статистика</p>
        </div>
        <div className="card px-3 py-2 text-center">
          <div className="text-df-muted text-xs">Цена</div>
          <div className="text-df-gold font-black text-base">
            {dex?.price_usd ? `$${parseFloat(dex.price_usd).toFixed(6)}` : '—'}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <StatCard
          label="Активных юзеров"
          value={statsLoading ? '...' : String(stats?.active_users ?? 0)}
        />
        <StatCard
          label="Market Cap"
          value={dex?.market_cap ? `$${Number(dex.market_cap).toLocaleString()}` : '—'}
        />
        <StatCard
          label="Объём 24ч"
          value={dex?.volume_24h ? `$${Number(dex.volume_24h).toLocaleString()}` : '—'}
        />
        <StatCard
          label="Ликвидность"
          value={dex?.liquidity_usd ? `$${Number(dex.liquidity_usd).toLocaleString()}` : '—'}
        />
      </div>

      <div className="card p-4 space-y-3">
        <p className="section-title">Изменение цены</p>
        <div className="grid grid-cols-3 gap-2 text-center">
          <div>
            <div className="text-df-muted text-xs mb-1">1 час</div>
            <PriceChange value={dex?.price_change_1h} />
          </div>
          <div>
            <div className="text-df-muted text-xs mb-1">6 часов</div>
            <PriceChange value={dex?.price_change_6h} />
          </div>
          <div>
            <div className="text-df-muted text-xs mb-1">24 часа</div>
            <PriceChange value={dex?.price_change_24h} />
          </div>
        </div>
      </div>

      <div className="card p-4 space-y-3">
        <p className="section-title">Транзакции за 24ч</p>
        <div className="flex gap-3">
          <div className="flex-1 bg-df-green/10 rounded-xl p-3 text-center">
            <div className="text-df-muted text-xs mb-1">Покупок</div>
            <div className="text-df-green font-black text-xl">{dex?.txns_24h_buys ?? '—'}</div>
          </div>
          <div className="flex-1 bg-df-red/10 rounded-xl p-3 text-center">
            <div className="text-df-muted text-xs mb-1">Продаж</div>
            <div className="text-df-red font-black text-xl">{dex?.txns_24h_sells ?? '—'}</div>
          </div>
        </div>
      </div>

      <div className="card overflow-hidden">
        <div className="p-3 border-b border-df-border flex items-center justify-between">
          <p className="section-title mb-0">График DEX (реальное время)</p>
          <a
            href={DEX_CHART_URL}
            target="_blank"
            rel="noreferrer"
            className="text-df-accent text-xs font-bold"
          >
            Открыть ↗
          </a>
        </div>
        <iframe
          src={`https://dexscreener.com/ton/${DF_TOKEN_ADDRESS}?embed=1&theme=dark&trades=0&info=0`}
          className="w-full border-0"
          style={{ height: 320 }}
          title="DEX Chart"
          loading="lazy"
        />
      </div>

      <a href={BUY_URL} target="_blank" rel="noreferrer" className="block">
        <button className="btn-gold w-full text-base">
          🛒 Купить $DF
        </button>
      </a>

      <div className="card p-4 space-y-3">
        <p className="section-title">Топ 10 холдеров</p>
        {holdersLoading ? (
          <div className="space-y-2">
            {Array(5).fill(0).map((_, i) => (
              <div key={i} className="shimmer h-10 w-full" />
            ))}
          </div>
        ) : (
          <div className="space-y-2">
            {(holdersData?.holders || []).slice(0, 10).map((h: any, i: number) => (
              <div
                key={i}
                className="flex items-center justify-between bg-df-surface rounded-xl px-3 py-2"
              >
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-black w-5 text-center ${i === 0 ? 'text-df-gold' : i === 1 ? 'text-gray-300' : i === 2 ? 'text-amber-600' : 'text-df-muted'}`}>
                    #{i + 1}
                  </span>
                  <span className="text-df-muted text-xs font-mono">
                    {h.address?.slice(0, 6)}...{h.address?.slice(-4)}
                  </span>
                </div>
                <span className="text-df-text text-xs font-bold">
                  {Number(h.balance / 1e9).toLocaleString()} $DF
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
