import { useEffect, useState } from 'react'
import { MapPin } from 'lucide-react'
import { useFarmer } from '../FarmerContext'
import { makeT } from '../i18n'
import { getNearbyAlerts, type NearbyAlert } from '../mockApi'

export default function Alerts() {
  const { lang } = useFarmer()
  const t = makeT(lang)
  const [alerts, setAlerts] = useState<NearbyAlert[] | null>(null)

  useEffect(() => {
    let on = true
    // MOCK — swap with the real endpoint; same shape.
    getNearbyAlerts({ lat: 18.52, lon: 73.86 }).then((a) => on && setAlerts(a))
    return () => {
      on = false
    }
  }, [])

  return (
    <div className="space-y-4">
      <h1 className="font-instrument-serif text-3xl leading-tight">{t('nearby')}</h1>

      {alerts === null && (
        <div className="space-y-2">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-20 rounded-2xl bg-soil-dark/5 animate-pulse" />
          ))}
        </div>
      )}

      {alerts !== null && alerts.length === 0 && (
        <div className="rounded-2xl border border-dashed border-soil-dark/20 p-8 text-center">
          <MapPin className="w-8 h-8 mx-auto text-leaf" />
          <p className="mt-3 text-sm font-light text-soil-dark/60">{t('emptyAlerts')}</p>
        </div>
      )}

      {alerts !== null &&
        alerts.length > 0 &&
        alerts.map((a) => (
          <div
            key={a.id}
            className="flex items-center gap-3 rounded-2xl bg-white border border-soil-dark/10 p-4"
          >
            <span className="shrink-0 w-10 h-10 rounded-full bg-ochre/15 text-ochre flex items-center justify-center">
              <MapPin className="w-5 h-5" />
            </span>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{a.disease}</p>
              <p className="text-xs font-light text-soil-dark/60">
                {a.distanceKm} {t('kmAway')} · {a.daysAgo} {t('daysAgo')}
              </p>
            </div>
          </div>
        ))}
    </div>
  )
}
