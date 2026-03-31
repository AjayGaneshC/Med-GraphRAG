import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const api = {
  // Health check
  checkHealth: async () => {
    const response = await axios.get(`${API_BASE_URL}/health`);
    return response.data;
  },

  // Statistics
  getStats: async () => {
    const response = await axios.get(`${API_BASE_URL}/stats`);
    return response.data;
  },

  // Query
  query: async (question) => {
    const response = await axios.post(`${API_BASE_URL}/query`, { query: question });
    return response.data;
  },

  // Ingest files
  ingestFiles: async (files) => {
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });
    const response = await axios.post(`${API_BASE_URL}/ingest/files`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Ingest text
  ingestText: async (text) => {
    const response = await axios.post(`${API_BASE_URL}/ingest/text`, { text });
    return response.data;
  },

  // Get entities
  getEntities: async (entityType = null, limit = 100) => {
    const params = new URLSearchParams();
    if (entityType) params.append('entity_type', entityType);
    params.append('limit', limit);
    
    const response = await axios.get(`${API_BASE_URL}/entities?${params}`);
    return response.data;
  },

  // Get subgraph
  getSubgraph: async (maxNodes = 50) => {
    const response = await axios.get(`${API_BASE_URL}/graph/subgraph?max_nodes=${maxNodes}`);
    return response.data;
  },

  // Get entity neighborhood
  getEntityNeighborhood: async (entityId, depth = 1) => {
    const response = await axios.get(`${API_BASE_URL}/graph/entity/${entityId}?depth=${depth}`);
    return response.data;
  },

  // Initialize database
  initDatabase: async () => {
    const response = await axios.post(`${API_BASE_URL}/database/init`);
    return response.data;
  },

  // Clear database
  clearDatabase: async () => {
    const response = await axios.delete(`${API_BASE_URL}/database/clear`);
    return response.data;
  },
};

export default api;
