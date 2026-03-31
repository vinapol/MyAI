import React, { useState, useEffect, useCallback, useRef } from 'react';
import ReactFlow, { 
  useNodesState, 
  useEdgesState, 
  Background, 
  Controls 
} from 'reactflow';
import axios from 'axios';
import 'reactflow/dist/style.css';
import VibrationNode from './vibrationNode.js';

// --- CONFIGURATION ---
const API_URL = "http://localhost:5001";
const nodeTypes = { vibrationNode: VibrationNode };

// --- CORRECTIF RESIZEOBSERVER ---
if (typeof window !== 'undefined') {
  const prevError = window.onerror;
  window.onerror = (...args) => {
    if (args[0].includes('ResizeObserver')) return true;
    if (prevError) return prevError(...args);
    return false;
  };
}

function App() {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  
  // État de la conversation (Rétroaction)
  const [conversation, setConversation] = useState({ attente_reponse: false, derniere_question: "" });
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorder = useRef(null);

  // 1. RÉCUPÉRATION DU GRAPHE ET DU CONTEXTE
  const fetchGraph = useCallback(async () => {
    try {
      const response = await axios.get(`${API_URL}/api/graph`);
      const { nodes: backendNodes, edges: backendEdges, conversation: convData } = response.data;

      // Formatage des nœuds avec style dynamique selon le poids
      const flowNodes = (backendNodes || []).map((n) => ({
        ...n,
        position: n.position || { x: Math.random() * 500, y: Math.random() * 300 },
        data: {
            ...n.data,
            // On peut ajouter ici des calculs de style si besoin
        }
      }));

      setNodes(flowNodes);
      setEdges(backendEdges || []);
      if (convData) setConversation(convData);
      
    } catch (err) {
      console.error("Erreur de synchronisation Teto Core:", err);
    }
  }, [setNodes, setEdges]);

  // 2. SYSTÈME D'ENREGISTREMENT VOCAL (RÉPONSE)
  const toggleRecording = async () => {
    if (isRecording) {
      mediaRecorder.current.stop();
      setIsRecording(false);
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder.current = new MediaRecorder(stream);
        const chunks = [];
        
        mediaRecorder.current.ondataavailable = (e) => chunks.push(e.data);
        mediaRecorder.current.onstop = async () => {
          const blob = new Blob(chunks, { type: 'audio/wav' });
          const formData = new FormData();
          formData.append('audio', blob);
          
          // Envoi de la réponse "Oui/Non" au Backend
          await axios.post(`${API_URL}/api/retroaction`, formData);
          fetchGraph(); 
        };

        mediaRecorder.current.start();
        setIsRecording(true);
      } catch (err) {
        alert("Microphone inaccessible");
      }
    }
  };

  // 3. BOUCLE DE MISE À JOUR
  useEffect(() => {
    fetchGraph();
    const interval = setInterval(fetchGraph, 4000);
    return () => clearInterval(interval);
  }, [fetchGraph]);

  return (
    <div style={{ width: '100vw', height: '100vh', display: 'flex', backgroundColor: '#020617', color: 'white', fontFamily: 'sans-serif' }}>
      
      {/* SIDEBAR GAUCHE */}
      <div style={{ width: '300px', backgroundColor: '#0f172a', borderRight: '1px solid #1e293b', padding: '25px', zIndex: 10 }}>
        <h1 style={{ color: '#3b82f6', margin: 0, fontSize: '1.8rem', letterSpacing: '-1px' }}>TETO <span style={{color:'white'}}>CORE</span></h1>
        <p style={{ fontSize: '0.7rem', color: '#64748b', marginBottom: '30px' }}>UNITÉ D'APPRENTISSAGE AUTONOME</p>
        
        <div style={{ padding: '15px', backgroundColor: '#1e293b', borderRadius: '10px', marginBottom: '20px' }}>
          <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Mémoire active</div>
          <div style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>{nodes.length} Neurones</div>
        </div>

        <button 
          onClick={fetchGraph}
          style={{ width: '100%', padding: '12px', borderRadius: '8px', border: 'none', backgroundColor: '#2563eb', color: 'white', fontWeight: 'bold', cursor: 'pointer' }}
        >
          Scanner la Mémoire
        </button>
      </div>

      {/* ZONE DU GRAPHE */}
      <div style={{ flex: 1, position: 'relative' }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={(_, node) => setSelectedNode(node)}
          fitView
        >
          <Background color="#1e293b" variant="dots" />
          <Controls />
        </ReactFlow>

        {/* BULLE DE DIALOGUE (Rétroaction) */}
        {conversation.derniere_question && (
          <div style={{
            position: 'absolute', bottom: '40px', left: '50%', transform: 'translateX(-50%)',
            width: '450px', backgroundColor: '#0f172a', border: '2px solid #3b82f6',
            borderRadius: '16px', padding: '20px', textAlign: 'center', zIndex: 100,
            boxShadow: '0 10px 25px rgba(0,0,0,0.5)'
          }}>
            <div style={{ color: '#3b82f6', fontSize: '0.7rem', fontWeight: 'bold', marginBottom: '10px', textTransform: 'uppercase' }}>Demande de validation</div>
            <div style={{ fontSize: '1.1rem', marginBottom: '20px' }}>"{conversation.derniere_question}"</div>
            
            <button 
              onClick={toggleRecording}
              style={{
                padding: '12px 25px', borderRadius: '30px', border: 'none',
                backgroundColor: isRecording ? '#ef4444' : '#3b82f6',
                color: 'white', fontWeight: 'bold', cursor: 'pointer',
                display: 'flex', alignItems: 'center', margin: '0 auto', gap: '10px'
              }}
            >
              <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: 'white', animation: isRecording ? 'pulse 1s infinite' : 'none' }} />
              {isRecording ? "J'écoute..." : "Répondre par la voix"}
            </button>
          </div>
        )}
      </div>

      {/* INSPECTEUR DROIT */}
      {selectedNode && (
        <div style={{ width: '320px', backgroundColor: '#0f172a', borderLeft: '1px solid #1e293b', padding: '25px', zIndex: 10 }}>
          <h2 style={{ color: '#3b82f6', marginTop: 0 }}>{selectedNode.data.label}</h2>
          <hr style={{ borderColor: '#1e293b' }} />
          <p style={{ color: '#94a3b8' }}>Type: <span style={{ color: 'white' }}>{selectedNode.type}</span></p>
          <p style={{ color: '#94a3b8' }}>ID: <span style={{ color: 'white', fontSize: '0.8rem' }}>{selectedNode.id}</span></p>
          <button 
            onClick={() => setSelectedNode(null)}
            style={{ marginTop: '20px', background: 'none', border: '1px solid #475569', color: '#94a3b8', padding: '8px 15px', borderRadius: '5px', cursor: 'pointer' }}
          >
            Fermer
          </button>
        </div>
      )}

      <style>{`
        @keyframes pulse {
          0% { opacity: 1; }
          50% { opacity: 0.3; }
          100% { opacity: 1; }
        }
      `}</style>
    </div>
  );
}

export default App;