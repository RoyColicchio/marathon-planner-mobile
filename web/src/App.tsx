import { Routes, Route, Navigate } from 'react-router-dom'
import HomeScreen from './screens/HomeScreen'
import SettingsScreen from './screens/SettingsScreen'
import WorkoutDetailScreen from './screens/WorkoutDetailScreen'
import StravaCallback from './screens/StravaCallback'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomeScreen />} />
      <Route path="/settings" element={<SettingsScreen />} />
      <Route path="/workout/:date" element={<WorkoutDetailScreen />} />
      <Route path="/auth/callback" element={<StravaCallback />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
