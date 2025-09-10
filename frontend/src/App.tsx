import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Box } from '@mui/material';

import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Vulnerabilities from './pages/Vulnerabilities';
import Tools from './pages/Tools';
import Alerts from './pages/Alerts';
import Settings from './pages/Settings';
import { WebSocketProvider } from './services/websocket';

function App() {
  return (
    <WebSocketProvider>
      <Box sx={{ display: 'flex', minHeight: '100vh' }}>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/vulnerabilities" element={<Vulnerabilities />} />
            <Route path="/tools" element={<Tools />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </Layout>
      </Box>
    </WebSocketProvider>
  );
}

export default App;