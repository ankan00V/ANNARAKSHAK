import { useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { ChevronDown, LocateFixed } from 'lucide-react'
import { api } from '../api/client'
import type { Irrigation } from '../api/types'
import LanguagePicker from '../farmer/components/LanguagePicker'
import { useFarmer } from '../farmer/FarmerContext'
import { DISTRICTS } from '../lib/districts'
import { useAsync } from '../lib/hooks'
import { Card, Spinner } from '../ui/kit'
import { useAuth } from './AuthContext'
import { emailOk, phoneOk } from './helpers'
import { Chips, CodePanel, Field, Input, Primary, Secondary, Select, Steps } from './parts'

const IRRIGATION: Irrigation[] = ['rainfed', 'canal', 'borewell', 'open_well', 'farm_pond', 'drip', 'sprinkler']
const today = () => new Date().toISOString().slice(0, 10)

/** The district whose headquarters is nearest this point — one less question
 *  for a farmer standing in their field. */
function districtAt(lat: number, lon: number): string {
  const d2 = (d: (typeof DISTRICTS)[number]) => (d.lat - lat) ** 2 + ((d.lon - lon) * Math.cos((lat * Math.PI) / 180)) ** 2
  return DISTRICTS.reduce((best, d) => (d2(d) < d2(best) ? d : best)).name
}

/** Optional questions, folded away: a farmer should see a short form, and open
 *  this only if they have the details at hand. */
function MoreDetails({ open, onToggle, children }: { open: boolean; onToggle: () => void; children: ReactNode }) {
  const { t } = useFarmer()
  return (
    <div className="rounded-2xl border border-soil-dark/10 bg-white/60">
      <button type="button" onClick={onToggle}
        className="w-full flex items-center justify-between px-3 min-h-[48px] text-[13px] font-medium text-soil-dark/70">
        {open ? t('authMoreHide') : t('authMore')}
        <ChevronDown className={`w-4 h-4 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && <div className="px-3 pb-3 space-y-3">{children}</div>}
    </div>
  )
}

/** What a farmer is asked, and why: everything here drives their advice.
 *  Who they are and how to reach them; where the field is (weather, the
 *  district's disease history, the 5 km outbreak radius); the crop and sowing
 *  date (crop stage, which pests to watch for); area and water source (dose
 *  and irrigation advice); Soil Health Card pH when they have one. */
export default function SignupFarmer() {
  const { lang, setLang, t } = useFarmer()
  const { signIn } = useAuth()
  const crops = useAsync(() => api.crops(lang), [lang])
  const [step, setStep] = useState(0)
  const [f, setF] = useState(() => ({
    name: '', phone: '', email: '',
    district: 'Bhandara', taluka: '', village: '', totalLand: '',
    crop: 'rice', variety: '', sowing: new Date(Date.now() - 30 * 864e5).toISOString().slice(0, 10),
    area: '', irrigation: 'rainfed' as Irrigation, ph: '',
    consent: false,
  }))
  const [coords, setCoords] = useState<{ lat: number; lon: number } | null>(null)
  const [locating, setLocating] = useState(false)
  const [fromGps, setFromGps] = useState(false)
  const [more, setMore] = useState(false)
  const [touched, setTouched] = useState(false)
  const set = <K extends keyof typeof f>(k: K, v: (typeof f)[K]) => setF((x) => ({ ...x, [k]: v }))

  const bad = {
    name: f.name.trim().length < 2,
    phone: !phoneOk(f.phone),
    email: !emailOk(f.email),
    village: f.village.trim().length < 2,
    totalLand: f.totalLand !== '' && !(parseFloat(f.totalLand) > 0),
    area: !(parseFloat(f.area) > 0 && parseFloat(f.area) <= 1000),
    sowing: !f.sowing || f.sowing > today(),
    ph: f.ph !== '' && !(parseFloat(f.ph) >= 3 && parseFloat(f.ph) <= 11),
  }
  const stepOk = [
    !bad.name && !bad.phone && !bad.email,
    !bad.village && !bad.totalLand,
    !bad.area && !bad.sowing && !bad.ph,
    f.consent,
  ]
  const next = () => {
    setTouched(true)
    if (stepOk[step]) {
      setTouched(false)
      setStep((s) => s + 1)
      window.scrollTo(0, 0)
    }
  }
  const show = (k: keyof typeof bad) => touched && bad[k]

  const locate = () => {
    if (!navigator.geolocation) return
    setLocating(true)
    navigator.geolocation.getCurrentPosition(
      (p) => {
        const { latitude: lat, longitude: lon } = p.coords
        setCoords({ lat, lon })
        setF((x) => ({ ...x, district: districtAt(lat, lon) }))  // one less question
        setFromGps(true)
        setLocating(false)
      },
      () => setLocating(false),
      { timeout: 10000, enableHighAccuracy: true },
    )
  }

  const payload = () => {
    const d = DISTRICTS.find((x) => x.name === f.district)!
    return {
      name: f.name.trim(), phone: f.phone, lang, district: f.district, taluka: f.taluka.trim() || null,
      village: f.village.trim(), lat: coords?.lat ?? d.lat, lon: coords?.lon ?? d.lon,
      location_from_gps: coords != null,
      total_land_acres: f.totalLand ? parseFloat(f.totalLand) : null, consent: f.consent,
      farm: {
        crop: f.crop, variety: f.variety.trim() || null, sowing_date: f.sowing, area_acres: parseFloat(f.area),
        irrigation: f.irrigation, soil_ph: f.ph ? parseFloat(f.ph) : null,
      },
    }
  }

  const titles = [t('authFarmerStep1'), t('authFarmerStep2'), t('authFarmerStep3'), t('authFarmerStep4')]
  const cropName = crops.data?.find((c) => c.id === f.crop)?.name ?? f.crop
  const selectedCrop = crops.data?.find((c) => c.id === f.crop)

  return (
    <div>
      <Steps step={step} titles={titles} />

      {step === 0 && (
        <div className="space-y-4">
          <Field label={t('authName')} error={show('name') && t('authFixField')}>
            <Input value={f.name} onChange={(e) => set('name', e.target.value)} autoComplete="name" invalid={show('name')} />
          </Field>
          <Field label={t('authMobile')} hint={t('authMobileHint')} error={show('phone') && t('authBadPhone')}>
            <div className="flex gap-2">
              <span className="min-h-[48px] px-3 rounded-xl border border-soil-dark/20 bg-cream flex items-center text-[15px] text-soil-dark/60">+91</span>
              <Input value={f.phone} onChange={(e) => set('phone', e.target.value)} type="tel" inputMode="numeric"
                autoComplete="tel-national" maxLength={14} placeholder="98XXXXXXXX" invalid={show('phone')} />
            </div>
          </Field>
          <Field label={t('authEmail')} hint={t('authEmailHint')} error={show('email') && t('authBadEmail')}>
            <Input value={f.email} onChange={(e) => set('email', e.target.value)} type="email" autoComplete="email"
              inputMode="email" placeholder="name@gmail.com" invalid={show('email')} />
          </Field>
          <div>
            <p className="text-[13px] font-medium text-soil-dark/80 mb-2">{t('authLanguage')}</p>
            <LanguagePicker variant="grid" onPick={setLang} />
          </div>
        </div>
      )}

      {step === 1 && (
        <div className="space-y-4">
          <Field label={t('district')} hint={fromGps ? t('authDistrictFromGps') : undefined}>
            <Select value={f.district} onChange={(v) => { set('district', v); setFromGps(false) }}>
              {DISTRICTS.map((d) => <option key={d.name}>{d.name}</option>)}
            </Select>
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label={t('authTaluka')} optional>
              <Input value={f.taluka} onChange={(e) => set('taluka', e.target.value)} />
            </Field>
            <Field label={t('authVillage')} error={show('village') && t('authFixField')}>
              <Input value={f.village} onChange={(e) => set('village', e.target.value)} invalid={show('village')} />
            </Field>
          </div>
          <Card className="p-3">
            <button type="button" onClick={locate}
              className="w-full flex items-center gap-2 text-[14px] text-leaf-deep font-semibold min-h-[44px]">
              <LocateFixed className="w-5 h-5" />
              {locating ? t('locating') : coords
                ? `${t('locationSet')} (${coords.lat.toFixed(3)}, ${coords.lon.toFixed(3)})`
                : t('authAtField')}
            </button>
            <p className="text-[12px] text-soil-dark/55 leading-snug">{t('authFieldHint')}</p>
          </Card>
          <MoreDetails open={more} onToggle={() => setMore((m) => !m)}>
            <Field label={t('authTotalLand')} optional error={show('totalLand') && t('authFixField')}>
              <Input value={f.totalLand} onChange={(e) => set('totalLand', e.target.value)} type="number"
                inputMode="decimal" min="0.1" step="0.1" invalid={show('totalLand')} />
            </Field>
          </MoreDetails>
        </div>
      )}

      {step === 2 && (
        <div className="space-y-4">
          <p className="text-sm text-soil-dark/60 -mt-2">{t('authFirstField')}</p>
          {!crops.data ? <Spinner /> : (
            <Field group label={t('crop')}>
              <Chips columns={2} value={[f.crop]} onChange={([c]) => set('crop', c)}
                options={crops.data.map((c) => ({ id: c.id, label: c.name }))} />
            </Field>
          )}
          {selectedCrop && !selectedCrop.photo_diagnosis && (
            <p className="text-xs rounded-xl bg-sky-50 text-sky-800 p-2.5">{t('photoLater')}</p>
          )}
          <Field label={t('area')} error={show('area') && t('authFixField')}>
            <Input value={f.area} onChange={(e) => set('area', e.target.value)} type="number" inputMode="decimal"
              min="0.1" step="0.1" invalid={show('area')} />
          </Field>
          <Field label={t('sowingDate')} error={show('sowing') && t('authFixField')}>
            <Input value={f.sowing} onChange={(e) => set('sowing', e.target.value)} type="date" max={today()}
              invalid={show('sowing')} />
          </Field>
          <Field group label={t('authIrrigation')}>
            <Chips columns={2} value={[f.irrigation]} onChange={([v]) => set('irrigation', v)}
              options={IRRIGATION.map((id) => ({ id, label: t(`irr_${id}`) }))} />
          </Field>
          <MoreDetails open={more} onToggle={() => setMore((m) => !m)}>
            <Field label={t('authVariety')} optional>
              <Input value={f.variety} onChange={(e) => set('variety', e.target.value)} placeholder="Jaya, MTU 1010…" />
            </Field>
            <Field label={t('soilPhCard')} hint={t('soilPhCardHint')} error={show('ph') && t('authFixField')}>
              <Input value={f.ph} onChange={(e) => set('ph', e.target.value)} type="number" inputMode="decimal"
                min="3" max="11" step="0.1" placeholder="6.8" invalid={show('ph')} />
            </Field>
          </MoreDetails>
        </div>
      )}

      {step === 3 && (
        <div className="space-y-4">
          <Card className="p-4">
            <p className="text-[11px] uppercase tracking-wider text-soil-dark/50 font-semibold mb-2">{t('authReview')}</p>
            <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1.5 text-[13px]">
              <dt className="text-soil-dark/55">{t('authName')}</dt><dd className="font-medium">{f.name}</dd>
              <dt className="text-soil-dark/55">{t('authMobile')}</dt><dd>+91 {f.phone.replace(/\D/g, '').slice(-10)}</dd>
              <dt className="text-soil-dark/55">{t('authEmail')}</dt><dd className="break-all">{f.email.trim()}</dd>
              <dt className="text-soil-dark/55">{t('authVillage')}</dt>
              <dd>{[f.village, f.taluka, f.district].filter(Boolean).join(', ')}</dd>
              <dt className="text-soil-dark/55">{t('crop')}</dt>
              <dd>{cropName}{f.variety && ` (${f.variety})`} · {f.area} {t('acres')} · {t(`irr_${f.irrigation}`)}</dd>
              <dt className="text-soil-dark/55">{t('sowingDate')}</dt><dd>{f.sowing}</dd>
            </dl>
            <button type="button" onClick={() => setStep(0)} className="mt-3 text-[13px] text-leaf-deep font-medium">
              {t('authChange')}
            </button>
          </Card>
          <label className="flex gap-3 items-start rounded-2xl bg-white border border-soil-dark/10 p-3 cursor-pointer">
            <input type="checkbox" checked={f.consent} onChange={(e) => set('consent', e.target.checked)}
              className="mt-1 w-5 h-5 accent-leaf-deep shrink-0" />
            <span className="text-[13px] leading-snug text-soil-dark/80">{t('authConsent')}</span>
          </label>
          {f.consent && (
            <CodePanel
              sendLabel={t('authSendCodeTo').replace('{to}', f.email.trim())}
              request={() => api.requestOtp({ role: 'farmer', purpose: 'signup', email: f.email.trim(), phone: f.phone, lang })}
              verify={async (challenge_id, code) => signIn(await api.signupFarmer({ ...payload(), challenge_id, code }))}
              submitLabel={t('authCreate')}
            />
          )}
        </div>
      )}

      {step < 3 && (
        <div className="mt-6 flex gap-3">
          {step > 0 && <Secondary onClick={() => setStep((s) => s - 1)}>{t('back')}</Secondary>}
          <Primary onClick={next}>{t('authNext')}</Primary>
        </div>
      )}
      {step === 3 && (
        <div className="mt-4">
          <Secondary onClick={() => setStep(2)}>{t('back')}</Secondary>
        </div>
      )}

      <p className="mt-8 text-center text-sm text-soil-dark/70">
        {t('authHaveAccount')}{' '}
        <Link to="/login?role=farmer" className="text-leaf-deep font-semibold underline underline-offset-2">{t('authLogin')}</Link>
      </p>
    </div>
  )
}
