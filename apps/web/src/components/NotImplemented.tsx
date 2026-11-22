import React from 'react';
import { AlertCircle, ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';

interface NotImplementedProps {
  moduleName: string;
  plannedTask: string;
  description: string;
}

export const NotImplemented: React.FC<NotImplementedProps> = ({
  moduleName,
  plannedTask,
  description,
}) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100%',
        minHeight: '400px',
        padding: '32px',
        textAlign: 'center',
        background: '#0a1128',
        borderRadius: '8px',
        border: '1px dashed #1e3a8a',
        margin: '24px',
      }}
    >
      <div
        style={{
          width: '56px',
          height: '56px',
          borderRadius: '50%',
          backgroundColor: 'rgba(239, 71, 111, 0.15)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#ef476f',
          marginBottom: '16px',
        }}
      >
        <AlertCircle size={32} />
      </div>

      <div
        style={{
          display: 'inline-block',
          backgroundColor: '#ef476f',
          color: '#ffffff',
          fontWeight: 700,
          fontSize: '0.75rem',
          padding: '3px 10px',
          borderRadius: '4px',
          letterSpacing: '0.05em',
          marginBottom: '12px',
        }}
      >
        STATUS: NOT_IMPLEMENTED
      </div>

      <h2 style={{ fontSize: '1.4rem', fontWeight: 600, color: '#f8fafc', marginBottom: '8px' }}>
        {moduleName}
      </h2>

      <p style={{ color: '#94a3b8', maxWidth: '520px', fontSize: '0.9rem', lineHeight: 1.5, marginBottom: '16px' }}>
        {description}
      </p>

      <div
        style={{
          background: '#0d1b38',
          border: '1px solid #1e293b',
          padding: '10px 16px',
          borderRadius: '6px',
          fontSize: '0.8rem',
          color: '#38bdf8',
          marginBottom: '24px',
          fontFamily: 'monospace',
        }}
      >
        Scheduled for Development: <strong>{plannedTask}</strong>
      </div>

      <Link
        to="/dashboard"
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '8px',
          backgroundColor: '#1b2f5b',
          color: '#f8fafc',
          padding: '8px 16px',
          borderRadius: '6px',
          fontSize: '0.85rem',
          textDecoration: 'none',
          fontWeight: 500,
        }}
      >
        <ArrowLeft size={16} /> Return to Operations Dashboard
      </Link>
    </div>
  );
};

