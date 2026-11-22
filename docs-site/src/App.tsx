import React, { useState, useEffect } from 'react';
import { DOCS_SECTIONS, DocSection } from './data/docsContent';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { DocViewer } from './components/DocViewer';
import { SearchModal } from './components/SearchModal';

export const App: React.FC = () => {
  const [theme, setTheme] = useState<'dark' | 'light'>(() => {
    return (localStorage.getItem('clearway_docs_theme') as 'dark' | 'light') || 'dark';
  });

  const [activeDocId, setActiveDocId] = useState<string>(() => {
    // Read URL hash if available (e.g. #architecture)
    const hash = window.location.hash.replace('#', '');
    return DOCS_SECTIONS.some((s) => s.id === hash) ? hash : 'introduction';
  });

  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('clearway_docs_theme', theme);
  }, [theme]);

  // Synchronize hash on doc change
  const handleSelectDoc = (id: string) => {
    setActiveDocId(id);
    window.location.hash = id;
    window.scrollTo({ top: 0, behavior: 'smooth' });
    setIsMobileSidebarOpen(false);
  };

  const currentSectionIndex = DOCS_SECTIONS.findIndex((s) => s.id === activeDocId);
  const currentSection = DOCS_SECTIONS[currentSectionIndex] || DOCS_SECTIONS[0];
  const prevSection = currentSectionIndex > 0 ? DOCS_SECTIONS[currentSectionIndex - 1] : undefined;
  const nextSection = currentSectionIndex < DOCS_SECTIONS.length - 1 ? DOCS_SECTIONS[currentSectionIndex + 1] : undefined;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', backgroundColor: 'var(--bg-primary)' }}>
      {/* Top Header */}
      <Header
        theme={theme}
        onToggleTheme={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
        onOpenSearch={() => setIsSearchOpen(true)}
        onToggleMobileSidebar={() => setIsMobileSidebarOpen(!isMobileSidebarOpen)}
      />

      {/* Main Layout Area */}
      <div style={{ display: 'flex', flex: 1, position: 'relative' }}>
        <Sidebar
          sections={DOCS_SECTIONS}
          activeId={activeDocId}
          onSelect={handleSelectDoc}
          isOpenMobile={isMobileSidebarOpen}
        />

        <main style={{ flex: 1, overflowX: 'hidden' }}>
          <DocViewer
            section={currentSection}
            onNavigate={handleSelectDoc}
            prevSection={prevSection}
            nextSection={nextSection}
          />
        </main>
      </div>

      {/* Global Search Modal */}
      <SearchModal
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
        onSelect={handleSelectDoc}
      />
    </div>
  );
};

export default App;
