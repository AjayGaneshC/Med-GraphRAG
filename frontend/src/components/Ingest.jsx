import { useState } from 'react';
import { Upload, FileText, Heart, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../services/api';

const Ingest = ({ onIngestComplete }) => {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [text, setText] = useState('');
  const [activeTab, setActiveTab] = useState('files');
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setSelectedFiles([...selectedFiles, ...Array.from(e.dataTransfer.files)]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFiles([...selectedFiles, ...Array.from(e.target.files)]);
    }
  };

  const removeFile = (index) => {
    setSelectedFiles(selectedFiles.filter((_, i) => i !== index));
  };

  const handleIngestFiles = async () => {
    if (selectedFiles.length === 0) return;

    setUploading(true);
    setResult(null);
    
    try {
      const data = await api.ingestFiles(selectedFiles);
      setResult({ success: true, data });
      setSelectedFiles([]);
      if (onIngestComplete) onIngestComplete();
    } catch (error) {
      console.error('Ingest failed:', error);
      setResult({ success: false, error: error.message });
    } finally {
      setUploading(false);
    }
  };

  const handleIngestText = async () => {
    if (!text.trim()) return;

    setUploading(true);
    setResult(null);
    
    try {
      const data = await api.ingestText(text);
      setResult({ success: true, data });
      setText('');
      if (onIngestComplete) onIngestComplete();
    } catch (error) {
      console.error('Ingest failed:', error);
      setResult({ success: false, error: error.message });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-4xl font-bold text-white flex items-center gap-3 mb-2">
          <Upload className="w-10 h-10 text-cardio-primary" />
          Ingest Documents
        </h1>
        <p className="text-gray-400">Add medical documents to the knowledge graph</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2">
        <button
          onClick={() => setActiveTab('files')}
          className={`px-6 py-3 rounded-lg font-semibold transition-all ${
            activeTab === 'files'
              ? 'bg-cardio-gradient text-white'
              : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
          }`}
        >
          <FileText className="inline w-5 h-5 mr-2" />
          Upload Files
        </button>
        <button
          onClick={() => setActiveTab('text')}
          className={`px-6 py-3 rounded-lg font-semibold transition-all ${
            activeTab === 'text'
              ? 'bg-cardio-gradient text-white'
              : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
          }`}
        >
          <FileText className="inline w-5 h-5 mr-2" />
          Paste Text
        </button>
      </div>

      {/* File Upload Tab */}
      {activeTab === 'files' && (
        <div className="cardio-card p-6 space-y-6">
          {/* Drop Zone */}
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-lg p-12 text-center transition-all ${
              dragActive
                ? 'border-cardio-primary bg-cardio-primary bg-opacity-10'
                : 'border-gray-600 hover:border-cardio-primary'
            }`}
          >
            <Upload className="w-16 h-16 mx-auto mb-4 text-cardio-primary" />
            <p className="text-white font-semibold mb-2">
              Drag & drop files here
            </p>
            <p className="text-gray-400 text-sm mb-4">
              Supports: PDF, DOCX, TXT, HTML, JSON, CSV, XML, MD, RTF
            </p>
            <label className="btn-outline-cardio cursor-pointer inline-flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Browse Files
              <input
                type="file"
                multiple
                onChange={handleFileChange}
                className="hidden"
                accept=".pdf,.docx,.doc,.txt,.html,.htm,.json,.csv,.xml,.md,.rtf"
              />
            </label>
          </div>

          {/* Selected Files */}
          {selectedFiles.length > 0 && (
            <div>
              <h3 className="text-white font-semibold mb-3">Selected Files ({selectedFiles.length})</h3>
              <div className="space-y-2">
                {selectedFiles.map((file, index) => (
                  <div key={index} className="flex items-center justify-between bg-gray-700 bg-opacity-50 rounded-lg p-3">
                    <div className="flex items-center gap-3">
                      <FileText className="w-5 h-5 text-cardio-accent" />
                      <div>
                        <p className="text-white">{file.name}</p>
                        <p className="text-gray-400 text-xs">{(file.size / 1024).toFixed(2)} KB</p>
                      </div>
                    </div>
                    <button
                      onClick={() => removeFile(index)}
                      className="text-red-400 hover:text-red-300"
                    >
                      <XCircle className="w-5 h-5" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Upload Button */}
          <motion.button
            onClick={handleIngestFiles}
            disabled={selectedFiles.length === 0 || uploading}
            className="btn-cardio w-full flex items-center justify-center gap-2"
            whileHover={{ scale: selectedFiles.length === 0 || uploading ? 1 : 1.02 }}
            whileTap={{ scale: selectedFiles.length === 0 || uploading ? 1 : 0.98 }}
          >
            {uploading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Ingesting...
              </>
            ) : (
              <>
                <Upload className="w-5 h-5" />
                Ingest Files
              </>
            )}
          </motion.button>
        </div>
      )}

      {/* Text Input Tab */}
      {activeTab === 'text' && (
        <div className="cardio-card p-6 space-y-6">
          <div>
            <label className="block text-gray-300 font-semibold mb-2">
              Paste Text Content
            </label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste medical text here..."
              rows={12}
              className="w-full bg-gray-700 bg-opacity-50 text-white border border-cardio-primary/50 rounded-lg p-4 focus:outline-none focus:border-cardio-primary transition-colors resize-none"
            />
          </div>

          <motion.button
            onClick={handleIngestText}
            disabled={!text.trim() || uploading}
            className="btn-cardio w-full flex items-center justify-center gap-2"
            whileHover={{ scale: !text.trim() || uploading ? 1 : 1.02 }}
            whileTap={{ scale: !text.trim() || uploading ? 1 : 0.98 }}
          >
            {uploading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Ingesting...
              </>
            ) : (
              <>
                <Heart className="w-5 h-5" fill="currentColor" />
                Ingest Text
              </>
            )}
          </motion.button>
        </div>
      )}

      {/* Result */}
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
              <XCircle className="w-6 h-6 text-red-500 flex-shrink-0" />
            )}
            <div>
              <h3 className={`font-semibold mb-2 ${
                result.success ? 'text-green-500' : 'text-red-500'
              }`}>
                {result.success ? 'Ingestion Successful!' : 'Ingestion Failed'}
              </h3>
              {result.success ? (
                <div className="text-gray-300 space-y-1">
                  <p>Entities extracted: {result.data.entities_count}</p>
                  <p>Relations found: {result.data.relations_count}</p>
                  <p className="text-sm text-gray-400 mt-2">{result.data.message}</p>
                </div>
              ) : (
                <p className="text-red-300">{result.error}</p>
              )}
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default Ingest;
