import React, { createContext, useContext, useState } from 'react'

interface ScenarioCtx {
  scenarioId: string
  setScenarioId: (id: string) => void
}

const ScenarioContext = createContext<ScenarioCtx>({
  scenarioId: 'production',
  setScenarioId: () => {},
})

export function ScenarioProvider({ children }: { children: React.ReactNode }) {
  const [scenarioId, setScenarioId] = useState('production')
  return (
    <ScenarioContext.Provider value={{ scenarioId, setScenarioId }}>
      {children}
    </ScenarioContext.Provider>
  )
}

export const useScenario = () => useContext(ScenarioContext)
