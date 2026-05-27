import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './components/Home';

import ImportForm from './components/ImportForm';
import MasterTable from './components/MasterTable';
import ArchivedList from './components/ArchivedList';
import RatiosCharts from './components/RatiosCharts';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/import" element={<ImportForm />} />
          <Route path="/master" element={<MasterTable />} />
          <Route path="/archived" element={<ArchivedList />} />
          <Route path="/ratios" element={<RatiosCharts />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
