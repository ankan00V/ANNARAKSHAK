import { Link } from 'react-router-dom'

export default function StubPage({
  title,
  subtitle,
  note,
}: {
  title: string
  subtitle: string
  note: string
}) {
  return (
    <div className="min-h-screen w-full bg-leaf-deep text-cream flex flex-col items-center justify-center px-6 text-center">
      <h1 className="font-instrument-serif text-4xl sm:text-5xl">{title}</h1>
      <p className="mt-4 max-w-md text-sm md:text-base font-light text-cream/70">{subtitle}</p>
      <p className="mt-2 max-w-md text-xs font-light text-cream/40">{note}</p>
      <Link
        to="/"
        className="mt-8 border border-cream/40 hover:bg-cream/10 rounded-full px-6 py-2.5 text-sm font-light transition-colors"
      >
        Back to the story
      </Link>
    </div>
  )
}
