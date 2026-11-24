import React, { useState } from 'react';
import { DocSection } from '../data/docsContent';
import { Copy, Check, ChevronRight, AlertTriangle, ShieldCheck, Tag, ArrowLeft, ArrowRight } from 'lucide-react';

interface DocViewerProps {
  section: DocSection;
  onNavigate: (id: string) => void;
  prevSection?: DocSection;
  nextSection?: DocSection;
}

export const DocViewer: React.FC<DocViewerProps> = ({
  section,
  onNavigate,
  prevSection,
  nextSection,
}) => {
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  const handleCopy = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(code);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  // Basic markdown-like block renderer
  const renderFormattedContent = (raw: string) => {
    const lines = raw.trim().split('\n');
    const elements: React.ReactNode[] = [];
    let inCodeBlock = false;
    let codeBuffer: string[] = [];
    let codeLang = '';

    lines.forEach((line, idx) => {
      // Code blocks
      if (line.startsWith('```')) {
        if (inCodeBlock) {
          const fullCode = codeBuffer.join('\n');
          elements.push(
            <div key={`code-${idx}`} style={{ position: 'relative', margin: '16px 0' }}>
              <button
                onClick={() => handleCopy(fullCode)}
                style={{
                  position: 'absolute',
                  top: '8px',
                  right: '8px',
                  backgroundColor: 'var(--bg-tertiary)',
                  border: '1px solid var(--border-color)',
                  color: 'var(--text-secondary)',
                  borderRadius: '4px',
                  padding: '4px 8px',
                  fontSize: '0.72rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  cursor: 'pointer',
                  zIndex: 2,
                }}
              >
                {copiedCode === fullCode ? <Check size={12} color="var(--accent-emerald)" /> : <Copy size={12} />}
                {copiedCode === fullCode ? 'Copied' : 'Copy'}
              </button>
              <pre>
                <code>{fullCode}</code>
              </pre>
            </div>
          );
          codeBuffer = [];
          inCodeBlock = false;
        } else {
          inCodeBlock = true;
          codeLang = line.replace('```', '').trim();
        }
        return;
      }

      if (inCodeBlock) {
        codeBuffer.push(line);
        return;
      }

      // Headers
      if (line.startsWith('# ')) {
        elements.push(<h1 key={idx}>{line.replace('# ', '')}</h1>);
        return;
      }
      if (line.startsWith('## ')) {
        elements.push(<h2 key={idx}>{line.replace('## ', '')}</h2>);
        return;
      }
      if (line.startsWith('### ')) {
        elements.push(<h3 key={idx}>{line.replace('### ', '')}</h3>);
        return;
      }

      // Callout alerts
      if (line.startsWith('> [!IMPORTANT]')) {
        elements.push(
          <div key={idx} className="callout callout-important">
            <strong style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--accent-rose)' }}>
              <AlertTriangle size={16} /> IMPORTANT SAFETY NOTICE
            </strong>
          </div>
        );
        return;
      }
      if (line.startsWith('> [!NOTE]')) {
        elements.push(
          <div key={idx} className="callout callout-note">
            <strong style={{ color: 'var(--accent-blue)' }}>NOTE / REFERENCE CONTEXT</strong>
          </div>
        );
        return;
      }

      // Blockquotes
      if (line.startsWith('> ')) {
        elements.push(
          <blockquote key={idx} style={{ borderLeft: '3px solid var(--accent-cyan)', paddingLeft: '12px', margin: '8px 0', color: 'var(--text-secondary)' }}>
            {line.replace('> ', '')}
          </blockquote>
        );
        return;
      }

      // Unordered lists
      if (line.startsWith('- ')) {
        elements.push(<li key={idx}>{line.replace('- ', '')}</li>);
        return;
      }

      // Empty lines
      if (!line.trim()) {
        return;
      }

      // Normal paragraph
      elements.push(<p key={idx}>{line}</p>);
    });

    return elements;
  };

  return (
    <div style={{ flex: 1, padding: '32px 40px', maxWidth: '960px', margin: '0 auto', width: '100%' }}>
      {/* Breadcrumbs */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
        <span>Docs</span>
        <ChevronRight size={13} />
        <span>{section.category}</span>
        <ChevronRight size={13} />
        <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{section.title}</span>
      </div>

      {/* Task & Status Metadata Bar */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          gap: '10px',
          padding: '8px 14px',
          backgroundColor: 'var(--bg-secondary)',
          border: '1px solid var(--border-color)',
          borderRadius: '8px',
          marginBottom: '24px',
          fontSize: '0.78rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <Tag size={13} color="var(--accent-cyan)" />
          <span style={{ color: 'var(--text-muted)' }}>Tasks:</span>
          {section.tasks.map((t) => (
            <span
              key={t}
              style={{
                backgroundColor: 'var(--bg-tertiary)',
                color: 'var(--accent-cyan)',
                fontFamily: 'monospace',
                fontWeight: 600,
                padding: '1px 6px',
                borderRadius: '4px',
                fontSize: '0.75rem',
              }}
            >
              {t}
            </span>
          ))}
        </div>

        <div style={{ color: 'var(--border-color)' }}>|</div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ color: 'var(--text-muted)' }}>Implementation State:</span>
          <span
            style={{
              padding: '2px 8px',
              borderRadius: '12px',
              fontWeight: 700,
              fontSize: '0.72rem',
              backgroundColor: section.status === 'VERIFIED' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
              color: section.status === 'VERIFIED' ? 'var(--accent-emerald)' : 'var(--accent-amber)',
              border: `1px solid ${section.status === 'VERIFIED' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`,
            }}
          >
            {section.status}
          </span>
        </div>
      </div>

      {/* Hero Banner for Introduction Section */}
      {section.id === 'introduction' && (
        <div
          style={{
            marginBottom: '28px',
            borderRadius: '10px',
            overflow: 'hidden',
            border: '1px solid var(--border-color)',
            boxShadow: '0 8px 30px rgba(0,0,0,0.35)',
          }}
        >
          <img
            src={`${import.meta.env.BASE_URL}banner.jpg`}
            alt="ClearWay AI Intelligent Traffic Management Platform"
            style={{ width: '100%', height: 'auto', display: 'block' }}
            onError={(e) => {
              (e.currentTarget as HTMLImageElement).src = '/banner.jpg';
            }}
          />
        </div>
      )}

      {/* Main Prose Article */}
      <article className="doc-prose">
        {renderFormattedContent(section.content)}
      </article>

      {/* Prev / Next Page Navigation */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginTop: '48px',
          paddingTop: '20px',
          borderTop: '1px solid var(--border-color)',
          gap: '16px',
        }}
      >
        {prevSection ? (
          <button
            onClick={() => onNavigate(prevSection.id)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              backgroundColor: 'var(--bg-secondary)',
              border: '1px solid var(--border-color)',
              color: 'var(--text-primary)',
              padding: '10px 16px',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '0.85rem',
              textAlign: 'left',
            }}
          >
            <ArrowLeft size={16} color="var(--accent-cyan)" />
            <div>
              <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Previous</div>
              <strong>{prevSection.title}</strong>
            </div>
          </button>
        ) : <div />}

        {nextSection ? (
          <button
            onClick={() => onNavigate(nextSection.id)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              backgroundColor: 'var(--bg-secondary)',
              border: '1px solid var(--border-color)',
              color: 'var(--text-primary)',
              padding: '10px 16px',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '0.85rem',
              textAlign: 'right',
            }}
          >
            <div>
              <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Next</div>
              <strong>{nextSection.title}</strong>
            </div>
            <ArrowRight size={16} color="var(--accent-cyan)" />
          </button>
        ) : <div />}
      </div>
    </div>
  );
};

