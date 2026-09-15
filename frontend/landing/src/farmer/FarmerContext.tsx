import { createContext, useContext, useMemo, useState, type ReactNode } from 'react'
import type { DiagnoseResult, Lang } from '../api/types'
import { makeT } from '../lib/i18n'
import { usePersistent } from '../lib/hooks'

interface FarmerState {
  lang: Lang
  setLang: (l: Lang) => void
  farmId: number | null
  setFarmId: (id: number | null) => void
  result: DiagnoseResult | null
  setResult: (r: DiagnoseResult | null) => void
  t: ReturnType<typeof makeT>
}

const Ctx = createContext<FarmerState | null>(null)

export function FarmerProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = usePersistent<Lang>('ar.lang', 'mr')
  const [farmId, setFarmId] = usePersistent<number | null>('ar.farm', null)
  const [result, setResult] = useState<DiagnoseResult | null>(null)
  const t = useMemo(() => makeT(lang), [lang])
  return (
    <Ctx.Provider value={{ lang, setLang, farmId, setFarmId, result, setResult, t }}>
      {children}
    </Ctx.Provider>
  )
}

export function useFarmer() {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useFarmer outside FarmerProvider')
  return ctx
}
