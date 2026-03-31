import { useState, useEffect } from 'react';
import { Network, Filter, Heart } from 'lucide-react';
import { motion } from 'framer-motion';
import ForceGraph2D from 'react-force-graph-2d';
import api from '../services/api';

const Explorer = () => {
  const [entities, setEntities] = useState([]);
  const [graphData, setGraphData] = useState(null);
  const [selectedType, setSelectedType] = useState(null);
  const [maxNodes, setMaxNodes] = useState(50);
  const [loading, setLoading] = useState(false);

  const entityTypes = [
    { value: 'DRUG', label: 'Drugs', color: '#ef4444' },
    { value: 'DISEASE', label: 'Diseases', color: '#f87171' },
    { value: 'SYMPTOM', label: 'Symptoms', color: '#fca5a5' },
    { value: 'GENE', label: 'Genes', color: '#b91c1c' },
    { value: 'PROTEIN', label: 'Proteins', color: '#991b1b' },
    { value: 'PROCEDURE', label: 'Procedures', color: '#f43f5e' },
    { value: 'ANATOMY', label: 'Anatomy', color: '#ec4899' },
    { value: 'ORGANISM', label: 'Organisms', color: '#be123c' },
    { value: 'CHEMICAL', label: 'Chemicals', color: '#e11d48' },
    { value: 'BIOMARKER', label: 'Biomarkers', color: '#fb7185' },
  ];

  useEffect(() => {
    loadEntities();
    loadGraph();
  }, [selectedType, maxNodes]);

  const loadEntities = async () => {
    try {
      const data = await api.getEntities(selectedType, 100);
      setEntities(data.entities || []);
    } catch (error) {
      console.error('Failed to load entities:', error);
    }
  };

  const loadGraph = async () => {
    setLoading(true);
    try {
      const data = await api.getSubgraph(maxNodes);
      
      console.log('Received graph data:', data);
      
      if (!data.nodes || !data.edges) {
        console.error('Invalid graph data structure:', data);
        setGraphData({ nodes: [], links: [] });
        return;
      }
      
      const nodesMap = new Map();
      data.nodes.forEach(node => {
        if (!nodesMap.has(node.id)) {
          nodesMap.set(node.id, {
            id: node.id,
            name: node.properties?.name || 'Unknown',
            type: node.labels?.[0] || 'Unknown',
            entityType: node.properties?.entity_type || 'Unknown',
            ...node
          });
        }
      });
      const nodes = Array.from(nodesMap.values());
      
      const linksMap = new Map();
      data.edges.forEach(edge => {
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
      
      console.log('Processed graph data:', { nodeCount: nodes.length, linkCount: links.length });
      
      setGraphData({ nodes, links });
    } catch (error) {
      console.error('Failed to load graph:', error);
    } finally {
      setLoading(false);
    }
  };

  const getNodeColor = (node) => {
    const typeColor = entityTypes.find(t => t.value === node.entityType);
    return typeColor ? typeColor.color : '#dc2626';
  };

  const handleNodeClick = async (node) => {
    try {
      const data = await api.getEntityNeighborhood(node.id, 1);
      
      const nodesMap = new Map();
      data.nodes.forEach(n => {
        if (!nodesMap.has(n.id)) {
          nodesMap.set(n.id, {
            id: n.id,
            name: n.properties.name,
            type: n.labels[0],
            entityType: n.properties.entity_type,
            ...n
          });
        }
      });
      const nodes = Array.from(nodesMap.values());
      
      const linksMap = new Map();
      data.edges.forEach(edge => {
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
    } catch (error) {
      console.error('Failed to load neighborhood:', error);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-4xl font-bold text-white flex items-center gap-3 mb-2">
          <Network className="w-10 h-10 text-cardio-primary" />
          Graph Explorer
        </h1>
        <p className="text-gray-400">Explore the cardiovascular knowledge graph</p>
      </div>

      {/* Filters */}
      <div className="cardio-card p-6">
        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <Filter className="w-5 h-5 text-cardio-primary" />
          Filters
        </h2>
        
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-4">
          <button
            onClick={() => setSelectedType(null)}
            className={`px-4 py-2 rounded-lg font-semibold transition-all ${
              selectedType === null
                ? 'bg-cardio-gradient text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            All Types
          </button>
          {entityTypes.map((type) => (
            <button
              key={type.value}
              onClick={() => setSelectedType(type.value)}
              className={`px-4 py-2 rounded-lg font-semibold transition-all ${
                selectedType === type.value
                  ? 'bg-cardio-gradient text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
              style={{
                borderLeft: `4px solid ${type.color}`,
              }}
            >
              {type.label}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-4">
          <label className="text-gray-300 font-semibold">Max Nodes:</label>
          <input
            type="range"
            min="10"
            max="100"
            step="10"
            value={maxNodes}
            onChange={(e) => setMaxNodes(Number(e.target.value))}
            className="flex-1"
          />
          <span className="text-cardio-accent font-bold">{maxNodes}</span>
          <button
            onClick={loadGraph}
            className="btn-cardio"
          >
            Refresh
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Entity List */}
        <div className="lg:col-span-1">
          <div className="cardio-card p-6">
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <Heart className="w-5 h-5 text-cardio-primary heart-icon" fill="currentColor" />
              Entities ({entities.length})
            </h2>
            <div className="space-y-2 max-h-[600px] overflow-y-auto">
              {entities.map((entity) => {
                const typeColor = entityTypes.find(t => t.value === entity.entity_type);
                return (
                  <motion.div
                    key={entity.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="bg-gray-700 bg-opacity-50 rounded-lg p-3 hover:bg-opacity-70 transition-all cursor-pointer"
                    onClick={() => handleNodeClick({ id: entity.id })}
                  >
                    <div className="flex items-center gap-2">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: typeColor?.color || '#dc2626' }}
                      ></div>
                      <div className="flex-1">
                        <p className="text-white font-semibold">{entity.name}</p>
                        <p className="text-gray-400 text-xs capitalize">
                          {entity.entity_type?.replace('_', ' ').toLowerCase()}
                        </p>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Graph Visualization */}
        <div className="lg:col-span-2">
          <div className="cardio-card p-6">
            <h2 className="text-xl font-bold text-white mb-4">Entity Neighborhood</h2>
            {loading ? (
              <div className="bg-gray-900 rounded-lg flex items-center justify-center" style={{ height: '600px' }}>
                <div className="text-center">
                  <Heart className="w-16 h-16 text-cardio-primary mx-auto mb-4 heart-icon" fill="currentColor" />
                  <p className="text-gray-400">Loading graph...</p>
                </div>
              </div>
            ) : graphData && graphData.nodes && graphData.nodes.length > 0 ? (
              <div className="bg-gray-900 rounded-lg overflow-hidden" style={{ height: '600px' }}>
                <div className="text-white text-sm p-2 bg-gray-800">
                  {graphData.nodes.length} nodes, {graphData.links.length} edges
                </div>
                <ForceGraph2D
                  graphData={graphData}
                  nodeLabel="name"
                  nodeColor={getNodeColor}
                  nodeRelSize={8}
                  linkColor={() => '#ef4444'}
                  linkWidth={2}
                  linkDirectionalArrowLength={6}
                  linkDirectionalArrowRelPos={1}
                  linkLabel={(link) => link.type}
                  backgroundColor="#111827"
                  onNodeClick={handleNodeClick}
                  width={800}
                  height={550}
                />
              </div>
            ) : (
              <div className="bg-gray-900 rounded-lg flex items-center justify-center" style={{ height: '600px' }}>
                <div className="text-center">
                  <Network className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                  <p className="text-gray-400">No graph data available</p>
                  <p className="text-gray-500 text-sm mt-2">
                    {graphData ? `Nodes: ${graphData.nodes?.length || 0}` : 'Click Refresh to load'}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Explorer;
