import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';

import ArchivedList from './components/ArchivedList';
import Home from './components/Home';
import ImportForm from './components/ImportForm';
import Layout from './components/Layout';
import MasterTable from './components/MasterTable';
import RatiosCharts from './components/RatiosCharts';
import Visuales from './pages/Visuales';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/import" element={<ImportForm />} />
          <Route path="/master" element={<MasterTable />} />
          <Route path="/archived" element={<ArchivedList />} />
          <Route path="/ratios" element={<Visuales />} />
          <Route path="/visuales" element={<Visuales />} />
          <Route path="/ratios/charts" element={<RatiosCharts />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
