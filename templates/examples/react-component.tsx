import React from 'react';

const HelloConductor: React.FC = () => {
  return (
    <div style={{ 
      padding: '2rem', 
      textAlign: 'center', 
      fontFamily: 'Arial, sans-serif',
      backgroundColor: '#f0f0f0',
      borderRadius: '8px',
      margin: '1rem'
    }}>
      <h1>🎼 Hello from Conductor!</h1>
      <p>Your {{team_name}} is ready to go!</p>
      <div style={{ marginTop: '1rem' }}>
        <p><strong>Status:</strong> ✅ Active</p>
        <p><strong>Team:</strong> {{team_name}}</p>
        <p><strong>Project:</strong> {{project_name}}</p>
        <p><strong>Environment:</strong> {{environment}}</p>
        <p><strong>Agents:</strong> Configured Successfully</p>
      </div>
      <button 
        onClick={() => alert('Conductor team is working!')}
        style={{
          padding: '0.5rem 1rem',
          backgroundColor: '#007bff',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer',
          marginTop: '1rem'
        }}
      >
        Test Team
      </button>
    </div>
  );
};

export default HelloConductor;