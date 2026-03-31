import { Heart, Activity, Database, Search, Upload, Network, Settings } from 'lucide-react';
import { motion } from 'framer-motion';

const Sidebar = ({ currentPage, setCurrentPage, healthStatus, stats }) => {
  const navItems = [
    { id: 'dashboard', icon: Activity, label: 'Dashboard', gradient: 'from-red-600 to-pink-600' },
    { id: 'query', icon: Search, label: 'Query', gradient: 'from-rose-600 to-red-600' },
    { id: 'ingest', icon: Upload, label: 'Ingest', gradient: 'from-pink-600 to-rose-600' },
    { id: 'explorer', icon: Network, label: 'Explorer', gradient: 'from-red-600 to-rose-600' },
    { id: 'settings', icon: Settings, label: 'Settings', gradient: 'from-rose-600 to-pink-600' },
  ];

  return (
    <div className="w-64 bg-gray-900 bg-opacity-80 backdrop-blur-md border-r border-cardio-primary flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-cardio-primary/30">
        <div className="flex items-center gap-3">
          <Heart className="w-8 h-8 text-cardio-primary heart-icon" fill="currentColor" />
          <div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-cardio-accent to-cardio-primary bg-clip-text text-transparent">
              CardioGraph
            </h1>
            <p className="text-xs text-gray-400">Medical Knowledge Graph</p>
          </div>
        </div>
      </div>

      {/* Status indicator */}
      <div className="px-6 py-4 border-b border-cardio-primary/30">
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${healthStatus.healthy ? 'bg-green-500 pulse-indicator' : 'bg-red-500'}`}></div>
          <span className="text-sm text-gray-300">
            {healthStatus.healthy ? 'System Healthy' : 'System Offline'}
          </span>
        </div>
        {stats && (
          <div className="mt-3 text-xs text-gray-400 space-y-1">
            <div className="flex justify-between">
              <span>Entities:</span>
              <span className="text-cardio-accent font-semibold">{stats.total_entities}</span>
            </div>
            <div className="flex justify-between">
              <span>Relations:</span>
              <span className="text-cardio-accent font-semibold">{stats.total_relations}</span>
            </div>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentPage === item.id;
          
          return (
            <motion.button
              key={item.id}
              onClick={() => setCurrentPage(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                isActive
                  ? `bg-gradient-to-r ${item.gradient} text-white shadow-lg`
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
              }`}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <Icon className="w-5 h-5" />
              <span className="font-medium">{item.label}</span>
            </motion.button>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-cardio-primary/30">
        <div className="text-xs text-gray-500 text-center">
          <p>Powered by Graph RAG</p>
          <p className="mt-1">Cardiovascular Edition</p>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
