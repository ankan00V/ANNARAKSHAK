import { Clock, IndianRupee, Users } from 'lucide-react'

const CARDS = [
  {
    icon: Clock,
    title: 'Late Detection',
    line: 'By the time symptoms are obvious, the infection has been spreading for days — and every hour narrows the window where treatment is still cheap and effective.',
  },
  {
    icon: Users,
    title: 'Thin Coverage',
    line: 'Extension officers are responsible for far more fields than they can physically visit, so most crops get expert eyes only after damage is already visible.',
  },
  {
    icon: IndianRupee,
    title: 'Costly Missteps',
    line: 'Guessing the wrong disease means spraying the wrong chemical — money spent, residues left on the field, and the actual problem still growing.',
  },
]

export default function Problem() {
  return (
    <section id="problem" className="w-full bg-cream text-soil-dark">
      <div className="max-w-6xl mx-auto px-6 md:px-12 py-16 md:py-24">
        <h2 className="font-instrument-serif text-3xl sm:text-4xl md:text-5xl leading-tight max-w-3xl">
          By the time you see it, it&apos;s already spreading.
        </h2>
        <p className="mt-5 max-w-2xl text-sm md:text-base font-light leading-relaxed text-soil-dark/80">
          Crop diseases and pests announce themselves quietly, then move fast. Extension staff
          cover huge areas and can&apos;t reach every field in time, and a wrong guess at the
          spray shop costs a farmer twice — once in chemicals, again in lost yield.
        </p>
        <div className="mt-10 md:mt-12 grid gap-5 md:grid-cols-3">
          {CARDS.map(({ icon: Icon, title, line }) => (
            <div key={title} className="rounded-2xl border border-soil-dark/10 bg-white/70 p-6">
              <Icon className="w-6 h-6 text-ochre" />
              <h3 className="mt-4 text-base font-medium">{title}</h3>
              <p className="mt-2 text-sm font-light leading-relaxed text-soil-dark/70">{line}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
