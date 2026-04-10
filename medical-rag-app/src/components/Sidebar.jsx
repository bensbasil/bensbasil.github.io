import { useState, useRef } from 'react';
import { UploadCloud, CheckCircle2, FileText, BarChart3, Loader2, X } from 'lucide-react';
import './Sidebar.css';

export default function Sidebar({ documents, onUploadSuccess }) {
  const [isUploading, setIsUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = async (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      await handleFile(e.target.files[0]);
    }
  };

  const handleFile = async (file) => {
    if (file.type !== "application/pdf") {
      alert("Please upload a valid PDF file.");
      return;
    }
    
    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      // Typically fetch from backend
      const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
      const res = await fetch(`${API_BASE}/api/documents/upload`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if(onUploadSuccess) onUploadSuccess();
      fileInputRef.current.value = "";
    } catch (err) {
      console.error(err);
      alert("Upload failed. Verify backend is running.");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <aside className="sidebar-container glass-panel animate-fade-in">
      <div className="sidebar-header">
        <div className="logo-container">
          <div className="logo-icon pulse-primary">
            <UploadCloud />
          </div>
          <h2>MedLit RAG</h2>
        </div>
        <p className="subtitle">Medical Knowledge Base</p>
      </div>

      <div className="upload-section">
        <form 
          className={`upload-zone ${dragActive ? 'drag-active' : ''}`}
          onDragEnter={handleDrag} onDragLeave={handleDrag} onDragOver={handleDrag} onDrop={handleDrop}
          onClick={() => fileInputRef.current.click()}
        >
          <input 
            ref={fileInputRef} type="file" accept="application/pdf"
            onChange={handleChange} style={{ display: "none" }}
          />
          {isUploading ? (
            <div className="uploading-state">
              <Loader2 className="spinner" size={32} />
              <p>Processing text & embeddings...</p>
            </div>
          ) : (
            <div className="default-state">
              <UploadCloud size={32} color="var(--accent-color)" />
              <p><strong>Click</strong> or <strong>Drag & Drop</strong> PDFs</p>
              <span className="upload-hint">Supports Milvus Vector Ingestion</span>
            </div>
          )}
        </form>
      </div>

      <div className="stats-section">
        <h3 className="section-title"><BarChart3 size={16} /> System Metrics</h3>
        <div className="metric-card">
          <span>Active Documents</span>
          <strong>{documents.length || 0}</strong>
        </div>
        <div className="metric-card">
          <span>Vector Database</span>
          <span className="status-badge success">Milvus Online</span>
        </div>
      </div>

      <div className="documents-list">
        <h3 className="section-title"><FileText size={16} /> Processed Files</h3>
        <div className="doc-scroll-area">
          {documents.length === 0 ? (
            <p className="empty-state">No documents ingested yet.</p>
          ) : (
            documents.map((doc, idx) => (
              <div key={idx} className="doc-item">
                <CheckCircle2 size={16} color="var(--success-color)" />
                <span className="doc-name" title={doc.filename}>{doc.filename}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </aside>
  );
}
