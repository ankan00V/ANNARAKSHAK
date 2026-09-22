import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { driver, type Driver, type DriveStep } from 'driver.js'
import 'driver.js/dist/driver.css'
import './tour.css'
import { Headphones, X } from 'lucide-react'
import { useFarmer } from '../FarmerContext'
import { TOUR_MUTED_KEY, TOUR_SEEN_KEY, TOUR_STEPS } from './steps'

// The spoken app tour. driver.js draws the spotlight and the card; this adds
// the voice — one clip per step in the farmer's language (public/tour, made by
// backend/make_tour_audio.py) — and the Home-first routing.

const store = {
  get: (k: string) => { try { return localStorage.getItem(k) } catch { return null } },
  set: (k: string, v: string) => { try { localStorage.setItem(k, v) } catch { /* private mode */ } },
}

const Ctx = createContext<{ start: () => void }>({ start: () => undefined })
export const useTour = () => useContext(Ctx)

export function TourProvider({ children }: { children: ReactNode }) {
  const { t, lang } = useFarmer()
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const tour = useRef<Driver | null>(null)
  // One audio element for the whole tour: it is first played inside the tap
  // that started the tour, which is what lets phones (iOS above all) keep
  // playing each next clip without a fresh tap.
  const audio = useRef<HTMLAudioElement | null>(null)
  const muted = useRef(store.get(TOUR_MUTED_KEY) === '1')
  const where = useRef(pathname)
  useEffect(() => { where.current = pathname }, [pathname])

  const play = useCallback((id: string) => {
    const a = audio.current
    if (!a) return
    a.pause()
    a.src = `/tour/${lang}/${id}.mp3`
    if (!muted.current) void a.play().catch(() => undefined)
  }, [lang])

  const start = useCallback(() => {
    store.set(TOUR_SEEN_KEY, '1')
    tour.current?.destroy()
    audio.current ??= new Audio()
    audio.current.src = `/tour/${lang}/welcome.mp3`
    if (!muted.current) void audio.current.play().catch(() => undefined)

    const steps: DriveStep[] = TOUR_STEPS.map((s) => ({
      element: s.target ? `[data-tour="${s.target}"]` : undefined,
      waitForElement: s.target ? 5000 : undefined,
      skipMissingElement: true, // a card that is not on screen (no weather yet) is skipped, not waited on forever
      disableActiveInteraction: !s.tap,
      advanceOnClick: Boolean(s.tap),
      data: { id: s.id },
      popover: { title: t(`tour_${s.id}_t`), description: t(`tour_${s.id}_b`), side: s.side, align: 'center' },
    }))

    const renderAudio = (footer: HTMLElement, id: string) => {
      const bar = document.createElement('div')
      bar.className = 'ar-tour-audio'
      const sound = document.createElement('button')
      const replay = document.createElement('button')
      const label = () => {
        sound.textContent = muted.current ? t('tourUnmute') : t('tourMute')
        sound.classList.toggle('ar-tour-playing', !muted.current)
        sound.setAttribute('aria-pressed', String(muted.current))
      }
      label()
      sound.onclick = () => {
        muted.current = !muted.current
        store.set(TOUR_MUTED_KEY, muted.current ? '1' : '0')
        if (muted.current) audio.current?.pause()
        else play(id)
        label()
      }
      replay.textContent = t('tourReplay')
      replay.onclick = () => {
        if (muted.current) { muted.current = false; store.set(TOUR_MUTED_KEY, '0'); label() }
        play(id)
      }
      bar.append(sound, replay)
      footer.prepend(bar)
    }

    const run = () => {
      tour.current = driver({
        steps,
        showProgress: true,
        progressText: t('tourProgress').replace('{n}', '{{current}}').replace('{total}', '{{total}}'),
        nextBtnText: `${t('tourNext')} →`,
        prevBtnText: `← ${t('tourBack')}`,
        doneBtnText: t('tourDone'),
        popoverClass: 'ar-tour',
        overlayColor: '#1b140d',
        overlayOpacity: 0.62,
        stagePadding: 6,
        stageRadius: 18,
        smoothScroll: true,
        allowClose: true,
        onHighlighted: (_el, step) => play(String(step.data?.id)),
        onPopoverRender: (pop, { index }) => renderAudio(pop.footer, TOUR_STEPS[index ?? 0]?.id ?? 'welcome'),
        onDestroyed: () => audio.current?.pause(),
      })
      tour.current.drive()
    }
    // The tour explains Home first: open it, then start once it has drawn.
    if (where.current !== '/app' && where.current !== '/app/') {
      navigate('/app')
      window.setTimeout(run, 350)
    } else run()
  }, [lang, navigate, play, t])

  useEffect(() => () => { tour.current?.destroy(); audio.current?.pause() }, [])

  return <Ctx.Provider value={{ start }}>{children}</Ctx.Provider>
}

/** On Home, until the farmer has taken or declined the tour on this device. */
export function TourInvite() {
  const { t } = useFarmer()
  const { start } = useTour()
  const [open, setOpen] = useState(() => store.get(TOUR_SEEN_KEY) !== '1')
  if (!open) return null
  const later = () => {
    store.set(TOUR_SEEN_KEY, '1')
    setOpen(false)
  }
  return (
    <section className="relative rounded-3xl bg-leaf-deep text-cream p-5 overflow-hidden animate-fadein" aria-label={t('tourInviteTitle')}>
      <span aria-hidden className="absolute -right-10 -top-12 w-40 h-40 rounded-full bg-ochre/25 blur-2xl" />
      <button onClick={later} aria-label={t('tourLater')} className="absolute top-3 right-3 w-8 h-8 rounded-full hover:bg-cream/10 flex items-center justify-center text-cream/70">
        <X className="w-4 h-4" />
      </button>
      <div className="relative flex items-start gap-4 pr-6">
        <span className="shrink-0 w-12 h-12 rounded-2xl bg-cream/10 ring-1 ring-ochre/50 flex items-center justify-center">
          <Headphones className="w-6 h-6 text-ochre" />
        </span>
        <div>
          <h2 className="text-lg font-semibold leading-snug">{t('tourInviteTitle')}</h2>
          <p className="mt-1 text-sm text-cream/75 leading-snug">{t('tourInviteBody')}</p>
        </div>
      </div>
      <div className="relative mt-4 flex gap-2">
        <button onClick={() => { setOpen(false); start() }}
          className="flex-1 min-h-[46px] rounded-full bg-ochre text-soil-dark text-sm font-semibold hover:brightness-105">
          {t('tourStart')}
        </button>
        <button onClick={later} className="min-h-[46px] px-5 rounded-full border border-cream/25 text-sm font-medium hover:bg-cream/10">
          {t('tourLater')}
        </button>
      </div>
    </section>
  )
}
