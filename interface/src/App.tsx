import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import WorkflowTrace from './pages/WorkflowTrace';
import Investigation from './pages/Investigation';
import './App.css';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/workflow" element={<WorkflowTrace />} />
        <Route path="/investigation" element={<Investigation />} />
        <Route path="*" element={<Dashboard />} />
      </Routes>
    </Router>
  );
}

export default App;
