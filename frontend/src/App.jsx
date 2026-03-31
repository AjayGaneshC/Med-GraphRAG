import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Dashboard from './components/Dashboard';
import Query from './components/Query';
import Ingest from './components/Ingest';
import Explorer from './components/Explorer';
import SettingsPanel from './components/SettingsPanel';
import Sidebar from './components/Sidebar';
import api from './services/api';

function App() {
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [stats, setStats] = useState(null);
  const [healthStatus, setHealthStatus] = useState({ healthy: false });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
    checkHealth();
    
    // Refresh stats every minute
    const statsInterval = setInterval(loadStats, 60000);
    // Check health every 30 seconds
    const healthInterval = setInterval(checkHealth, 30000);
    
    return () => {
      clearInterval(statsInterval);
      clearInterval(healthInterval);
    };
  }, []);

  const loadStats = async () => {
    try {
      const data = await api.getStats();
      setStats(data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to load stats:', error);
      setLoading(false);
    }
  };

  const checkHealth = async () => {
    try {
      const health = await api.checkHealth();
      setHealthStatus(health);
    } catch (error) {
      console.error('Health check failed:', error);
      setHealthStatus({ healthy: false });
    }
  };

  const renderPage = () => {
    const pageVariants = {
      initial: { opacity: 0, y: 20 },
      animate: { opacity: 1, y: 0 },
      exit: { opacity: 0, y: -20 }
    };

    switch (currentPage) {
      case 'dashboard':
        return (
          <motion.div
            key="dashboard"
            variants={pageVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={{ duration: 0.3 }}
          >
            <Dashboard stats={stats} loading={loading} onRefresh={loadStats} />
          </motion.div>
        );
      case 'query':
        return (
          <motion.div
            key="query"
            variants={pageVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={{ duration: 0.3 }}
          >
            <Query />
          </motion.div>
        );
      case 'ingest':
        return (
          <motion.div
            key="ingest"
            variants={pageVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={{ duration: 0.3 }}
          >
            <Ingest onIngestComplete={loadStats} />
          </motion.div>
        );
      case 'explorer':
        return (
          <motion.div
            key="explorer"
            variants={pageVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={{ duration: 0.3 }}
          >
            <Explorer />
          </motion.div>
        );
      case 'settings':
        return (
          <motion.div
            key="settings"
            variants={pageVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={{ duration: 0.3 }}
          >
            <SettingsPanel onAction={loadStats} />
          </motion.div>
        );
      default:
        return <Dashboard stats={stats} loading={loading} onRefresh={loadStats} />;
    }
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar 
        currentPage={currentPage}
        setCurrentPage={setCurrentPage}
        healthStatus={healthStatus}
        stats={stats}
      />
      
      <main className="flex-1 overflow-auto p-8">
        <AnimatePresence mode="wait">
          {renderPage()}
        </AnimatePresence>
      </main>
    </div>
  );
}

export default App;
