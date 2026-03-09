import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from '@/api/client'
import { ScenarioProvider } from '@/context/ScenarioContext'
import { Layout } from '@/components/Layout'
import { WarMap } from '@/pages/WarMap'
import { GraphExplorer } from '@/pages/GraphExplorer'
import { ActorDashboard } from '@/pages/ActorDashboard'
import { EventLog } from '@/pages/EventLog'

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ScenarioProvider>
        <BrowserRouter>
          <Routes>
            <Route element={<Layout />}>
              <Route index element={<Navigate to="/map" replace />} />
              <Route path="/map" element={<WarMap />} />
              <Route path="/graph" element={<GraphExplorer />} />
              <Route path="/actors" element={<ActorDashboard />} />
              <Route path="/events" element={<EventLog />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </ScenarioProvider>
    </QueryClientProvider>
  )
}
