import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';

import Home from './components/Home';
import ImportForm from './components/ImportForm';
import Layout from './components/Layout';
import RatiosCharts from './components/RatiosCharts';
import Visuales from './pages/Visuales';

const TemporaryDisabledPage = () => (
  <div className="mx-auto max-w-3xl space-y-4 rounded-lg border border-[#E0D5C7] bg-white p-8">
    <h1 className="text-3xl font-serif text-primary">Vista temporalmente desactivada</h1>
    <p className="text-sm text-accent">
      Esta superficie no forma parte del MVP visual actual en produccion.
    </p>
    <p className="text-sm text-accent">
      La demo activa y fiable esta en <strong>/visuales</strong>, con las tabs de <strong>Rango</strong>{' '}
      y <strong>Solidez</strong>.
    </p>
  </div>
);

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/import" element={<ImportForm />} />
          <Route path="/master" element={<TemporaryDisabledPage />} />
          <Route path="/archived" element={<TemporaryDisabledPage />} />
          <Route path="/ratios" element={<Visuales />} />
          <Route path="/visuales" element={<Visuales />} />
          <Route path="/ratios/charts" element={<RatiosCharts />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
