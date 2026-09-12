import type { ReactNode } from 'react'
import { createContext, useContext, useState } from 'react'
import type { Diagnosis } from './mockApi'

export type Lang = 'hi' | 'mr' | 'en'

interface FarmerState {
  lang: Lang
  setLang: (l: Lang) => void
  diagnosis: Diagnosis | null
  setDiagnosis: (d: Diagnosis) => void
}

const FarmerContext = createContext<FarmerState | null>(null)

export function FarmerProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>('en')
  const [diagnosis, setDiagnosis] = useState<Diagnosis | null>(null)
  return (
    <FarmerContext.Provider value={{ lang, setLang, diagnosis, setDiagnosis }}>
      {children}
    </FarmerContext.Provider>
  )
}

export function useFarmer() {
  const ctx = useContext(FarmerContext)
  if (!ctx) throw new Error('useFarmer outside FarmerProvider')
  return ctx
}
