import type { Lang } from './FarmerContext'

// MOCK BACKEND — every function here stands in for a real API call.
// Swap the bodies with fetch() calls to the FastAPI backend; the shapes
// already match the planned endpoints, so no component code changes.

export interface RiskForecast {
  district: string
  crop: string
  level: 'low' | 'medium' | 'high'
}

export interface RecentDiagnosis {
  id: string
  disease: string
  date: string
  confidence: number
  thumb: string
}

export interface AdvisoryStep {
  step: string
}

export interface Diagnosis {
  disease: string
  crop: string
  confidence: number
  imageUrl: string
  heatmap: { top: number; left: number; size: number }
  flagged: boolean
  advisory: AdvisoryStep[]
}

export interface DosageResult {
  pesticide: string
  quantity: string
  costInr: number
}

export interface NearbyAlert {
  id: string
  disease: string
  distanceKm: number
  daysAgo: number
}

const FLAG_THRESHOLD = 70

const wait = (ms: number) => new Promise((r) => setTimeout(r, ms))

// GET /predict (multipart image) — picks a canned response, low-confidence
// every third scan so the expert-review path is demoable on demand.
export async function predictDisease(image: File, lang: Lang): Promise<Diagnosis> {
  await wait(900)

  // MOCK advisory content — real text comes from the ICAR knowledge base
  // translated via Bhashini later.
  const advisoryByLang: Record<Lang, AdvisoryStep[]> = {
    en: [
      { step: 'Remove and burn the visibly infected leaves. Do not compost them.' },
      { step: 'Spray Mancozeb 75 WP — 2.5 g per litre of water, early morning.' },
      { step: 'Repeat after 10 days. Keep the field free of standing water.' },
    ],
    hi: [
      { step: 'दिखाई दे रहे संक्रमित पत्ते तोड़कर जला दें। खाद में न डालें।' },
      { step: 'मैंकोजेब 75 WP छिड़काव करें — 2.5 ग्राम प्रति लीटर पानी, सुबह जल्दी।' },
      { step: '10 दिन बाद दोहराएं। खेत में पानी जमा न रहने दें।' },
    ],
    mr: [
      { step: 'दिसणारी संक्रमित पाने काढून जाळा. कंपोस्टमध्ये टाकू नका.' },
      { step: 'मॅन्कोझेब 75 WP फवारणी करा — 2.5 ग्रॅम प्रति लिटर पाणी, सकाळी लवकर.' },
      { step: '10 दिवसांनी पुन्हा करा. शेतात पाणी साचू देऊ नका.' },
    ],
  }

  const candidates = [
    { disease: 'Leaf Blight', crop: 'Rice' },
    { disease: 'Early Blight', crop: 'Tomato' },
    { disease: 'Powdery Mildew', crop: 'Wheat' },
  ]
  const pick = candidates[Math.floor(Math.random() * candidates.length)]
  const confidence = Math.round((62 + Math.random() * 33) * 10) / 10

  return {
    ...pick,
    confidence,
    imageUrl: URL.createObjectURL(image),
    heatmap: {
      top: 20 + Math.random() * 30,
      left: 15 + Math.random() * 40,
      size: 34 + Math.random() * 18,
    },
    flagged: confidence < FLAG_THRESHOLD,
    advisory: advisoryByLang[lang],
  }
}

// GET /risk-forecast?district=X&crop=Y
export async function getRiskForecast(_district: string, _crop: string): Promise<RiskForecast> {
  await wait(400)
  const levels: RiskForecast['level'][] = ['low', 'medium', 'high']
  return {
    district: 'Pune',
    crop: 'Cotton',
    level: levels[Math.floor(Math.random() * levels.length)],
  }
}

// GET /diagnoses/recent (per farmer)
export async function getRecentDiagnoses(): Promise<RecentDiagnosis[]> {
  await wait(300)
  // MOCK thumbnails — inline SVG placeholders so nothing is fetched.
  const svg = (c: string) =>
    `data:image/svg+xml,${encodeURIComponent(
      `<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96"><rect width="96" height="96" fill="${c}"/><circle cx="48" cy="48" r="20" fill="rgba(0,0,0,0.25)"/></svg>`,
    )}`
  return [
    { id: 'd1', disease: 'Leaf Blight', date: '10 Sep', confidence: 91.4, thumb: svg('#6b8f4e') },
    { id: 'd2', disease: 'Early Blight', date: '6 Sep', confidence: 88.2, thumb: svg('#8f7a4e') },
    { id: 'd3', disease: 'Powdery Mildew', date: '29 Aug', confidence: 64.8, thumb: svg('#96836b') },
  ]
}

// GET /dosage?disease=X&land=Y&unit=Z — rule-of-thumb table below is
// illustrative; the real endpoint computes from the ICAR dosage KB.
export async function getDosage(
  disease: string | null,
  land: number,
  unit: 'acres' | 'hectares',
): Promise<DosageResult> {
  await wait(500)
  const acres = unit === 'acres' ? land : land * 2.471
  const litresPerAcre = 200
  const concentration = 2.5 // g per litre, mocked per-disease entry
  const grams = acres * litresPerAcre * concentration
  const packets = Math.ceil(grams / 100)
  return {
    pesticide: disease ? `${disease} — Mancozeb 75 WP` : 'Mancozeb 75 WP',
    quantity: `${grams.toFixed(0)} g (~${packets} × 100 g pack${packets > 1 ? 's' : ''})`,
    costInr: packets * 210,
  }
}

// GET /alerts/nearby?lat=..&lon=..
export async function getNearbyAlerts(_location: {
  lat: number
  lon: number
}): Promise<NearbyAlert[]> {
  await wait(400)
  return [
    { id: 'a1', disease: 'Leaf Blight', distanceKm: 3.2, daysAgo: 1 },
    { id: 'a2', disease: 'Bollworm', distanceKm: 7.8, daysAgo: 2 },
    { id: 'a3', disease: 'Rust', distanceKm: 12.5, daysAgo: 4 },
  ]
}
