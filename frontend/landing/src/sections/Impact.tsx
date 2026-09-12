const FARMER_POINTS = [
  'Act the same day symptoms appear, not weeks later.',
  'Safer pesticide use — the right chemical, at the right dose.',
  'Advice in your own language, heard out loud, not just read.',
  'No waiting on a lab result before starting treatment.',
]

const OFFICIAL_POINTS = [
  'District-wide visibility into outbreaks as they emerge.',
  'A validation queue instead of blind trust in AI outputs.',
  'Better planning for preventive response and surveillance.',
]

function PointList({ points, dotClass }: { points: string[]; dotClass: string }) {
  return (
    <ul className="mt-6 space-y-3">
      {points.map((point) => (
        <li key={point} className="flex gap-3 text-sm md:text-base font-light text-cream/80">
          <span aria-hidden className={`mt-[9px] w-1.5 h-1.5 rounded-full shrink-0 ${dotClass}`} />
          {point}
        </li>
      ))}
    </ul>
  )
}

export default function Impact() {
  return (
    <section id="impact" className="w-full bg-soil-dark text-cream">
      <div className="max-w-6xl mx-auto px-6 md:px-12 py-16 md:py-24 grid gap-12 md:grid-cols-2">
        <div>
          <h2 className="font-instrument-serif text-3xl sm:text-4xl md:text-5xl">For Farmers</h2>
          <PointList points={FARMER_POINTS} dotClass="bg-ochre" />
        </div>
        <div id="for-officials" className="scroll-mt-24">
          <h2 className="font-instrument-serif text-3xl sm:text-4xl md:text-5xl">
            For Officials
          </h2>
          <PointList points={OFFICIAL_POINTS} dotClass="bg-cream/60" />
        </div>
      </div>
    </section>
  )
}
