// The app tour, step by step. Each step points at an element tagged
// data-tour="<target>" (none: a centred card), shows tour_<id>_t / tour_<id>_b
// and plays public/tour/<lang>/<id>.mp3 (backend/make_tour_audio.py — keep
// the ids in step with its STEPS).
//
// `tap`: the farmer may tap the real thing and the tour goes on from there
// (Spray check and Alerts open their screens). Cards on Home are shown, not
// opened, so a stray tap never takes the tour off the page it is explaining.

export interface TourStep {
  id: string
  target?: string
  side?: 'top' | 'right' | 'bottom' | 'left'
  tap?: boolean
}

export const TOUR_STEPS: TourStep[] = [
  { id: 'welcome' },
  { id: 'farm', target: 'farm', side: 'bottom' },
  { id: 'weather', target: 'weather', side: 'bottom' },
  { id: 'live', target: 'live', side: 'top' },
  { id: 'scan', target: 'scan', side: 'top' },
  { id: 'checks', target: 'checks', side: 'top' },
  { id: 'spray', target: 'nav-spray', tap: true },
  { id: 'alerts', target: 'nav-alerts', tap: true },
  { id: 'krishi', target: 'krishi', side: 'left' },
  { id: 'lang', target: 'lang', side: 'bottom' },
  { id: 'done' },
]

/** Seen or dismissed on this device: the invite is not offered again. */
export const TOUR_SEEN_KEY = 'ar.tour.v1'
export const TOUR_MUTED_KEY = 'ar.tour.muted'
