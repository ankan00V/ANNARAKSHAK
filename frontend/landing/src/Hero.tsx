import { Link } from 'react-router-dom'
import { ArrowRight, Play } from 'lucide-react'
import Navbar from './Navbar'
import { smoothScrollTo } from './smoothScroll'

export default function Hero() {
  return (
    <section className="w-full h-screen overflow-hidden relative">
      <video
        className="absolute inset-0 w-full h-full object-cover"
        src="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260622_204103_f607742e-09da-4cf5-bb06-4e67b0a531de.mp4"
        autoPlay
        muted
        loop
        playsInline
      />

      <div className="relative z-10 flex flex-col h-full">
        <Navbar />

        <div className="flex-1 flex flex-col items-center justify-start pt-4 sm:pt-6 md:pt-8 lg:pt-10 px-6 text-center">
          <h1 className="font-instrument-serif text-white text-3xl sm:text-4xl md:text-5xl lg:text-6xl xl:text-7xl leading-[1.1] max-w-5xl">
            CROP <span className="italic font-instrument-serif">and</span> PEST
            <br />
            DETECTION <span className="italic font-instrument-serif">for</span> EVERY
            <br />
            FARMER
          </h1>
          <p className="mt-4 md:mt-5 text-white/70 text-sm md:text-base font-light max-w-md leading-relaxed">
            We help farmers catch crop disease and pest damage early
            <br className="hidden sm:block" /> and protect every harvest before it&apos;s too
            late.
          </p>
          <div className="mt-5 md:mt-6 flex flex-col sm:flex-row items-center gap-4">
            <Link
              to="/app"
              className="group bg-white text-black rounded-full px-7 py-3 text-sm font-medium"
            >
              <span className="inline-flex items-center gap-2">
                See It Detect
                <ArrowRight className="w-4 h-4 transition-transform duration-200 group-hover:translate-x-0.5" />
              </span>
            </Link>
            {/* demo footage not shot yet — swap this scroll for a modal with the
                embedded demo video once it exists */}
            <button
              onClick={() => smoothScrollTo('how-it-works')}
              className="bg-transparent border border-white/40 text-white rounded-full px-7 py-3 text-sm font-light hover:bg-white/10 hover:border-white/60 transition-colors duration-200"
            >
              <span className="inline-flex items-center gap-2">
                <Play className="w-4 h-4" />
                Watch Demo
              </span>
            </button>
          </div>
        </div>
      </div>
    </section>
  )
}
