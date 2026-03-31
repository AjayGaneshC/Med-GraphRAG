// API Base URL
const API_BASE = '';

// State
let selectedFiles = [];
let currentGraph = null;

// Utility Functions
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span>${type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'}</span>
        <span>${message}</span>
    `;
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

function formatNumber(num) {
    return num.toLocaleString();
}

// Navigation
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();
        const page = item.dataset.page;
        
        // Update nav
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        item.classList.add('active');
        
        // Update pages
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        document.getElementById(`${page}-page`).classList.add('active');
        
        // Load page data
        if (page === 'dashboard') loadDashboard();
        if (page === 'graph') loadGraphExplorer();
    });
});

// Health Check & Stats
async function updateHealth() {
    try {
        const response = await fetch(`${API_BASE}/api/health`);
        const data = await response.json();
        
        document.getElementById('neo4j-status').classList.toggle('connected', data.neo4j === 'connected');
        document.getElementById('ollama-status').classList.toggle('connected', data.ollama === 'connected');
    } catch (error) {
        console.error('Health check failed:', error);
    }
}

async function updateStats() {
    try {
        const response = await fetch(`${API_BASE}/api/stats`);
        const data = await response.json();
        
        // Update sidebar
        document.getElementById('sidebar-entities').textContent = formatNumber(data.entities);
        document.getElementById('sidebar-relations').textContent = formatNumber(data.relations);
        document.getElementById('sidebar-docs').textContent = formatNumber(data.documents);
        document.getElementById('sidebar-chunks').textContent = formatNumber(data.chunks);
        
        // Update metrics
        document.getElementById('metric-docs').textContent = formatNumber(data.documents);
        document.getElementById('metric-chunks').textContent = formatNumber(data.chunks);
        document.getElementById('metric-occurrences').textContent = formatNumber(data.occurrences);
        document.getElementById('metric-entities').textContent = formatNumber(data.entities);
        document.getElementById('metric-relations').textContent = formatNumber(data.relations);
        
        return data;
    } catch (error) {
        console.error('Stats update failed:', error);
        return null;
    }
}

// Dashboard
async function loadDashboard() {
    const stats = await updateStats();
    if (!stats) return;
    
    // Render entity chart
    const chartContainer = document.getElementById('entity-chart');
    if (stats.entity_types && stats.entity_types.length > 0) {
        const maxCount = Math.max(...stats.entity_types.map(t => t.count));
        chartContainer.innerHTML = stats.entity_types.map(type => `
            <div class="chart-bar">
                <div class="chart-label">${type.type}</div>
                <div class="chart-bar-fill" style="width: ${(type.count / maxCount) * 100}%">
                    ${type.count}
                </div>
            </div>
        `).join('');
    } else {
        chartContainer.innerHTML = '<p style="color: #718096;">No entities in the graph yet</p>';
    }
    
    // Load top entities
    try {
        const response = await fetch(`${API_BASE}/api/entities?limit=10`);
        const data = await response.json();
        const container = document.getElementById('top-entities');
        
        if (data.entities && data.entities.length > 0) {
            container.innerHTML = data.entities.map(ent => `
                <div style="margin-bottom: 0.75rem;">
                    <span class="entity-badge ${ent.type}">${ent.type}</span>
                    <strong>${ent.name}</strong>
                    <span style="color: #718096; font-size: 0.875rem;">(${ent.count} mentions)</span>
                </div>
            `).join('');
        } else {
            container.innerHTML = '<p style="color: #718096;">No entities in the graph yet</p>';
        }
    } catch (error) {
        console.error('Failed to load top entities:', error);
    }
}

// Query
document.getElementById('search-btn').addEventListener('click', async () => {
    const query = document.getElementById('query-input').value.trim();
    if (!query) {
        showToast('Please enter a question', 'error');
        return;
    }
    
    const btn = document.getElementById('search-btn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Searching...';
    
    try {
        const response = await fetch(`${API_BASE}/api/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });
        
        if (!response.ok) throw new Error('Query failed');
        
        const result = await response.json();
        displayQueryResults(result);
    } catch (error) {
        showToast('Query failed: ' + error.message, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<span class="icon">🔎</span> Search';
    }
});

