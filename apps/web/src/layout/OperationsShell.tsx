import React from 'react';
import { TopBar } from './TopBar';
import { Sidebar } from './Sidebar';

interface OperationsShellProps {
  children: React.ReactNode;
}

export const OperationsShell: React.FC<OperationsShellProps> = ({ children }) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        width: '100vw',
        overflow: 'hidden',
        backgroundColor: '#070d1e',
      }}
    >
      <TopBar />
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        <Sidebar />
        <main
          style={{
            flex: 1,
            overflowY: 'auto',
            position: 'relative',
            backgroundColor: '#070d1e',
          }}
        >
          {children}
        </main>
      </div>
    </div>
  );
};
