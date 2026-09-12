import { useEffect, useState } from 'react'
import { Camera, Droplets, Bell } from 'lucide-react'
import { Link, Outlet, useLocation } from 'react-router-dom'
import { FarmerProvider, useFarmer } from './FarmerContext'
import { makeT } from './i18n'
import type { Lang } from './FarmerContext'

const LANGS: Lang[] = ['hi', 'mr', 'en']

const NAV = [
  { to: '/app', icon: Camera, key: 'home' },
  { to: '/app/dosage', icon: Droplets, key: 'dosage' },
  { to: '/app/alerts', icon: Bell, key: 'alerts' },
]

const SCREENS = new Set(['/app', '/app/dosage', '/app/alerts'])

function Shell() {
  const { lang, setLang } = useFarmer()
  const t = makeT(lang)
  const { pathname } = useLocation()
  const [shown, setShown] = useState(pathname)
  const [fading, setFading] = useState(false)

  useEffect(() => {
    if (pathname === shown) return
    setFading(true)
    const id = setTimeout(() => {
      setShown(pathname)
      window.scrollTo(0, 0)
      setFading(false)
    }, 180)
    return () => clearTimeout(id)
  }, [pathname, shown])

  const navTarget = SCREENS.has(pathname) ? pathname : '/app'

  return (
    <div className="min-h-screen w-full bg-cream text-soil-dark flex flex-col">
      <header className="sticky top-0 z-20 bg-leaf-deep text-cream">
        <div className="flex items-center justify-between px-4 py-3">
          <span className="font-semibold tracking-tight">AnnRakshak</span>
          <div className="flex rounded-full bg-cream/10 p-1">
            {LANGS.map((code) => (
              <button
                key={code}
                onClick={() => setLang(code)}
                aria-label={`Language: ${code.toUpperCase()}`}
                className={`px-3 py-1.5 rounded-full text-xs font-medium min-h-[32px] transition-colors duration-200 ${
                  lang === code ? 'bg-cream text-leaf-deep' : 'text-cream/70 hover:text-cream'
                }`}
              >
                {code.toUpperCase()}
              </button>
            ))}
          </div>
        </div>
      </header>

      <main
        className={`flex-1 w-full max-w-md mx-auto px-4 pt-5 pb-24 transition-all duration-200 ${
          fading ? 'opacity-0 translate-y-1' : 'opacity-100 translate-y-0'
        }`}
      >
        <div key={shown}>
          <Outlet />
        </div>
      </main>

      <nav className="fixed bottom-0 inset-x-0 z-20 bg-white border-t border-soil-dark/10">
        <div className="max-w-md mx-auto grid grid-cols-3">
          {NAV.map(({ to, icon: Icon, key }) => {
            const active = navTarget === to
            return (
              <Link
                key={to}
                to={to}
                className={`flex flex-col items-center justify-center gap-0.5 py-2.5 min-h-[56px] text-[11px] font-medium transition-colors duration-200 ${
                  active ? 'text-leaf-deep' : 'text-soil-dark/50 hover:text-soil-dark'
                }`}
              >
                <Icon className="w-5 h-5" strokeWidth={active ? 2.4 : 2} />
                {t(key)}
                <span
                  aria-hidden
                  className={`w-6 h-0.5 rounded-full transition-colors duration-200 ${
                    active ? 'bg-ochre' : 'bg-transparent'
                  }`}
                />
              </Link>
            )
          })}
        </div>
      </nav>
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
