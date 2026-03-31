import { useState } from 'react';
import { Search, Heart, Loader2 } from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../services/api';
import ForceGraph2D from 'react-force-graph-2d';

const Query = () => {
  const [question, setQuestion] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [graphData, setGraphData] = useState(null);

  const handleQuery = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    try {
      const data = await api.query(question);
      setResult(data);
      
      // Transform graph data for visualization
      if (data.graph) {
        const nodesMap = new Map();
        data.graph.nodes.forEach(node => {
          if (!nodesMap.has(node.id)) {
            nodesMap.set(node.id, {
              id: node.id,
              name: node.properties.name,
              type: node.labels[0],
              ...node
            });
          }
        });
        const nodes = Array.from(nodesMap.values());
        
        const linksMap = new Map();
        data.graph.edges.forEach(edge => {
          const linkId = `${edge.start}-${edge.type}-${edge.end}`;
          if (!linksMap.has(linkId)) {
            linksMap.set(linkId, {
              source: edge.start,
              target: edge.end,
              type: edge.type,
              ...edge
            });
          }
        });
        const links = Array.from(linksMap.values());
        
        setGraphData({ nodes, links });
      }
    } catch (error) {
      console.error('Query failed:', error);
      setResult({ error: 'Query failed. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  const getNodeColor = (nodeType) => {
    const colors = {
      'CanonicalEntity': '#dc2626',
      'DRUG': '#ef4444',
      'DISEASE': '#f87171',
      'SYMPTOM': '#fca5a5',
      'GENE': '#b91c1c',
      'PROTEIN': '#991b1b',
      'PROCEDURE': '#f43f5e',
      'ANATOMY': '#ec4899',
      'ORGANISM': '#be123c',
      'CHEMICAL': '#e11d48',
      'BIOMARKER': '#fb7185',
    };
    return colors[nodeType] || '#dc2626';
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-4xl font-bold text-white flex items-center gap-3 mb-2">
          <Search className="w-10 h-10 text-cardio-primary" />
          Query Knowledge Graph
        </h1>
        <p className="text-gray-400">Ask questions about cardiovascular medical knowledge</p>
      </div>

      {/* Query Form */}
      <div className="cardio-card p-6">
        <form onSubmit={handleQuery} className="space-y-4">
          <div>
            <label className="block text-gray-300 font-semibold mb-2">
              Your Question
            </label>
            <div className="relative">
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="E.g., What drugs treat hypertension?"
                className="w-full bg-gray-700 bg-opacity-50 text-white border border-cardio-primary/50 rounded-lg px-4 py-3 pr-12 focus:outline-none focus:border-cardio-primary transition-colors"
              />
              <Heart className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-cardio-primary" />
            </div>
          </div>
          
          <motion.button
            type="submit"
            disabled={loading}
            className="btn-cardio w-full flex items-center justify-center gap-2"
            whileHover={{ scale: loading ? 1 : 1.02 }}
            whileTap={{ scale: loading ? 1 : 0.98 }}
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <Search className="w-5 h-5" />
                Search
              </>
            )}
          </motion.button>
        </form>
      </div>

      {/* Results */}
      {result && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          {/* Answer */}
          <div className="cardio-card p-6">
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <Heart className="w-5 h-5 text-cardio-primary heart-icon" fill="currentColor" />
              Answer
            </h2>
            {result.error ? (
              <div className="bg-red-900 bg-opacity-30 border border-red-500 rounded-lg p-4">
                <p className="text-red-300">{result.error}</p>
              </div>
            ) : (
              <div className="bg-gray-700 bg-opacity-30 rounded-lg p-6">
                <p className="text-white leading-relaxed">{result.answer}</p>
              </div>
            )}
          </div>

          {/* Supporting Context */}
          {result.context && result.context.length > 0 && (
            <div className="cardio-card p-6">
              <h2 className="text-xl font-bold text-white mb-4">Supporting Context</h2>
              <div className="space-y-3">
                {result.context.map((ctx, index) => (
                  <div key={index} className="bg-gray-700 bg-opacity-30 rounded-lg p-4">
                    <p className="text-gray-300 text-sm">{ctx}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Graph Visualization */}
          {graphData && graphData.nodes.length > 0 && (
            <div className="cardio-card p-6">
              <h2 className="text-xl font-bold text-white mb-4">Knowledge Graph</h2>
              <div className="bg-gray-900 rounded-lg overflow-hidden" style={{ height: '500px' }}>
                <ForceGraph2D
                  graphData={graphData}
                  nodeLabel="name"
                  nodeColor={(node) => getNodeColor(node.type)}
                  nodeRelSize={6}
                  linkColor={() => '#ef4444'}
                  linkWidth={2}
                  linkDirectionalArrowLength={6}
                  linkDirectionalArrowRelPos={1}
                  linkLabel={(link) => link.type}
                  backgroundColor="#111827"
                />
              </div>
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
};

export default Query;
