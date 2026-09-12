import { useEffect, useRef, useState } from 'react'
import { Camera, ChevronRight, Droplets, MapPin } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import { useFarmer } from '../FarmerContext'
import { makeT } from '../i18n'
import {
  getRecentDiagnoses,
  getRiskForecast,
  predictDisease,
  type RecentDiagnosis,
  type RiskForecast,
} from '../mockApi'

const RISK_STYLES: Record<RiskForecast['level'], string> = {
  low: 'bg-leaf/15 text-leaf-deep border-leaf/40',
  medium: 'bg-ochre/15 text-ochre border-ochre/40',
  high: 'bg-soil-dark/10 text-soil-dark border-soil-dark/40',
}

export default function Home() {
  const { lang, setDiagnosis } = useFarmer()
  const t = makeT(lang)
  const navigate = useNavigate()
  const fileRef = useRef<HTMLInputElement>(null)
  const [risk, setRisk] = useState<RiskForecast | null>(null)
  const [recent, setRecent] = useState<RecentDiagnosis[]>([])
  const [scanning, setScanning] = useState(false)

  useEffect(() => {
    let on = true
    // MOCK — replace with real fetches; shapes identical.
    getRiskForecast('Pune', 'Cotton').then((r) => on && setRisk(r))
    getRecentDiagnoses().then((r) => on && setRecent(r))
    return () => {
      on = false
    }
  }, [])

  const onPick = async (file: File | undefined) => {
    if (!file) return
    setScanning(true)
    const result = await predictDisease(file, lang)
    setDiagnosis(result)
    navigate('/app/result')
  }

  return (
    <div className="space-y-5">
      <button
        onClick={() => fileRef.current?.click()}
        disabled={scanning}
        className="w-full min-h-[112px] rounded-3xl bg-leaf-deep text-cream flex flex-col items-center justify-center gap-2 active:scale-[0.99] transition-transform duration-200 disabled:opacity-80"
      >
        <Camera className="w-8 h-8 text-ochre" />
        <span className="text-base font-medium">
          {scanning ? '…' : t('takePhoto')}
        </span>
        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          capture="environment"
          className="hidden"
          onChange={(e) => {
            onPick(e.target.files?.[0])
            e.target.value = ''
          }}
        />
      </button>

      {risk && (
        <Link
          to="/app/alerts"
          className={`flex items-center justify-between rounded-2xl border px-4 min-h-[64px] ${RISK_STYLES[risk.level]}`}
        >
          <span className="flex items-center gap-2.5">
            <MapPin className="w-5 h-5" />
            <span className="text-sm font-medium">
              {t('risk')} · {t(risk.level)} — {risk.crop}, {risk.district}
            </span>
          </span>
          <ChevronRight className="w-4 h-4 opacity-60" />
        </Link>
      )}

      <section>
        <h2 className="text-sm font-medium text-soil-dark/70 mb-2">{t('recent')}</h2>
        <ul className="space-y-2">
          {recent.map((d) => (
            <li
              key={d.id}
              className="flex items-center gap-3 rounded-2xl bg-white border border-soil-dark/10 p-3"
            >
              <img src={d.thumb} alt="" className="w-12 h-12 rounded-xl object-cover" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{d.disease}</p>
                <p className="text-xs font-light text-soil-dark/60">{d.date}</p>
              </div>
              <span
                className={`px-2 py-1 rounded-full text-[11px] font-medium ${
                  d.confidence >= 70
                    ? 'bg-leaf/15 text-leaf-deep'
                    : 'bg-ochre/15 text-ochre'
                }`}
              >
                {d.confidence}% {t('confidence')}
              </span>
            </li>
          ))}
        </ul>
      </section>

      <div className="grid grid-cols-2 gap-3">
        <Link
          to="/app/dosage"
          className="min-h-[72px] rounded-2xl bg-ochre/15 border border-ochre/40 text-ochre flex flex-col items-center justify-center gap-1.5"
        >
          <Droplets className="w-6 h-6" />
          <span className="text-sm font-medium">{t('dosage')}</span>
        </Link>
        <Link
          to="/app/alerts"
          className="min-h-[72px] rounded-2xl bg-leaf/15 border border-leaf/40 text-leaf-deep flex flex-col items-center justify-center gap-1.5"
        >
          <MapPin className="w-6 h-6" />
          <span className="text-sm font-medium">{t('alerts')}</span>
        </Link>
      </div>
    </div>
  )
}
