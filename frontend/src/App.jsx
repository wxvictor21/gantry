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
            <div style={{ display: 'flex' }}>
              <div style={{ flex: 1 }}>
                <MotorControl />
              </div>
              <div style={{ flex: 1.5 }}>
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
