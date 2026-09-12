import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import Landing from './Landing'
import FarmerApp from './farmer/FarmerApp'
import Home from './farmer/screens/Home'
import Result from './farmer/screens/Result'
import Dosage from './farmer/screens/Dosage'
import Alerts from './farmer/screens/Alerts'
import { OfficerStub } from './pages/Stubs'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/app" element={<FarmerApp />}>
          <Route index element={<Home />} />
          <Route path="result" element={<Result />} />
          <Route path="dosage" element={<Dosage />} />
          <Route path="alerts" element={<Alerts />} />
        </Route>
        <Route path="/officer" element={<OfficerStub />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
