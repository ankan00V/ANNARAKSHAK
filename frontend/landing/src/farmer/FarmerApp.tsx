import { useEffect, useState } from 'react'
import { Bell, Camera, FlaskConical, History, Home as HomeIcon, MapPin, Repeat } from 'lucide-react'
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import type { Farm } from '../api/types'
import { LANGS } from '../lib/i18n'
import { FarmerProvider, useFarmer } from './FarmerContext'
import Onboard from './screens/Onboard'

const NAV = [
  { to: '/app', icon: HomeIcon, key: 'home' },
  { to: '/app/scan', icon: Camera, key: 'scan' },
  { to: '/app/spray', icon: FlaskConical, key: 'spray' },
  { to: '/app/alerts', icon: Bell, key: 'alerts' },
  { to: '/app/history', icon: History, key: 'history' },
]

function Shell() {
  const { lang, setLang, farmId, setFarmId, t } = useFarmer()
  const { pathname } = useLocation()
  const navigate = useNavigate()
  const [farm, setFarm] = useState<Farm | null>(null)

  useEffect(() => {
    if (farmId == null) return
    let on = true
    api.farms(lang).then((fs) => {
      if (!on) return
      const f = fs.find((x) => x.id === farmId) ?? null
      setFarm(f)
      if (!f) setFarmId(null) // stale id from an older database
    }).catch(() => undefined)
    return () => {
      on = false
    }
  }, [farmId, lang, setFarmId])

  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])

  const active = pathname === '/app/result' || pathname === '/app/live'
    ? '/app/scan'
    : NAV.slice().reverse().find((n) => pathname === n.to || pathname.startsWith(n.to + '/'))?.to ?? '/app'

  return (
    <div className="min-h-screen w-full bg-cream text-soil-dark flex flex-col">
      <header className="sticky top-0 z-30 bg-leaf-deep text-cream shadow-sm">
        <div className="max-w-md mx-auto flex items-center justify-between gap-3 px-4 py-3">
          <Link to="/app" className="flex items-center gap-2 min-w-0">
            <span className="w-8 h-8 rounded-full bg-cream/10 ring-1 ring-ochre/40 flex items-center justify-center font-instrument-serif text-lg text-ochre">
              अ
            </span>
            <span className="min-w-0">
              <span className="block font-semibold tracking-tight leading-none">AnnRakshak</span>
              {farm && (
                <span className="flex items-center gap-1 text-[11px] text-cream/70 truncate">
                  <MapPin className="w-3 h-3 shrink-0" />
                  {farm.farmer_name} · {farm.crop_name} · {farm.district}
                </span>
              )}
            </span>
          </Link>
          <div className="flex items-center gap-1.5">
            {farm && (
              <button
                onClick={() => {
                  setFarmId(null)
                  navigate('/app')
                }}
                aria-label={t('switchFarm')}
                className="w-9 h-9 rounded-full bg-cream/10 flex items-center justify-center hover:bg-cream/20"
              >
                <Repeat className="w-4 h-4" />
              </button>
            )}
            <div className="flex rounded-full bg-cream/10 p-0.5">
              {LANGS.map(({ code, label }) => (
                <button
                  key={code}
                  onClick={() => setLang(code)}
                  className={`px-2.5 py-1.5 rounded-full text-[11px] font-medium min-h-[32px] transition-colors ${
                    lang === code ? 'bg-cream text-leaf-deep' : 'text-cream/70 hover:text-cream'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1 w-full max-w-md mx-auto px-4 pt-5 pb-28 animate-fadein" key={pathname}>
        {farmId == null ? <Onboard /> : <Outlet />}
      </main>

      {farmId != null && (
        <nav className="fixed bottom-0 inset-x-0 z-30 bg-white/95 backdrop-blur border-t border-soil-dark/10 pb-[env(safe-area-inset-bottom)]">
          <div className="max-w-md mx-auto grid grid-cols-5">
            {NAV.map(({ to, icon: Icon, key }) => {
              const on = active === to
              const isScan = to === '/app/scan'
              return (
                <Link
                  key={to}
                  to={to}
                  className={`flex flex-col items-center justify-center gap-0.5 py-2 min-h-[60px] text-[10.5px] font-medium transition-colors ${
                    on ? 'text-leaf-deep' : 'text-soil-dark/50 hover:text-soil-dark'
                  }`}
                >
                  {isScan ? (
                    <span className={`-mt-6 w-12 h-12 rounded-full flex items-center justify-center shadow-lg ring-4 ring-cream ${on ? 'bg-ochre text-cream' : 'bg-leaf-deep text-cream'}`}>
                      <Icon className="w-5 h-5" />
                    </span>
                  ) : (
                    <Icon className="w-5 h-5" strokeWidth={on ? 2.4 : 2} />
                  )}
                  {t(key)}
                </Link>
              )
            })}
          </div>
        </nav>
      )}
    </div>
  )
}

export default function FarmerApp() {
  return (
    <FarmerProvider>
      <Shell />
    </FarmerProvider>
  )
}
