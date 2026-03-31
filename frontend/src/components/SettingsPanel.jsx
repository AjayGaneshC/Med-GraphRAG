import { useState } from 'react';
import { Settings, Database, Trash2, RefreshCw, AlertTriangle, CheckCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../services/api';

const SettingsPanel = ({ onAction }) => {
  const [initializing, setInitializing] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [result, setResult] = useState(null);
  const [showConfirm, setShowConfirm] = useState(false);

  const handleInitialize = async () => {
    setInitializing(true);
    setResult(null);
    
    try {
      const data = await api.initDatabase();
      setResult({ success: true, message: data.message });
      if (onAction) onAction();
    } catch (error) {
      console.error('Initialize failed:', error);
      setResult({ success: false, message: error.message });
    } finally {
      setInitializing(false);
    }
  };

  const handleClear = async () => {
    setClearing(true);
    setResult(null);
    setShowConfirm(false);
    
    try {
      const data = await api.clearDatabase();
      setResult({ success: true, message: data.message });
      if (onAction) onAction();
    } catch (error) {
      console.error('Clear failed:', error);
      setResult({ success: false, message: error.message });
    } finally {
      setClearing(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-4xl font-bold text-white flex items-center gap-3 mb-2">
          <Settings className="w-10 h-10 text-cardio-primary" />
          System Settings
        </h1>
        <p className="text-gray-400">Manage database and system configuration</p>
      </div>

      {/* Database Actions */}
      <div className="cardio-card p-6">
        <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
          <Database className="w-6 h-6 text-cardio-primary" />
          Database Management
        </h2>

        <div className="space-y-4">
          {/* Initialize Schema */}
          <div className="bg-gray-700 bg-opacity-30 rounded-lg p-6">
            <div className="flex items-start gap-4">
              <RefreshCw className="w-6 h-6 text-blue-500 flex-shrink-0 mt-1" />
              <div className="flex-1">
                <h3 className="text-white font-semibold mb-2">Initialize Schema</h3>
                <p className="text-gray-400 text-sm mb-4">
                  Create or update database schema, indexes, and constraints. Safe to run multiple times.
                </p>
                <motion.button
                  onClick={handleInitialize}
                  disabled={initializing}
                  className="btn-outline-cardio flex items-center gap-2"
                  whileHover={{ scale: initializing ? 1 : 1.02 }}
                  whileTap={{ scale: initializing ? 1 : 0.98 }}
                >
                  {initializing ? (
                    <>
                      <RefreshCw className="w-5 h-5 animate-spin" />
                      Initializing...
                    </>
                  ) : (
                    <>
                      <RefreshCw className="w-5 h-5" />
                      Initialize Schema
                    </>
                  )}
                </motion.button>
              </div>
            </div>
          </div>

          {/* Clear Database */}
          <div className="bg-gray-700 bg-opacity-30 rounded-lg p-6 border border-red-500/30">
            <div className="flex items-start gap-4">
              <AlertTriangle className="w-6 h-6 text-red-500 flex-shrink-0 mt-1" />
              <div className="flex-1">
                <h3 className="text-white font-semibold mb-2">Clear Database</h3>
                <p className="text-gray-400 text-sm mb-4">
                  <span className="text-red-400 font-semibold">Warning:</span> This will permanently delete all data including documents, chunks, entities, and relations. This action cannot be undone!
                </p>
                
                {!showConfirm ? (
                  <motion.button
                    onClick={() => setShowConfirm(true)}
                    className="bg-red-600 hover:bg-red-700 text-white font-semibold py-2 px-6 rounded-lg transition-all flex items-center gap-2"
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <Trash2 className="w-5 h-5" />
                    Clear Database
                  </motion.button>
                ) : (
                  <div className="space-y-3">
                    <p className="text-yellow-400 font-semibold">Are you absolutely sure?</p>
                    <div className="flex gap-3">
                      <motion.button
                        onClick={handleClear}
                        disabled={clearing}
                        className="bg-red-600 hover:bg-red-700 text-white font-semibold py-2 px-6 rounded-lg transition-all flex items-center gap-2"
                        whileHover={{ scale: clearing ? 1 : 1.02 }}
                        whileTap={{ scale: clearing ? 1 : 0.98 }}
                      >
                        {clearing ? (
                          <>
                            <RefreshCw className="w-5 h-5 animate-spin" />
                            Clearing...
                          </>
                        ) : (
                          <>
                            <Trash2 className="w-5 h-5" />
                            Yes, Clear Everything
                          </>
                        )}
                      </motion.button>
                      <button
                        onClick={() => setShowConfirm(false)}
                        disabled={clearing}
                        className="bg-gray-600 hover:bg-gray-700 text-white font-semibold py-2 px-6 rounded-lg transition-all"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Result Message */}
      {result && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className={`cardio-card p-6 ${
            result.success
              ? 'border-green-500'
              : 'border-red-500'
          }`}
        >
          <div className="flex items-start gap-3">
            {result.success ? (
              <CheckCircle className="w-6 h-6 text-green-500 flex-shrink-0" />
            ) : (
              <AlertTriangle className="w-6 h-6 text-red-500 flex-shrink-0" />
            )}
            <div>
              <h3 className={`font-semibold mb-2 ${
                result.success ? 'text-green-500' : 'text-red-500'
              }`}>
                {result.success ? 'Success!' : 'Error'}
              </h3>
              <p className={result.success ? 'text-green-300' : 'text-red-300'}>
                {result.message}
              </p>
            </div>
          </div>
        </motion.div>
      )}

      {/* Configuration Info */}
      <div className="cardio-card p-6">
        <h2 className="text-xl font-bold text-white mb-4">System Configuration</h2>
        <div className="bg-gray-700 bg-opacity-30 rounded-lg p-4 space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-400">Backend API:</span>
            <span className="text-white font-mono">http://localhost:8000</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Database:</span>
            <span className="text-white font-mono">Neo4j</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">LLM Provider:</span>
            <span className="text-white font-mono">Ollama (llama3:latest)</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Embedding Model:</span>
            <span className="text-white font-mono">all-MiniLM-L6-v2</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPanel;
