import { useState } from 'react'
import { Ban, FlaskConical, Info, Loader2, ShieldCheck } from 'lucide-react'
import { api } from '../../api/client'
import type { LabelVerdict } from '../../api/types'
import { useAsync } from '../../lib/hooks'
import { ErrorBox, ListenButton, VoiceButton } from '../../ui/kit'
import { useFarmer } from '../FarmerContext'

const QUICK = ['Mancozeb', 'Copper oxychloride', 'Emamectin', 'Tricyclazole', 'Chlorantraniliprole', 'Glyphosate']

export default function Spray() {
  const { farmId, lang, t } = useFarmer()
  const [q, setQ] = useState('')
  const [busy, setBusy] = useState(false)
  const [v, setV] = useState<LabelVerdict | null>(null)
  const [error, setError] = useState<Error | null>(null)
  const home = useAsync(() => api.home(farmId!, lang), [farmId, lang])
  const current = home.data?.problems.find((p) => p.status === 'open' && p.name)

  const check = async (text = q) => {
    if (!text.trim()) return
    setBusy(true)
    setError(null)
    try {
      setV(await api.labelCheck(farmId!, text.trim(), lang))
    } catch (e) {
      setError(e as Error)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-5">
      <div>
        <FlaskConical className="w-8 h-8 text-ochre" />
        <h1 className="mt-2 font-instrument-serif text-3xl leading-tight">{t('sprayTitle')}</h1>
        <p className="mt-1 text-sm text-soil-dark/60">{t('spraySub')}</p>
      </div>

      <p className="text-xs rounded-xl bg-white border border-soil-dark/10 px-3 py-2">
        <span className="text-soil-dark/50">{t('forProblem')}: </span>
        <span className="font-medium">{current?.name ?? t('noDiagnosisYet')}</span>
      </p>

      <form
        onSubmit={(e) => {
          e.preventDefault()
          check()
        }}
        className="space-y-2"
      >
        <div className="flex gap-2">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder={t('productName')}
            className="flex-1 min-w-0 min-h-[48px] rounded-xl border border-soil-dark/20 px-3 bg-white text-sm focus:outline-none focus:border-leaf"
          />
          <VoiceButton lang={lang} label={t('speak')} recordingLabel={t('recording')} onText={(txt) => {
            setQ(txt)
            check(txt)
          }} />
        </div>
        <button type="submit" disabled={busy || !q.trim()} className="w-full min-h-[48px] rounded-full bg-leaf-deep text-cream text-sm font-medium disabled:opacity-50 flex items-center justify-center gap-2">
          {busy && <Loader2 className="w-4 h-4 animate-spin" />}
          {t('check')}
        </button>
      </form>

      <div className="flex flex-wrap gap-1.5">
        {QUICK.map((p) => (
          <button key={p} onClick={() => {
            setQ(p)
            check(p)
          }} className="px-3 py-1.5 rounded-full bg-white border border-soil-dark/15 text-xs">
            {p}
          </button>
        ))}
      </div>

      {error && <ErrorBox error={error} />}

      {v && (
        <section className={`rounded-2xl p-5 animate-fadein ${v.is_veto ? 'bg-ember text-cream' : 'bg-white border-2 border-leaf/40'}`}>
          <div className="flex items-start justify-between gap-3">
            <p className="flex items-center gap-2 text-xl font-semibold">
              {v.is_veto ? <Ban className="w-6 h-6" /> : <ShieldCheck className="w-6 h-6 text-leaf" />}
              {v.is_veto ? t('vetoTitle') : t('noObjectionTitle')}
            </p>
            <ListenButton text={v.message} lang={lang} label={t('listen')} stopLabel={t('stop')} compact />
          </div>
          {v.product && <p className={`mt-1 text-xs ${v.is_veto ? 'text-cream/80' : 'text-soil-dark/60'}`}>{v.product}</p>}
          <p className="mt-3 text-[15px] leading-snug">{v.message}</p>
        </section>
      )}

      <p className="flex gap-2 text-xs text-soil-dark/60">
        <Info className="w-4 h-4 shrink-0" />
        {t('neverSafeNote')}
      </p>
    </div>
  )
}