function displayQueryResults(result) {
    const container = document.getElementById('search-results');
    const showGraph = document.getElementById('show-graph').checked;
    const showSources = document.getElementById('show-sources').checked;
    
    let html = `
        <div class="answer-box">
            <h4>💡 Answer</h4>
            <p>${result.answer}</p>
        </div>
    `;
    
    if (result.entities_found && result.entities_found.length > 0) {
        html += `
            <div class="card">
                <h2>🏷️ Entities Found</h2>
                ${result.entities_found.slice(0, 15).map(e => `<span class="entity-badge DRUG">${e}</span>`).join('')}
            </div>
        `;
    }
    
    if (showSources && result.sources && result.sources.length > 0) {
        html += `
            <div class="card">
                <h2>📚 Sources</h2>
                ${result.sources.map((src, i) => `
                    <div class="source-card">
                        <strong>📄 ${src.document}</strong>
                        <p style="margin-top: 0.5rem; color: #4a5568; font-size: 0.875rem;">${src.text.substring(0, 300)}...</p>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    container.innerHTML = html;
}

// File Upload
const uploadZone = document.getElementById('upload-zone');
const fileInput = document.getElementById('file-input');

uploadZone.addEventListener('click', () => fileInput.click());

uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('dragover');
});

uploadZone.addEventListener('dragleave', () => {
    uploadZone.classList.remove('dragover');
});

uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('dragover');
    handleFiles(e.dataTransfer.files);
});

fileInput.addEventListener('change', (e) => {
    handleFiles(e.target.files);
});

function handleFiles(files) {
    selectedFiles = Array.from(files);
    displayFileList();
    document.getElementById('upload-btn').style.display = 'block';
}

function displayFileList() {
    const container = document.getElementById('file-list');
    container.innerHTML = selectedFiles.map((file, index) => `
        <div class="file-item">
            <span>📄 ${file.name} (${(file.size / 1024).toFixed(1)} KB)</span>
            <span class="file-remove" onclick="removeFile(${index})">✖</span>
        </div>
    `).join('');
}

function removeFile(index) {
    selectedFiles.splice(index, 1);
    displayFileList();
    if (selectedFiles.length === 0) {
        document.getElementById('upload-btn').style.display = 'none';
    }
}

document.getElementById('upload-btn').addEventListener('click', async () => {
    if (selectedFiles.length === 0) return;
    
    const btn = document.getElementById('upload-btn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Processing...';
    
    const formData = new FormData();
    selectedFiles.forEach(file => formData.append('files', file));
    
    const progressContainer = document.getElementById('upload-progress');
    progressContainer.innerHTML = '<div class="progress-bar"><div class="progress-fill" style="width: 50%"></div></div>';
    
    try {
        const response = await fetch(`${API_BASE}/api/ingest/files`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) throw new Error('Upload failed');
        
        const result = await response.json();
        
        progressContainer.innerHTML = `
            <div class="answer-box">
                <h4>✅ Ingestion Complete!</h4>
                <p>Files processed: ${result.files_processed}</p>
                <p>Chunks: ${result.stats.chunks} | Entities: ${result.stats.new_entities} | Relations: ${result.stats.relations}</p>
                ${result.errors.length > 0 ? `<p style="color: #f56565; margin-top: 0.5rem;">Errors: ${result.errors.join(', ')}</p>` : ''}
            </div>
        `;
        
        showToast('Documents ingested successfully', 'success');
        updateStats();
        
        // Reset
        selectedFiles = [];
        fileInput.value = '';
        displayFileList();
        btn.style.display = 'none';
    } catch (error) {
        showToast('Upload failed: ' + error.message, 'error');
        progressContainer.innerHTML = '';
    } finally {
        btn.disabled = false;
        btn.innerHTML = '📥 Start Ingestion';
    }
});

// Paste Text Ingestion
document.getElementById('paste-ingest-btn').addEventListener('click', async () => {
    const title = document.getElementById('doc-title').value.trim() || 'Untitled Document';
    const content = document.getElementById('doc-content').value.trim();
    
    if (!content) {
        showToast('Please enter some text', 'error');
        return;
    }
    
    const btn = document.getElementById('paste-ingest-btn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Processing...';
    
    try {
        const formData = new FormData();
        formData.append('title', title);
        formData.append('content', content);
        
        const response = await fetch(`${API_BASE}/api/ingest/text`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) throw new Error('Ingestion failed');
        
        const result = await response.json();
        
        document.getElementById('paste-result').innerHTML = `
            <div class="answer-box">
                <h4>✅ Ingestion Complete!</h4>
                <p>Chunks: ${result.stats.chunks} | Entities: ${result.stats.new_entities} | Relations: ${result.stats.relations}</p>
            </div>
        `;
        
        showToast('Text ingested successfully', 'success');
        updateStats();
        
        // Clear form
        document.getElementById('doc-title').value = '';
        document.getElementById('doc-content').value = '';
    } catch (error) {
        showToast('Ingestion failed: ' + error.message, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '📥 Ingest Text';
    }
});

// Tabs
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        const tabName = tab.dataset.tab;
        
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        
        document.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));
        document.getElementById(`${tabName}-tab`).classList.add('active');
    });
});

