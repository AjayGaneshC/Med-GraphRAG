import { useState, useEffect } from 'react';
import { Heart, Activity, Database, FileText, RefreshCw } from 'lucide-react';
import { motion } from 'framer-motion';

const Dashboard = ({ stats, loading, onRefresh }) => {
  const [refreshing, setRefreshing] = useState(false);

  const handleRefresh = async () => {
    setRefreshing(true);
    await onRefresh();
    setTimeout(() => setRefreshing(false), 500);
  };

  const metrics = stats ? [
    {
      icon: Database,
      label: 'Total Documents',
      value: stats.total_documents,
      color: 'from-red-500 to-rose-500',
      iconColor: 'text-red-500',
    },
    {
      icon: FileText,
      label: 'Total Chunks',
      value: stats.total_chunks,
      color: 'from-rose-500 to-pink-500',
      iconColor: 'text-rose-500',
    },
    {
      icon: Heart,
      label: 'Canonical Entities',
      value: stats.total_entities,
      color: 'from-pink-500 to-red-500',
      iconColor: 'text-pink-500',
    },
    {
      icon: Activity,
      label: 'Total Relations',
      value: stats.total_relations,
      color: 'from-red-600 to-rose-600',
      iconColor: 'text-red-600',
    },
  ] : [];

  const entityBreakdown = stats?.entity_breakdown || {};
  const entityTypes = Object.entries(entityBreakdown).sort((a, b) => b[1] - a[1]);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold text-white flex items-center gap-3">
            <Heart className="w-10 h-10 text-cardio-primary heart-icon" fill="currentColor" />
            Cardiovascular Knowledge Graph
          </h1>
          <p className="text-gray-400 mt-2">Medical entity extraction and relationship mapping</p>
        </div>
        <motion.button
          onClick={handleRefresh}
          disabled={refreshing}
          className="btn-cardio flex items-center gap-2"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <RefreshCw className={`w-5 h-5 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </motion.button>
      </div>

      {/* Metrics Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="cardio-card p-6 animate-pulse">
              <div className="h-12 w-12 bg-gray-700 rounded-lg mb-4"></div>
              <div className="h-4 bg-gray-700 rounded w-3/4 mb-2"></div>
              <div className="h-8 bg-gray-700 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {metrics.map((metric, index) => {
            const Icon = metric.icon;
            return (
              <motion.div
                key={metric.label}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="cardio-card p-6 hover:scale-105 transition-transform"
              >
                <div className={`w-12 h-12 rounded-lg bg-gradient-to-r ${metric.color} p-2.5 mb-4`}>
                  <Icon className="w-full h-full text-white" />
                </div>
                <p className="text-gray-400 text-sm mb-1">{metric.label}</p>
                <p className="text-3xl font-bold text-white">{metric.value.toLocaleString()}</p>
              </motion.div>
            );
          })}
        </div>
      )}

      {/* Entity Breakdown */}
      {!loading && entityTypes.length > 0 && (
        <div className="cardio-card p-6">
          <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
            <Activity className="w-6 h-6 text-cardio-primary" />
            Entity Distribution
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {entityTypes.map(([type, count], index) => (
              <motion.div
                key={type}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.05 }}
                className="bg-gray-700 bg-opacity-50 rounded-lg p-4 text-center"
              >
                <p className="text-cardio-accent font-semibold text-lg">{count}</p>
                <p className="text-gray-300 text-xs mt-1 capitalize">{type.replace('_', ' ')}</p>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Visualization placeholder */}
      {!loading && (
        <div className="cardio-card p-6">
          <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
            <Heart className="w-6 h-6 text-cardio-primary" />
            System Vitals
          </h2>
          <div className="grid grid-cols-3 gap-6">
            <div className="text-center">
              <div className="text-5xl font-bold text-cardio-accent mb-2">
                {stats?.total_occurrences || 0}
              </div>
              <div className="text-gray-400">Occurrences</div>
            </div>
            <div className="text-center">
              <div className="text-5xl font-bold text-rose-500 mb-2">
                {entityTypes.length}
              </div>
              <div className="text-gray-400">Entity Types</div>
            </div>
            <div className="text-center">
              <div className="text-5xl font-bold text-pink-500 mb-2">
                {stats?.total_relations || 0}
              </div>
              <div className="text-gray-400">Connections</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
