import type {
  AlertView,
  CaseBundle,
  CaseListItem,
  ClarifyResult,
  CropInfo,
  DiagnoseResult,
  Farm,
  Home,
  Hotspots,
  LabelVerdict,
  Lang,
  ModelCard,
  OutlookRow,
  PesticideBaseline,
  ProblemView,
  RainfallPanel,
  Summary,
  TargetView,
  TrapReading,
} from './types'

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response
  try {
    res = await fetch(path, init)
  } catch {
    throw new ApiError(0, 'offline')
  }
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, detail)
  }
  return res.json() as Promise<T>
}

const json = (body: unknown): RequestInit => ({
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
})

export const api = {
  health: () => req<{ status: string; model: { is_stub: boolean }; voice: { configured: boolean } }>('/health'),

  crops: (lang: Lang) => req<CropInfo[]>(`/api/kb/crops?lang=${lang}`),
  targets: (lang: Lang, crop?: string) =>
    req<TargetView[]>(`/api/kb/targets?lang=${lang}${crop ? `&crop=${crop}` : ''}`),
  pesticides: () => req<{ id: string; name: string; class: string }[]>('/api/kb/pesticides'),

  samples: (crop: string) => req<{ url: string; true_class: string; expected: 'advise' | 'clarify' | 'escalate' | 'retake' | null }[]>(`/api/samples?crop=${crop}`),
  farms: (lang: Lang) => req<Farm[]>(`/api/farms?lang=${lang}`),
  createFarm: (body: Record<string, unknown>) => req<Farm>('/api/farms', json(body)),
  home: (farmId: number, lang: Lang) => req<Home>(`/api/farms/${farmId}/home?lang=${lang}`),

  diagnose: (farmId: number, image: Blob, lang: Lang, scenario?: string) => {
    const fd = new FormData()
    fd.append('image', image, 'photo.jpg')
    fd.append('lang', lang)
    if (scenario) fd.append('demo_scenario', scenario)
    return req<DiagnoseResult>(`/api/farms/${farmId}/diagnose`, { method: 'POST', body: fd })
  },
  clarify: (problemId: number, cueId: string, answer: 'yes' | 'no' | 'unknown', lang: Lang) =>
    req<ClarifyResult>(`/api/problems/${problemId}/clarify`, json({ cue_id: cueId, answer, lang })),
  escalate: (problemId: number, lang: Lang) =>
    req<{ case: CaseListItem; message: string }>(`/api/problems/${problemId}/escalate?lang=${lang}`, {
      method: 'POST',
    }),
  problem: (problemId: number, lang: Lang) => req<ProblemView>(`/api/problems/${problemId}?lang=${lang}`),
  followup: (id: number, response: 'improved' | 'no_change' | 'got_worse', lang: Lang) =>
    req<{ case?: CaseListItem; message?: string }>(`/api/followups/${id}`, json({ response, lang })),

  alerts: (farmId: number, lang: Lang) => req<AlertView[]>(`/api/farms/${farmId}/alerts?lang=${lang}`),
  alertOutcome: (id: number, outcome: 'nothing_found' | 'found' | 'snoozed', lang: Lang) =>
    req<{ case?: CaseListItem; message?: string; problem_id?: number }>(
      `/api/alerts/${id}/outcome`,
      json({ outcome, lang }),
    ),
  runRisk: (farmId: number) => req<{ issued: number[] }>(`/api/farms/${farmId}/risk/run`, { method: 'POST' }),

  traps: (farmId: number) => req<TrapReading[]>(`/api/farms/${farmId}/traps`),
  addTrap: (farmId: number, body: Record<string, unknown>) =>
    req<{ issued: number[]; fired: { target: string; trigger: string; level: string }[] }>(
      `/api/farms/${farmId}/traps`,
      json(body),
    ),

  labelCheck: (farmId: number, product: string, lang: Lang, problemId?: number) =>
    req<LabelVerdict>('/api/labelcheck', json({ farm_id: farmId, product, lang, problem_id: problemId })),

  cases: (status: 'open' | 'resolved' | 'all' = 'open') => req<CaseListItem[]>(`/api/cases?status=${status}`),
  caseBundle: (id: number) => req<CaseBundle>(`/api/cases/${id}`),
  resolveCase: (id: number, body: Record<string, unknown>) =>
    req<{ verdict: string; final_label: string; model_label: string | null; spread_alerts: number }>(
      `/api/cases/${id}/resolve`,
      json(body),
    ),

  summary: () => req<Summary>('/api/officials/summary'),
  hotspots: () => req<Hotspots>('/api/officials/hotspots'),
  rainfall: () => req<RainfallPanel>('/api/officials/rainfall'),
  modelCard: () => req<ModelCard>('/api/officials/model'),
  pesticideBaseline: () => req<PesticideBaseline>('/api/officials/pesticides'),
  outlook: () => req<OutlookRow[]>('/api/officials/outlook'),
  addSensor: (farmId: number, readings: Record<string, unknown>[]) =>
    req<{ stored: number }>(`/api/farms/${farmId}/sensor`, json(readings)),
  runAll: () =>
    req<{ farms: number; alerts_issued: number; weather_sources: Record<string, number> }>(
      '/api/officials/risk/run-all',
      { method: 'POST' },
    ),

  tts: async (text: string, lang: Lang): Promise<Blob> => {
    const res = await fetch('/api/voice/tts', json({ text, lang }))
    if (!res.ok) throw new ApiError(res.status, 'tts failed')
    return res.blob()
  },
  stt: (audio: Blob, lang: Lang) => {
    const fd = new FormData()
    fd.append('audio', audio, 'speech.webm')
    fd.append('lang', lang)
    return req<{ transcript: string }>('/api/voice/stt', { method: 'POST', body: fd })
  },
}
