import { useState } from 'react'
import { AlertTriangle, ArrowLeft, Droplets, Volume2 } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import { useFarmer } from '../FarmerContext'
import { makeT } from '../i18n'

export default function Result() {
  const { lang, diagnosis } = useFarmer()
  const t = makeT(lang)
  const navigate = useNavigate()
  const [listening, setListening] = useState(false)

  if (!diagnosis) {
    return (
      <div className="text-center pt-16">
        <p className="text-sm font-light text-soil-dark/60">{t('noScanBody')}</p>
        <Link
          to="/app"
          className="mt-6 inline-flex items-center justify-center min-h-[48px] px-6 rounded-full bg-leaf-deep text-cream text-sm font-medium"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          {t('backHome')}
        </Link>
      </div>
    )
  }

  const { disease, crop, confidence, imageUrl, heatmap, flagged, advisory } = diagnosis

  const listen = () => {
    if (listening) return
    setListening(true)
    // MOCK — Bhashini TTS lands here later.
    setTimeout(() => setListening(false), 2200)
  }

  return (
    <div className="space-y-5">
      <div className="relative rounded-3xl overflow-hidden bg-soil-dark">
        <img src={imageUrl} alt={`${crop} leaf`} className="w-full h-64 object-cover" />
        <div
          aria-label={t('aiLookedHere')}
          className="absolute rounded-full border-4 border-ochre/90"
          style={{
            top: `${heatmap.top}%`,
            left: `${heatmap.left}%`,
            width: `${heatmap.size}%`,
            aspectRatio: '1',
            background:
              'radial-gradient(circle, rgba(200,134,45,0.45) 0%, rgba(200,134,45,0.18) 55%, rgba(200,134,45,0) 75%)',
          }}
        />
        <span className="absolute bottom-3 left-3 bg-black/60 text-cream text-[11px] px-2.5 py-1 rounded-full">
          {t('aiLookedHere')}
        </span>
      </div>

      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="font-instrument-serif text-3xl leading-tight">{disease}</h1>
          <p className="text-xs font-light text-soil-dark/60">{crop}</p>
        </div>
        <span
          className={`shrink-0 px-3 py-1.5 rounded-full text-sm font-medium ${
            confidence >= 70 ? 'bg-leaf/15 text-leaf-deep' : 'bg-ochre/15 text-ochre'
          }`}
        >
          {confidence}% {t('confidence')}
        </span>
      </div>

      {flagged ? (
        <div className="rounded-2xl border border-ochre/50 bg-ochre/10 p-4 flex gap-3">
          <AlertTriangle className="w-5 h-5 text-ochre shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-ochre">{t('flaggedTitle')}</p>
            <p className="mt-1 text-sm font-light leading-relaxed text-soil-dark/80">
              {t('flaggedBody')}
            </p>
          </div>
        </div>
      ) : (
        <section className="rounded-2xl bg-white border border-soil-dark/10 p-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-medium">{t('whatToDo')}</h2>
            <button
              onClick={listen}
              className={`flex items-center gap-1.5 min-h-[40px] px-3.5 rounded-full text-xs font-medium border transition-colors duration-200 ${
                listening
                  ? 'bg-ochre text-cream border-ochre animate-pulse'
                  : 'bg-leaf-deep text-cream border-leaf-deep'
              }`}
            >
              <Volume2 className="w-4 h-4" />
              {listening ? t('listening') : t('listen')}
            </button>
          </div>
          <ol className="mt-3 space-y-3">
            {advisory.map(({ step }, i) => (
              <li key={i} className="flex gap-3">
                <span
                  aria-hidden
                  className="shrink-0 w-6 h-6 rounded-full bg-leaf/15 text-leaf-deep text-xs font-medium flex items-center justify-center"
                >
                  {i + 1}
                </span>
                <p className="text-sm font-light leading-relaxed">{step}</p>
              </li>
            ))}
          </ol>
        </section>
      )}

      <div className="grid grid-cols-2 gap-3">
        <Link
          to="/app/dosage"
          className="min-h-[48px] rounded-full bg-ochre text-cream flex items-center justify-center gap-2 text-sm font-medium"
        >
          <Droplets className="w-4 h-4" />
          {t('calcDosage')}
        </Link>
        <button
          onClick={() => navigate('/app')}
          className="min-h-[48px] rounded-full border border-soil-dark/30 text-soil-dark flex items-center justify-center gap-2 text-sm font-medium"
        >
          <ArrowLeft className="w-4 h-4" />
          {t('backHome')}
        </button>
      </div>
    </div>
  )
}
