import React from 'react';
import { DocSection } from '../data/docsContent';
import { BookOpen, CheckCircle, Clock } from 'lucide-react';

interface SidebarProps {
  sections: DocSection[];
  activeId: string;
  onSelect: (id: string) => void;
  isOpenMobile?: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  sections,
  activeId,
  onSelect,
  isOpenMobile,
}) => {
  // Group by category
  const categories: Record<string, DocSection[]> = {};
  sections.forEach((sec) => {
    if (!categories[sec.category]) {
      categories[sec.category] = [];
    }
    categories[sec.category].push(sec);
  });

  return (
    <aside
      className={`docs-sidebar ${isOpenMobile ? 'mobile-open' : ''}`}
      style={{
        width: '290px',
        flexShrink: 0,
        backgroundColor: 'var(--bg-secondary)',
        borderRight: '1px solid var(--border-color)',
        height: 'calc(100vh - 60px)',
        overflowY: 'auto',
        padding: '20px 14px',
        position: 'sticky',
        top: '60px',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          padding: '10px 12px',
          marginBottom: '18px',
          backgroundColor: 'rgba(56, 189, 248, 0.06)',
          borderRadius: '8px',
          border: '1px solid rgba(56, 189, 248, 0.25)',
        }}
      >
        <img
          src={`${import.meta.env.BASE_URL}logo.jpg`}
          alt="ClearWay AI"
          style={{
            width: '28px',
            height: '28px',
            borderRadius: '6px',
            objectFit: 'cover',
          }}
          onError={(e) => {
            (e.currentTarget as HTMLImageElement).src = '/logo.jpg';
          }}
        />
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <span style={{ fontSize: '0.85rem', fontWeight: 800, color: 'var(--text-primary)' }}>ClearWay AI</span>
          <span style={{ fontSize: '0.65rem', color: 'var(--accent-cyan)', fontWeight: 600 }}>v0.1.0-mvp • 60/60 Tasks</span>
        </div>
      </div>

      <div style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)', fontSize: '0.78rem', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 700 }}>
        <BookOpen size={14} color="var(--accent-cyan)" />
        <span>Documentation Topics</span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
        {Object.entries(categories).map(([category, items]) => (
          <div key={category}>
            <div
              style={{
                fontSize: '0.75rem',
                fontWeight: 700,
                color: 'var(--text-muted)',
                marginBottom: '8px',
                paddingLeft: '8px',
                letterSpacing: '0.03em',
              }}
            >
              {category}
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
              {items.map((item) => {
                const isActive = item.id === activeId;
                const isVerified = item.status === 'VERIFIED';

                return (
                  <button
                    key={item.id}
                    onClick={() => onSelect(item.id)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      width: '100%',
                      padding: '7px 10px',
                      borderRadius: '6px',
                      border: 'none',
                      backgroundColor: isActive ? 'var(--bg-tertiary)' : 'transparent',
                      color: isActive ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                      fontWeight: isActive ? 600 : 400,
                      fontSize: '0.82rem',
                      textAlign: 'left',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                      borderLeft: isActive ? '3px solid var(--accent-cyan)' : '3px solid transparent',
                    }}
                  >
                    <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {item.title}
                    </span>

                    {/* Status indicator */}
                    <span
                      title={isVerified ? 'Module Verified with Test Evidence' : 'Module Planned in Roadmap'}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        fontSize: '0.65rem',
                        padding: '1px 5px',
                        borderRadius: '4px',
                        backgroundColor: isVerified ? 'rgba(16, 185, 129, 0.15)' : 'rgba(148, 163, 184, 0.1)',
                        color: isVerified ? 'var(--accent-emerald)' : 'var(--text-muted)',
                        marginLeft: '6px',
                      }}
                    >
                      {isVerified ? <CheckCircle size={10} style={{ marginRight: '2px' }} /> : <Clock size={10} style={{ marginRight: '2px' }} />}
                      {isVerified ? 'VERIFIED' : 'PLAN'}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
};

