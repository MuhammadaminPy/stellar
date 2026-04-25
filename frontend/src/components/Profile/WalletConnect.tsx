import { useState, useEffect } from 'react'
import { useMutation, useQueryClient } from 'react-query'
import { useAppStore } from '../../store'
import api from '../../utils/api'

declare global {
  interface Window {
    TonConnectUI?: any
    tonConnectUI?: any
  }
}

interface WalletState {
  address: string | null
  connected: boolean
}

export default function WalletConnect() {
  const { lang } = useAppStore()
  const isRu = lang === 'ru'
  const qc = useQueryClient()

  const [wallet, setWallet] = useState<WalletState>({ address: null, connected: false })
  const [amount, setAmount] = useState('')
  const [step, setStep] = useState<'idle' | 'amount' | 'pending' | 'success' | 'error'>('idle')
  const [errorMsg, setErrorMsg] = useState('')
  const [tcReady, setTcReady] = useState(false)

  // Load TonConnect UI dynamically
  useEffect(() => {
    if (window.tonConnectUI) {
      setTcReady(true)
      return
    }
    const script = document.createElement('script')
    script.src = 'https://unpkg.com/@tonconnect/ui@latest/dist/tonconnect-ui.min.js'
    script.onload = () => {
      try {
        window.tonConnectUI = new window.TonConnectUI({
          manifestUrl: `${window.location.origin}/tonconnect-manifest.json`,
        })
        window.tonConnectUI.onStatusChange((w: any) => {
          if (w) {
            setWallet({ address: w.account?.address || null, connected: true })
          } else {
            setWallet({ address: null, connected: false })
          }
        })
        setTcReady(true)
      } catch (e) {
        console.error('TonConnect init failed', e)
      }
    }
    document.head.appendChild(script)
  }, [])

  const handleConnect = async () => {
    if (!window.tonConnectUI) return
    try {
      await window.tonConnectUI.openModal()
    } catch (e) {
      console.error('Connect failed', e)
    }
  }

  const handleDisconnect = async () => {
    if (!window.tonConnectUI) return
    await window.tonConnectUI.disconnect()
    setWallet({ address: null, connected: false })
    setStep('idle')
  }

  const depositMutation = useMutation(
    async ({ boc, amount_ton, wallet_address }: { boc: string; amount_ton: number; wallet_address: string }) => {
      const res = await api.post('/wallet/deposit/ton_connect', {
        boc,
        amount_ton,
        wallet_address,
      })
      return res.data
    },
    {
      onSuccess: (data) => {
        setStep('success')
        qc.invalidateQueries('profile')
      },
      onError: (e: any) => {
        setErrorMsg(e.response?.data?.detail || (isRu ? 'Ошибка пополнения' : 'Deposit failed'))
        setStep('error')
      },
    }
  )

  const handleDeposit = async () => {
    if (!wallet.connected || !wallet.address || !amount) return

    const tonAmount = parseFloat(amount)
    if (isNaN(tonAmount) || tonAmount <= 0) return

    setStep('pending')
    setErrorMsg('')

    try {
      // Fetch deposit comment from backend
      const infoRes = await api.get('/wallet/deposit/info')
      const { comment, wallet: destWallet } = infoRes.data

      // Send TON transaction via TonConnect
      const amountNano = Math.floor(tonAmount * 1e9).toString()
      const txPayload = {
        validUntil: Math.floor(Date.now() / 1000) + 300,
        messages: [
          {
            address: destWallet,
            amount: amountNano,
            payload: btoa(comment), // base64 encoded comment
          },
        ],
      }

      const result = await window.tonConnectUI.sendTransaction(txPayload)

      // Verify on backend
      depositMutation.mutate({
        boc: result.boc,
        amount_ton: tonAmount,
        wallet_address: wallet.address,
      })
    } catch (e: any) {
      if (e?.message?.includes('User rejects')) {
        setStep('idle')
      } else {
        setErrorMsg(isRu ? 'Транзакция отменена или ошибка' : 'Transaction cancelled or failed')
        setStep('error')
      }
    }
  }

  const shortAddr = (addr: string) =>
    addr.length > 12 ? `${addr.slice(0, 6)}...${addr.slice(-4)}` : addr

  if (!tcReady) return null

  return (
    <div className="card p-4 space-y-3">
      <h3 className="font-bold text-df-text">💎 TON {isRu ? 'Кошелёк' : 'Wallet'}</h3>

      {!wallet.connected ? (
        <button
          onClick={handleConnect}
          className="w-full btn-primary py-2.5 rounded-xl font-bold text-sm"
        >
          {isRu ? '🔗 Подключить кошелёк' : '🔗 Connect wallet'}
        </button>
      ) : (
        <div className="space-y-3">
          <div className="flex items-center justify-between bg-df-surface rounded-xl px-3 py-2">
            <div>
              <p className="text-xs text-df-muted">{isRu ? 'Кошелёк подключён' : 'Wallet connected'}</p>
              <p className="text-df-accent font-mono text-sm">{wallet.address ? shortAddr(wallet.address) : '—'}</p>
            </div>
            <button
              onClick={handleDisconnect}
              className="text-xs text-df-muted hover:text-df-red transition-colors"
            >
              {isRu ? 'Отключить' : 'Disconnect'}
            </button>
          </div>

          {step === 'idle' && (
            <button
              onClick={() => setStep('amount')}
              className="w-full bg-df-green/10 text-df-green border border-df-green/30 py-2.5 rounded-xl font-bold text-sm hover:bg-df-green/20 transition-colors"
            >
              💰 {isRu ? 'Пополнить баланс' : 'Deposit'}
            </button>
          )}

          {step === 'amount' && (
            <div className="space-y-2">
              <input
                type="number"
                min="0.01"
                step="0.1"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder={isRu ? 'Сумма в TON' : 'Amount in TON'}
                className="w-full bg-df-surface border border-df-border rounded-xl px-4 py-2.5 text-df-text focus:outline-none focus:border-df-accent"
              />
              <p className="text-df-muted text-xs text-center">
                {isRu
                  ? 'Средства будут зачислены в $DF по курсу на момент пополнения'
                  : 'Funds will be credited in $DF at the current rate'}
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setStep('idle')}
                  className="flex-1 bg-df-surface text-df-muted py-2 rounded-xl text-sm"
                >
                  {isRu ? 'Отмена' : 'Cancel'}
                </button>
                <button
                  onClick={handleDeposit}
                  disabled={!amount || parseFloat(amount) <= 0}
                  className="flex-1 btn-primary py-2 rounded-xl font-bold text-sm disabled:opacity-50"
                >
                  {isRu ? 'Отправить' : 'Send'}
                </button>
              </div>
            </div>
          )}

          {step === 'pending' && (
            <div className="text-center py-4 space-y-2">
              <div className="text-2xl animate-pulse">💎</div>
              <p className="text-df-muted text-sm">
                {isRu ? 'Подтверди транзакцию в кошельке...' : 'Confirm transaction in your wallet...'}
              </p>
            </div>
          )}

          {step === 'success' && (
            <div className="text-center py-3 space-y-1">
              <div className="text-2xl">✅</div>
              <p className="text-df-green font-bold">
                {isRu ? 'Пополнение прошло!' : 'Deposit successful!'}
              </p>
              <button onClick={() => setStep('idle')} className="text-df-muted text-sm underline">
                {isRu ? 'Ещё раз' : 'Again'}
              </button>
            </div>
          )}

          {step === 'error' && (
            <div className="text-center py-3 space-y-1">
              <div className="text-2xl">❌</div>
              <p className="text-df-red text-sm">{errorMsg}</p>
              <button onClick={() => setStep('amount')} className="text-df-muted text-sm underline">
                {isRu ? 'Попробовать снова' : 'Try again'}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
