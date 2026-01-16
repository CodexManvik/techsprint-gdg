import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ErrorBoundary } from './components/shared/ErrorBoundary';
import { Home } from './pages/Home';
import { Lobby } from './pages/Lobby';
import { Interview } from './pages/Interview';
import { Report } from './pages/Report';

function App() {
  return (
    <ErrorBoundary>
      <Router>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/lobby" element={<Lobby />} />
          <Route path="/interview" element={<Interview />} />
          <Route path="/report" element={<Report />} />
        </Routes>
      </Router>
    </ErrorBoundary>
  );
}

export default App;
