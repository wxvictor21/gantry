import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import MotorControl from './components/MotorControl';
import Gallery from './components/Gallery';
import LastImage from './components/LastImage';

export default function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '2rem' }}>
              <div style={{ flex: 1 }}>
                <MotorControl />
              </div>
              <div style={{ flex: 1 }}>
                <LastImage />
              </div>
            </div>
          } />
          <Route path="/gallery" element={<Gallery />} />
        </Routes>
      </Layout>
    </Router>
  );
}
