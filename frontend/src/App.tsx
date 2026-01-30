import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/layout/ProtectedRoute';
import { Auth } from './pages/Auth';
import { Dashboard } from './pages/Dashboard';
import { Lobby } from './pages/Lobby'; // Will refactor later
import { Interview } from './pages/Interview'; // Will refactor later
import { Report } from './pages/Report'; // Will refactor later

// Placeholder for Landing
const Landing = () => <Navigate to="/auth" />;

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/auth" element={<Auth />} />

        {/* Protected Routes */}
        <Route element={<ProtectedRoute />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/lobby" element={<Lobby />} />
          <Route path="/interview/:sessionId" element={<Interview />} />
          <Route path="/report/:sessionId" element={<Report />} />
        </Route>
      </Routes>
    </AuthProvider>
  );
}

export default App;
