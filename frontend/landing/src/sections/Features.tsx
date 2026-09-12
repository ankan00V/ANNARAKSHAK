import { Bell, Calculator, Languages, MessageSquare, UserCheck, ZoomIn } from 'lucide-react'

const FEATURES = [
  {
    icon: Languages,
    title: 'Multilingual Voice',
    line: 'Ask questions and hear advisories in Hindi, Marathi, or English.',
  },
  {
    icon: MessageSquare,
    title: 'Works Without a Smartphone',
    line: 'SMS and call-based support reach farmers on any phone, on any network.',
  },
  {
    icon: ZoomIn,
    title: 'Explainable Diagnosis',
    line: 'See exactly what the AI noticed on the leaf before you trust it.',
  },
  {
    icon: Bell,
    title: 'Nearby Outbreak Alerts',
    line: 'Know when disease is spreading in fields around you, not just your own.',
  },
  {
    icon: Calculator,
    title: 'Dosage Calculator',
    line: 'The right amount of pesticide for your land — nothing wasted, nothing extra.',
  },
  {
    icon: UserCheck,
    title: 'Officer Validation',
    line: 'Every uncertain case is reviewed by a real expert, not left to the model.',
  },
]

export default function Features() {
  return (
    <section id="features" className="w-full bg-cream text-soil-dark">
      <div className="max-w-6xl mx-auto px-6 md:px-12 py-16 md:py-24">
        <h2 className="font-instrument-serif text-3xl sm:text-4xl md:text-5xl leading-tight max-w-3xl">
          Built for how farmers actually work.
        </h2>
        <div className="mt-10 md:mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map(({ icon: Icon, title, line }) => (
            <div key={title} className="rounded-2xl border border-soil-dark/10 bg-white/70 p-6">
              <Icon className="w-6 h-6 text-leaf" />
              <h3 className="mt-4 text-base font-medium">{title}</h3>
              <p className="mt-2 text-sm font-light leading-relaxed text-soil-dark/70">{line}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
