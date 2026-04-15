import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Chat from './components/Chat';

function App() {
  const [documents, setDocuments] = useState([]);

  const fetchDocuments = async () => {
    try {
      const API_BASE = import.meta.env.VITE_API_BASE_URL || "https://api.bensbasil.in";
      const res = await fetch(`${API_BASE}/api/documents`);
      const data = await res.json();
      if(Array.isArray(data)) {
        setDocuments(data);
      }
    } catch (err) {
      console.error("Failed to fetch documents", err);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  return (
    <div className="layout-container">
      <Sidebar documents={documents} onUploadSuccess={fetchDocuments} />
      <Chat />
    </div>
  );
}

export default App;
