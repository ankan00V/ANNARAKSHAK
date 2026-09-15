import { BellRing, Camera, HelpCircle, Sprout, UserCheck } from 'lucide-react'

const STEPS = [
  { icon: BellRing, label: 'Alert', line: 'Weather, crop stage, traps and nearby cases say where to look — before damage shows.' },
  { icon: Camera, label: 'Photo', line: 'The AI names the disease or pest and shows where it looked.' },
  { icon: HelpCircle, label: 'Ask or escalate', line: 'Torn between two? One field question. Unsure? A KVK expert, not a guess.' },
  { icon: Sprout, label: 'Act', line: 'Safest steps first, a dose for your field, and a spray check before you buy.' },
  { icon: UserCheck, label: 'Follow up', line: 'Day 4 check-in. Confirmed cases warn neighbours and teach the system.' },
]

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="w-full bg-leaf-deep text-cream">
      <div className="max-w-6xl mx-auto px-6 md:px-12 py-16 md:py-24">
        <h2 className="font-instrument-serif text-3xl sm:text-4xl md:text-5xl leading-tight max-w-3xl">
          From an early warning to a checked treatment.
        </h2>
        <div className="mt-12 grid gap-10 md:grid-cols-5 md:gap-6">
          {STEPS.map(({ icon: Icon, label, line }, i) => (
            <div
              key={label}
              className="relative flex md:flex-col items-start md:items-center md:text-center gap-5 md:gap-0"
            >
              {i < STEPS.length - 1 && (
                <div
                  aria-hidden
                  className="hidden md:block absolute top-7 left-1/2 w-full h-px bg-cream/20"
                />
              )}
              <div className="relative z-10 flex items-center justify-center w-14 h-14 rounded-full border border-cream/30 bg-leaf-deep shrink-0">
                <Icon className="w-6 h-6 text-ochre" />
              </div>
              <div className="md:mt-5">
                <div className="flex md:flex-col md:items-center items-baseline gap-3 md:gap-1">
                  <span className="text-xs font-medium tracking-widest text-ochre">
                    0{i + 1}
                  </span>
                  <h3 className="text-lg font-medium">{label}</h3>
                </div>
                <p className="mt-2 text-sm font-light leading-relaxed text-cream/70">{line}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