// Graph Explorer
let entityListCache = [];

async function loadGraphExplorer() {
    await loadEntityList();
}

async function loadEntityList() {
    const entityType = document.getElementById('entity-type-filter').value;
    const search = document.getElementById('entity-search').value;
    
    try {
        const response = await fetch(`${API_BASE}/api/entities?entity_type=${entityType}&search=${search}&limit=50`);
        const data = await response.json();
        entityListCache = data.entities || [];
        
        const container = document.getElementById('entity-list');
        container.innerHTML = entityListCache.map(ent => `
            <div class="entity-item" onclick="viewEntityGraph('${ent.id}')">
                <span class="entity-badge ${ent.type}">${ent.type}</span>
                <div><strong>${ent.name}</strong></div>
                <div style="font-size: 0.75rem; color: #718096;">${ent.count} mentions</div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Failed to load entities:', error);
    }
}

document.getElementById('entity-type-filter').addEventListener('change', loadEntityList);
document.getElementById('entity-search').addEventListener('input', loadEntityList);

async function viewEntityGraph(entityId) {
    try {
        const response = await fetch(`${API_BASE}/api/graph/entity/${entityId}`);
        const data = await response.json();
        
        renderGraph(data.nodes, data.edges);
    } catch (error) {
        showToast('Failed to load graph: ' + error.message, 'error');
    }
}

function renderGraph(nodes, edges) {
    const container = document.getElementById('graph-viz');
    
    const colors = {
        DRUG: '#48bb78',
        DISEASE: '#f56565',
        SYMPTOM: '#ed8936',
        GENE: '#4299e1',
        PROTEIN: '#9f7aea',
        ANATOMY: '#a0aec0',
        PROCEDURE: '#718096',
        CHEMICAL: '#38b2ac',
        BIOMARKER: '#ed64a6',
        ORGANISM: '#68d391'
    };
    
    const visNodes = nodes.map(n => ({
        id: n.id,
        label: n.name.substring(0, 20),
        color: colors[n.type] || '#999',
        title: `${n.name} (${n.type})`
    }));
    
    const visEdges = edges.map(e => ({
        from: e.source,
        to: e.target,
        label: e.label || e.type,
        arrows: 'to'
    }));
    
    const graphData = {
        nodes: new vis.DataSet(visNodes),
        edges: new vis.DataSet(visEdges)
    };
    
    const options = {
        nodes: {
            shape: 'dot',
            size: 20,
            font: { size: 12, color: '#2d3748' }
        },
        edges: {
            font: { size: 10, align: 'middle' },
            color: { color: '#cbd5e0' }
        },
        physics: {
            enabled: true,
            stabilization: { iterations: 100 }
        }
    };
    
    if (currentGraph) currentGraph.destroy();
    currentGraph = new vis.Network(container, graphData, options);
}

// Settings
document.getElementById('init-schema-btn').addEventListener('click', async () => {
    const btn = document.getElementById('init-schema-btn');
    btn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE}/api/database/init`, { method: 'POST' });
        if (!response.ok) throw new Error('Init failed');
        
        showToast('Schema initialized successfully', 'success');
    } catch (error) {
        showToast('Init failed: ' + error.message, 'error');
    } finally {
        btn.disabled = false;
    }
});

document.getElementById('refresh-stats-btn').addEventListener('click', async () => {
    await updateStats();
    showToast('Stats refreshed', 'success');
});

document.getElementById('clear-db-btn').addEventListener('click', async () => {
    if (!confirm('Are you sure you want to delete ALL data? This cannot be undone!')) return;
    
    const btn = document.getElementById('clear-db-btn');
    btn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE}/api/database/clear`, { method: 'DELETE' });
        if (!response.ok) throw new Error('Clear failed');
        
        showToast('Database cleared', 'success');
        await updateStats();
    } catch (error) {
        showToast('Clear failed: ' + error.message, 'error');
    } finally {
        btn.disabled = false;
    }
});

// Initialize
updateHealth();
updateStats();
setInterval(updateHealth, 30000); // Update health every 30s
setInterval(updateStats, 60000); // Update stats every 60s
loadDashboard();
