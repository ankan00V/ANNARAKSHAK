import { useEffect, useState } from 'react'
import { Calculator, ShieldAlert } from 'lucide-react'
import { useFarmer } from '../FarmerContext'
import { makeT } from '../i18n'
import { getDosage, type DosageResult } from '../mockApi'

export default function Dosage() {
  const { lang, diagnosis } = useFarmer()
  const t = makeT(lang)
  const [land, setLand] = useState('')
  const [unit, setUnit] = useState<'acres' | 'hectares'>('acres')
  const [result, setResult] = useState<DosageResult | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    setResult(null)
  }, [unit])

  const calc = async () => {
    const n = parseFloat(land)
    if (!n || n <= 0) return
    setBusy(true)
    // MOCK — real endpoint computes from the ICAR dosage KB.
    setResult(await getDosage(diagnosis?.disease ?? null, n, unit))
    setBusy(false)
  }

  return (
    <div className="space-y-5">
      <h1 className="font-instrument-serif text-3xl leading-tight">{t('landSize')}</h1>

      {diagnosis && (
        <p className="text-xs font-light text-soil-dark/60">
          {diagnosis.disease} · {diagnosis.crop}
        </p>
      )}

      <div className="rounded-2xl bg-white border border-soil-dark/10 p-4 space-y-4">
        <div className="flex gap-2">
          <input
            type="number"
            inputMode="decimal"
            min="0"
            value={land}
            onChange={(e) => setLand(e.target.value)}
            placeholder="0.0"
            aria-label={t('landSize')}
            className="flex-1 min-h-[48px] rounded-xl border border-soil-dark/20 px-4 text-lg font-medium bg-cream/50 focus:outline-none focus:border-leaf"
          />
          <div className="flex rounded-xl bg-cream p-1 border border-soil-dark/10">
            {(['acres', 'hectares'] as const).map((u) => (
              <button
                key={u}
                onClick={() => setUnit(u)}
                className={`px-3 min-h-[40px] rounded-lg text-xs font-medium transition-colors duration-200 ${
                  unit === u ? 'bg-leaf-deep text-cream' : 'text-soil-dark/60'
                }`}
              >
                {t(u)}
              </button>
            ))}
          </div>
        </div>
        <button
          onClick={calc}
          disabled={busy || !land}
          className="w-full min-h-[48px] rounded-full bg-leaf-deep text-cream text-sm font-medium flex items-center justify-center gap-2 disabled:opacity-50"
        >
          <Calculator className="w-4 h-4" />
          {t('calculate')}
        </button>
      </div>

      {result && (
        <div className="rounded-2xl bg-white border border-soil-dark/10 p-4 space-y-3 animate-[fadein_0.25s_ease-out]">
          <div className="flex justify-between items-baseline">
            <span className="text-xs font-light text-soil-dark/60">{t('pesticide')}</span>
            <span className="text-sm font-medium text-right">{result.pesticide}</span>
          </div>
          <div className="flex justify-between items-baseline">
            <span className="text-xs font-light text-soil-dark/60">{t('quantity')}</span>
            <span className="text-sm font-medium">{result.quantity}</span>
          </div>
          <div className="flex justify-between items-baseline">
            <span className="text-xs font-light text-soil-dark/60">{t('estCost')}</span>
            <span className="text-lg font-medium text-leaf-deep">₹{result.costInr}</span>
          </div>
        </div>
      )}

      <p className="flex gap-2.5 rounded-2xl border border-ochre/40 bg-ochre/10 p-4 text-xs font-light leading-relaxed text-soil-dark/80">
        <ShieldAlert className="w-4 h-4 text-ochre shrink-0 mt-0.5" />
        {t('disclaimer')}
      </p>
    </div>
  )
}
