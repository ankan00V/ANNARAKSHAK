const FARMER_POINTS = [
  'Know where to look before symptoms spread, from your own weather and crop stage.',
  'Fewer wasted sprays — wrong-class, wrong-crop and weed-killer sprays are stopped.',
  'Advice in Marathi or Hindi, heard out loud, not just read.',
  'An honest “I’m not sure” and a real expert, instead of a confident wrong answer.',
]

const OFFICIAL_POINTS = [
  'Hotspots from expert-confirmed cases, not rumours — with a 5 km spread radius.',
  'A validation queue that measures field accuracy instead of trusting the model.',
  'A weekly risk outlook by pest and district to plan preventive interventions.',
  'IMD rainfall against normal and the state pesticide-use baseline on one screen.',
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
