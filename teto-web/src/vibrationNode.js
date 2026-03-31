import React from 'react';
import { Handle, Position } from 'reactflow';

const VibrationNode = ({ data }) => {
  // Calcul de la taille en fonction des itérations (min 80px, max 150px)
  const size = Math.min(80 + (data.iterations || 0) * 5, 150);
  
  // Intensité de l'aura (shadow) selon le poids/importance
  const glow = (data.poids || 0.1) * 20;

  const nodeStyle = {
    width: `${size}px`,
    height: `${size}px`,
    borderRadius: '50%',
    backgroundColor: '#facc15', // Jaune vif (Tailwind yellow-400)
    color: '#0f172a',           // Texte bleu nuit très foncé (lisibilité maximum)
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    border: '3px solid #eab308',
    boxShadow: `0 0 ${glow}px #facc15`,
    transition: 'all 0.5s ease-in-out',
    padding: '10px',
    textAlign: 'center',
    fontWeight: '800',
    fontSize: size > 100 ? '14px' : '11px',
    cursor: 'pointer',
  };

  return (
    <div style={nodeStyle}>
      {/* Entrée et Sortie des liens */}
      <Handle type="target" position={Position.Top} style={{ background: '#ca8a04' }} />
      
      <div style={{ fontSize: '1.2rem', marginBottom: '2px' }}>🎶</div>
      
      <div style={{ 
        textTransform: 'uppercase', 
        lineHeight: '1.1',
        wordBreak: 'break-word' 
      }}>
        {/* On affiche 'label' ou 'texte' selon ce que le backend envoie */}
        {data.label || data.texte || "???"}
      </div>

      {data.iterations > 0 && (
        <div style={{ 
          fontSize: '9px', 
          marginTop: '5px', 
          opacity: 0.8,
          backgroundColor: 'rgba(0,0,0,0.1)',
          padding: '2px 6px',
          borderRadius: '10px'
        }}>
          {data.iterations} itér.
        </div>
      )}

      <Handle type="source" position={Position.Bottom} style={{ background: '#ca8a04' }} />
    </div>
  );
};

export default VibrationNode;