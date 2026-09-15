import { useState } from 'react'
import { Ban, BadgeCheck, BookOpen, ChevronDown, FlaskConical, Leaf, Phone, PhoneCall, ShieldAlert, Sprout } from 'lucide-react'
import type { Advisory, IcarTech, LadderRung } from '../../api/types'
import { ListenButton, Pill } from '../../ui/kit'
import { useFarmer } from '../FarmerContext'

const TIER = {
  cultural: { icon: Sprout, tone: 'bg-leaf/15 text-leaf-deep', key: 'cultural' },
  biological: { icon: Leaf, tone: 'bg-lime-100 text-lime-800', key: 'biological' },
  chemical: { icon: FlaskConical, tone: 'bg-ember/10 text-ember', key: 'chemical' },
}

/** The advisory in the order the product promises: what NOT to do first and
 *  loudest, then the ladder cultural → biological → chemical, with the
 *  chemical rung collapsed until the farmer asks for it. */
export default function AdvisoryView({ advisory }: { advisory: Advisory }) {
  const { t, lang } = useFarmer()
  const [showChem, setShowChem] = useState(false)
  const nonChem = advisory.ladder.filter((r) => r.tier !== 'chemical')
  const chem = advisory.ladder.filter((r) => r.tier === 'chemical')

  const speech = [
    advisory.name + '.',
    t('whatToAvoid') + ': ' + advisory.what_to_avoid.join(' '),
    t('whatToDo') + ': ' + nonChem.map((r) => r.action).join(' '),
    advisory.what_to_check,
  ].join(' ')

  return (
    <div className="space-y-4">
      <section className="rounded-2xl border-2 border-ember/40 bg-ember/5 p-4">
        <div className="flex items-center justify-between">
          <h2 className="flex items-center gap-2 text-sm font-bold uppercase tracking-wide text-ember">
            <Ban className="w-4 h-4" />
            {t('whatToAvoid')}
          </h2>
          <ListenButton text={speech} lang={lang} label={t('listen')} stopLabel={t('stop')} />
        </div>
        <ul className="mt-2 space-y-2">
          {advisory.what_to_avoid.map((a, i) => (
            <li key={i} className="text-[14px] leading-snug font-medium text-soil-dark flex gap-2">
              <span aria-hidden className="text-ember">✕</span>
              {a}
            </li>
          ))}
        </ul>
      </section>

      <section className="rounded-2xl bg-white border border-soil-dark/10 p-4">
        <h2 className="text-sm font-semibold">{t('whatToDo')}</h2>
        <p className="mt-1 text-xs text-soil-dark/60">{advisory.what_to_check}</p>
        <ol className="mt-3 space-y-3">
          {nonChem.map((r, i) => (
            <Rung key={i} rung={r} n={i + 1} />
          ))}
        </ol>

        {chem.length > 0 && (
          <div className="mt-4 border-t border-dashed border-soil-dark/15 pt-3">
            <p className="text-xs text-soil-dark/60">{t('chemicalLast')}</p>
            <button
              onClick={() => setShowChem((s) => !s)}
              className="mt-2 w-full min-h-[44px] rounded-xl border border-ember/30 text-ember text-sm font-medium flex items-center justify-center gap-2"
            >
              <FlaskConical className="w-4 h-4" />
              {showChem ? t('hideChemical') : t('showChemical')}
              <ChevronDown className={`w-4 h-4 transition-transform ${showChem ? 'rotate-180' : ''}`} />
            </button>
            {showChem && (
              <ol className="mt-3 space-y-3 animate-fadein">
                {chem.map((r, i) => (
                  <Rung key={i} rung={r} n={nonChem.length + i + 1} />
                ))}
              </ol>
            )}
          </div>
        )}
      </section>

      {advisory.icar_options?.length > 0 && (
        <section className="rounded-2xl bg-white border border-leaf/30 p-4">
          <h2 className="text-sm font-semibold flex items-center gap-1.5">
            <BadgeCheck className="w-4 h-4 text-leaf" />
            {t('icarTitle')}
          </h2>
          <p className="mt-1 text-xs text-soil-dark/60">{t('icarSub')}</p>
          <ul className="mt-3 space-y-3">
            {advisory.icar_options.map((o) => <IcarOption key={o.id} o={o} />)}
          </ul>
        </section>
      )}

      <section className="rounded-2xl bg-soil-dark text-cream p-4 flex gap-3">
        <PhoneCall className="w-5 h-5 text-ochre shrink-0 mt-0.5" />
        <div>
          <p className="text-xs uppercase tracking-wide text-cream/60">{t('expertTrigger')}</p>
          <p className="text-sm mt-0.5">{advisory.expert_trigger}</p>
          <a href="tel:18001801551" className="mt-2 inline-block text-xs text-ochre underline underline-offset-2">
            {t('callKcc')}
          </a>
        </div>
      </section>

      <details className="rounded-2xl bg-white/60 border border-soil-dark/10 p-3 text-xs">
        <summary className="cursor-pointer flex items-center gap-1.5 font-medium text-soil-dark/70">
          <BookOpen className="w-3.5 h-3.5" />
          {t('sources')} ({advisory.citations.length})
        </summary>
        <ul className="mt-2 space-y-1.5">
          {advisory.citations.map((c, i) => (
            <li key={i} className="text-soil-dark/70">
              <span className="font-medium text-soil-dark">{c.title}</span> — {c.publisher}
              {c.url && (
                <a href={c.url} target="_blank" rel="noreferrer" className="ml-1 text-leaf-deep underline">
                  {c.url.replace(/^https?:\/\//, '')}
                </a>
              )}
            </li>
          ))}
        </ul>
      </details>
    </div>
  )
}

function Rung({ rung, n }: { rung: LadderRung; n: number }) {
  const { t } = useFarmer()
  const tier = TIER[rung.tier]
  const Icon = tier.icon
  return (
    <li className="flex gap-3">
      <span className={`shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${tier.tone}`}>
        <Icon className="w-4 h-4" />
      </span>
      <div className="flex-1 min-w-0">
        <p className="text-[11px] font-semibold uppercase tracking-wide text-soil-dark/50">
          {n}. {t(tier.key)}
        </p>
        {rung.tier !== 'chemical' ? (
          <p className="text-[14px] leading-snug mt-0.5">{rung.action}</p>
        ) : (
          <div className="mt-0.5 space-y-1">
            <p className="text-[14px] font-semibold">{rung.product}</p>
            {rung.dose && <p className="text-[13px]">{rung.dose}</p>}
            {rung.for_field && (
              <p className="text-[13px] rounded-lg bg-cream px-2 py-1.5">
                <span className="font-medium">{t('doseForField')}: </span>
                {rung.for_field.replace(/^[^:]+:\s*/, '')}
              </p>
            )}
            {rung.timing && <p className="text-xs text-soil-dark/60">{rung.timing}</p>}
            <p className="text-xs flex items-start gap-1.5 text-soil-dark/70">
              <ShieldAlert className="w-3.5 h-3.5 text-ochre shrink-0 mt-px" />
              {rung.label_rule}
            </p>
            {!rung.verified && <Pill tone="ochre">{t('dosePending')}</Pill>}
          </div>
        )}
      </div>
    </li>
  )
}

const ICAR_TYPE_KEY = {
  biocontrol: 'icar_biocontrol',
  variety: 'icar_variety',
  practice: 'icar_practice',
  app: 'icar_app',
  monitoring: 'icar_monitoring',
  reference: 'icar_monitoring',
} as const

function IcarOption({ o }: { o: IcarTech }) {
  const { t } = useFarmer()
  return (
    <li className="rounded-xl bg-cream/60 p-3">
      <Pill tone="leaf" className="!text-[10px]">{t(ICAR_TYPE_KEY[o.type])}</Pill>
      <p className="mt-1.5 text-[14px] leading-snug">{o.summary}</p>
      {o.link_reason && (
        <p className="mt-1 text-xs text-soil-dark/70"><span className="font-medium">{t('icarWhy')}: </span>{o.link_reason}</p>
      )}
      {o.claim && (
        <p className="mt-1 text-xs text-leaf-deep"><span className="font-medium">{t('icarResult')}: </span>{o.claim}</p>
      )}
      {o.supply && (
        <p className="mt-1 text-xs text-soil-dark/70"><span className="font-medium">{t('icarSupply')}: </span>{o.supply}</p>
      )}
      <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-soil-dark/60">
        <span>{o.institute.name}, {o.institute.city}</span>
        {o.institute.phone && (
          <a href={`tel:${o.institute.phone.replace(/[^0-9+]/g, '')}`} className="inline-flex items-center gap-1 text-leaf-deep font-medium">
            <Phone className="w-3 h-3" /> {t('icarCall')} {o.institute.phone}
          </a>
        )}
        {o.lead_time_days && <Pill tone="ochre" className="!text-[10px]">{t('icarLead').replace('{n}', String(o.lead_time_days))}</Pill>}
      </div>
    </li>
  )
}
