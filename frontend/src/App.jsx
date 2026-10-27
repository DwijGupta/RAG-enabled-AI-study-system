import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar.jsx';
import Header from './components/Header.jsx';
import SourcesPanel from './components/SourcesPanel.jsx';
import ChatPanel from './components/ChatPanel.jsx';
import EvidencePanel from './components/EvidencePanel.jsx';
import HomeView from './components/HomeView.jsx';
import StudyToolsView from './components/StudyToolsView.jsx';
import LearningProgressView from './components/LearningProgressView.jsx';
import UploadModal from './components/UploadModal.jsx';
import CommandPalette from './components/CommandPalette.jsx';
import SettingsModal from './components/SettingsModal.jsx';

import { 
  initialNotebooks, 
  initialSources, 
  initialMessages, 
  citationsDatabase,
  mockLearnerProfile
} from './data/mockData.js';

export default function App() {
  // Theme State with persistent local storage
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('studybuddy_theme') || 'dark';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('studybuddy_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  // Global Navigation & Views
  const [currentView, setCurrentView] = useState('notebook'); // 'notebook' | 'home' | 'flashcards' | 'quizzes' | 'progress'
  const [studyToolsTab, setStudyToolsTab] = useState('study-guide');
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  // Notebooks & Active Workspace
  const [notebooks, setNotebooks] = useState(initialNotebooks);
  const [currentNotebook, setCurrentNotebook] = useState(initialNotebooks[0]);
  const [sources, setSources] = useState(initialSources);

  // Side Panels Shiftable & Resizable State
  const [isSourcesPanelOpen, setIsSourcesPanelOpen] = useState(true);
  const [isEvidencePanelOpen, setIsEvidencePanelOpen] = useState(true);
  const [sourcesWidth, setSourcesWidth] = useState(280);
  const [evidenceWidth, setEvidenceWidth] = useState(340);
  const [isResizingLeft, setIsResizingLeft] = useState(false);
  const [isResizingRight, setIsResizingRight] = useState(false);

  // Citations & Evidence Panel
  const [activeCitationId, setActiveCitationId] = useState('cit-1');

  // Tutor Mode & Chat Messages
  const [tutorMode, setTutorMode] = useState('Learn');
  const [messages, setMessages] = useState([
    {
      id: 'msg-welcome',
      sender: 'tutor',
      timestamp: 'Just now',
      mode: 'Learn',
      content: "### Welcome to AI Study Buddy!\nUpload course textbooks, lecture slides, or notes on the left, or ask any question to start learning."
    }
  ]);
  const [isGenerating, setIsGenerating] = useState(false);

  // Chat Memory & Sessions
  const [chatSessions, setChatSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState('session_default');

  // Modals
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);

  // Handle panel shift/resize drag events
  useEffect(() => {
    const handleMouseMove = (e) => {
      if (isResizingLeft) {
        const sidebarWidth = isSidebarCollapsed ? 64 : 240;
        const newWidth = e.clientX - sidebarWidth;
        if (newWidth >= 180 && newWidth <= 520) {
          setSourcesWidth(newWidth);
        }
      } else if (isResizingRight) {
        const newWidth = window.innerWidth - e.clientX;
        if (newWidth >= 220 && newWidth <= 650) {
          setEvidenceWidth(newWidth);
        }
      }
    };

    const handleMouseUp = () => {
      setIsResizingLeft(false);
      setIsResizingRight(false);
    };

    if (isResizingLeft || isResizingRight) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    } else {
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    }

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizingLeft, isResizingRight, isSidebarCollapsed]);

  // Synchronize chat sessions from backend memory
  const fetchSessions = async () => {
    try {
      const res = await fetch('/api/chat/sessions?user_id=student_1');
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data) && data.length > 0) {
          setChatSessions(data);
        }
      }
    } catch (err) {
      console.warn('Could not fetch sessions from backend:', err);
    }
  };

  // Synchronize documents from backend ingestion
  const fetchSources = async () => {
    try {
      const res = await fetch('/api/ingestion/documents');
      if (res.ok) {
        const docs = await res.json();
        if (Array.isArray(docs) && docs.length > 0) {
          const mapped = docs.map((d) => ({
            id: d.id,
            name: d.title || 'Untitled Document',
            type: d.source_type === 'image' ? 'image' : d.source_type === 'web' ? 'web' : 'pdf',
            pages: d.total_pages || 1,
            chunks: d.total_pages ? `${d.total_pages} pages` : 'Indexed',
            status: d.status || 'Indexed & Ready',
            active: true,
            badge: (d.source_type || 'PDF').toUpperCase()
          }));
          setSources(mapped);
          setNotebooks((prev) =>
            prev.map((nb) =>
              nb.id === currentNotebook.id ? { ...nb, sourcesCount: mapped.length } : nb
            )
          );
        }
      }
    } catch (err) {
      console.warn('Could not fetch documents from backend:', err);
    }
  };

  useEffect(() => {
    fetchSessions();
    fetchSources();
  }, []);

  // Keyboard shortcut listener for Command Palette (Ctrl+K / Cmd+K)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setIsCommandPaletteOpen((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Source Handlers
  const handleToggleSourceActive = (sourceId) => {
    setSources((prev) =>
      prev.map((s) => (s.id === sourceId ? { ...s, active: !s.active } : s))
    );
  };

  const handleSelectAllSources = () => {
    setSources((prev) => prev.map((s) => ({ ...s, active: true })));
  };

  const handleClearAllSources = () => {
    setSources((prev) => prev.map((s) => ({ ...s, active: false })));
  };

  const handleAddSource = (newSource) => {
    setSources((prev) => [newSource, ...prev]);
    setNotebooks((prev) =>
      prev.map((nb) =>
        nb.id === currentNotebook.id ? { ...nb, sourcesCount: nb.sourcesCount + 1 } : nb
      )
    );
    setTimeout(fetchSources, 800);
  };

  const handleRemoveSource = async (sourceId) => {
    try {
      await fetch(`/api/ingestion/document/${sourceId}`, { method: 'DELETE' });
    } catch (err) {
      console.warn('Backend delete document failed, removing locally:', err);
    }
    setSources((prev) => prev.filter((s) => s.id !== sourceId));
    setNotebooks((prev) =>
      prev.map((nb) =>
        nb.id === currentNotebook.id ? { ...nb, sourcesCount: Math.max(0, nb.sourcesCount - 1) } : nb
      )
    );
  };

  const handleNewNotebook = () => {
    const newId = `nb-${Date.now()}`;
    const newNb = {
      id: newId,
      title: 'Untitled Study Notebook',
      course: 'New Course Track',
      sourcesCount: 0,
      lastActive: 'Just now',
      progress: 0,
      color: '#3B82F6',
      pinned: false,
      description: 'Upload textbooks, lecture transcripts, and syllabus materials to begin studying.'
    };
    setNotebooks([newNb, ...notebooks]);
    setCurrentNotebook(newNb);
    setSources([]);
    handleNewSession();
    setCurrentView('notebook');
  };

  const handleUpdateNotebookTitle = (newTitle) => {
    setCurrentNotebook((prev) => ({ ...prev, title: newTitle }));
    setNotebooks((prev) =>
      prev.map((nb) => (nb.id === currentNotebook.id ? { ...nb, title: newTitle } : nb))
    );
  };

  // Citation Handlers
  const handleSelectCitation = (citId) => {
    setActiveCitationId(citId);
    setIsEvidencePanelOpen(true);
  };

  const handleNavigateCitation = (direction) => {
    const citKeys = Object.keys(citationsDatabase);
    const currIndex = citKeys.indexOf(activeCitationId);
    if (currIndex === -1) {
      setActiveCitationId(citKeys[0]);
      return;
    }
    if (direction === 'next') {
      setActiveCitationId(citKeys[(currIndex + 1) % citKeys.length]);
    } else {
      setActiveCitationId(citKeys[(currIndex - 1 + citKeys.length) % citKeys.length]);
    }
  };

  // Chat Memory Handlers
  const handleSelectSession = async (sessionId) => {
    setCurrentSessionId(sessionId);
    setCurrentView('notebook');
    try {
      const res = await fetch(`/api/chat/history/${sessionId}`);
      if (res.ok) {
        const data = await res.json();
        if (data.messages && data.messages.length > 0) {
          setMessages(data.messages);
          const firstTutorWithCitations = data.messages.find(
            (m) => m.sender === 'tutor' && m.citations && m.citations.length > 0
          );
          if (firstTutorWithCitations) {
            setActiveCitationId(firstTutorWithCitations.citations[0]);
          }
          return;
        }
      }
    } catch (err) {
      console.error('Error fetching session history:', err);
    }
    // Fallback welcome if empty
    setMessages([
      {
        id: 'msg-welcome',
        sender: 'tutor',
        timestamp: 'Just now',
        mode: tutorMode,
        content: `### Session: ${sessionId}\nAsk any question grounded in your course materials!`
      }
    ]);
  };

  const handleNewSession = () => {
    const newSessionId = `session_${Date.now()}`;
    setCurrentSessionId(newSessionId);
    setMessages([
      {
        id: 'msg-welcome',
        sender: 'tutor',
        timestamp: 'Just now',
        mode: tutorMode,
        content: `### Welcome to your study session!

1. Upload or select your sources (PDFs, Diagrams, Concept Images, or Web Pages) on the left.
2. Ask any complex concept or exam-style question.
3. Every response is grounded in real-time vector embeddings and knowledge graph evidence with clickable citation chips.`
      }
    ]);
    setCurrentView('notebook');
  };

  const handleDeleteSession = async (sessionId) => {
    try {
      await fetch(`/api/chat/session/${sessionId}`, { method: 'DELETE' });
    } catch (err) {
      console.error('Error deleting session:', err);
    }
    setChatSessions((prev) => prev.filter((s) => s.session_id !== sessionId));
    if (currentSessionId === sessionId) {
      handleNewSession();
    }
  };

  const handleClearChat = async () => {
    try {
      await fetch(`/api/chat/session/${currentSessionId}`, { method: 'DELETE' });
    } catch (err) {
      console.error('Error clearing chat session:', err);
    }
    fetchSessions();
    setMessages([
      {
        id: 'msg-welcome',
        sender: 'tutor',
        timestamp: 'Just now',
        mode: tutorMode,
        content: `### Chat memory cleared for this session.
Ask any new question to continue studying!`
      }
    ]);
  };

  const handleDeleteMessage = async (msgId) => {
    const msg = messages.find((m) => m.id === msgId);
    if (msg?.trace_id) {
      try {
        await fetch(`/api/chat/message/${msg.trace_id}`, { method: 'DELETE' });
      } catch (err) {
        console.error('Error deleting message trace:', err);
      }
    }
    setMessages((prev) => prev.filter((m) => m.id !== msgId));
  };

  // Real-Time RAG Chat Message Handler
  const handleSendMessage = async (text) => {
    const userMsg = {
      id: `msg-${Date.now()}`,
      sender: 'user',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      content: text
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsGenerating(true);

    try {
      const res = await fetch('/api/chat/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'student_1',
          session_id: currentSessionId,
          query: text
        })
      });

      if (res.ok) {
        const data = await res.json();
        const replyCitations = data.citations && data.citations.length > 0 ? data.citations : [];
        const tutorReply = {
          id: `msg-${Date.now() + 1}`,
          sender: 'tutor',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          mode: data.planner_action || tutorMode,
          content: data.answer || "No response generated.",
          citations: replyCitations,
          rationale: data.rationale,
          faithfulness: data.faithfulness_score,
          diagnosedWeakness: data.diagnosed_weakness
        };

        setMessages((prev) => [...prev, tutorReply]);
        setIsGenerating(false);

        if (replyCitations.length > 0) {
          setActiveCitationId(replyCitations[0]);
          setIsEvidencePanelOpen(true);
        }

        fetchSessions();
        return;
      } else {
        const errorData = await res.text();
        let errMsg = `Server returned status ${res.status}`;
        try {
          const parsed = JSON.parse(errorData);
          if (parsed.detail) errMsg = parsed.detail;
        } catch (_) {
          if (errorData) errMsg = errorData.slice(0, 200);
        }

        setMessages((prev) => [
          ...prev,
          {
            id: `msg-err-${Date.now()}`,
            sender: 'tutor',
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            mode: 'Notice',
            content: `⚠️ **Could not generate answer:** ${errMsg}\n\nPlease check that your Gemini API key is valid and the backend is running.`
          }
        ]);
        setIsGenerating(false);
      }
    } catch (err) {
      console.error('Chat API request error:', err);
      setMessages((prev) => [
        ...prev,
        {
          id: `msg-err-${Date.now()}`,
          sender: 'tutor',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          mode: 'Offline',
          content: `⚠️ **Connection Error:** Could not reach backend server at \`/api/chat/message\` (${err.message}).\n\nPlease ensure the backend server is running on port 8000.`
        }
      ]);
      setIsGenerating(false);
    }
  };

  const activeSources = sources.filter((s) => s.active);

  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw', overflow: 'hidden' }}>
      {/* 1. Persistent Left Navigation Sidebar */}
      <Sidebar
        currentView={currentView}
        setCurrentView={setCurrentView}
        notebooks={notebooks}
        currentNotebook={currentNotebook}
        onSelectNotebook={(nb) => {
          setCurrentNotebook(nb);
          setCurrentView('notebook');
        }}
        onNewNotebook={handleNewNotebook}
        onOpenSettings={() => setIsSettingsOpen(true)}
        onOpenCommandPalette={() => setIsCommandPaletteOpen(true)}
        theme={theme}
        onToggleTheme={toggleTheme}
        isCollapsed={isSidebarCollapsed}
        setIsCollapsed={setIsSidebarCollapsed}
        chatSessions={chatSessions}
        currentSessionId={currentSessionId}
        onSelectSession={handleSelectSession}
        onNewSession={handleNewSession}
        onDeleteSession={handleDeleteSession}
      />

      {/* 2. Main Workspace Surface */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%', minWidth: 0, overflow: 'hidden' }}>
        {/* VIEW A: NOTEBOOK WORKSPACE (Core centerpiece) */}
        {currentView === 'notebook' && (
          <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minWidth: 0 }}>
            {/* Notebook Workspace Header */}
            <Header
              notebook={currentNotebook}
              onUpdateNotebookTitle={handleUpdateNotebookTitle}
              activeSourcesCount={activeSources.length}
              totalSourcesCount={sources.length}
              tutorMode={tutorMode}
              setTutorMode={setTutorMode}
              onOpenStudyGuide={() => {
                setStudyToolsTab('study-guide');
                setCurrentView('study-tools');
              }}
              onOpenFlashcards={() => {
                setStudyToolsTab('flashcards');
                setCurrentView('flashcards');
              }}
              onOpenQuiz={() => {
                setStudyToolsTab('quiz');
                setCurrentView('quizzes');
              }}
              onOpenNotes={() => {
                setStudyToolsTab('study-guide');
                setCurrentView('study-tools');
              }}
              onOpenCommandPalette={() => setIsCommandPaletteOpen(true)}
              theme={theme}
              onToggleTheme={toggleTheme}
              onGoHome={() => setCurrentView('home')}
              isSourcesOpen={isSourcesPanelOpen}
              onToggleSources={() => setIsSourcesPanelOpen((prev) => !prev)}
              isEvidenceOpen={isEvidencePanelOpen}
              onToggleEvidence={() => setIsEvidencePanelOpen((prev) => !prev)}
            />

            {/* 3-Column Split-Pane Layout with Shiftable Dividers */}
            <div style={{ flex: 1, display: 'flex', minHeight: 0, overflow: 'hidden', position: 'relative' }}>
              {/* Left Column: Sources Panel */}
              {isSourcesPanelOpen && (
                <SourcesPanel
                  sources={sources}
                  onToggleSourceActive={handleToggleSourceActive}
                  onSelectAllSources={handleSelectAllSources}
                  onClearAllSources={handleClearAllSources}
                  onOpenUpload={() => setIsUploadOpen(true)}
                  onRemoveSource={handleRemoveSource}
                  onSelectSourcePreview={(src) => {
                    setActiveCitationId(src.name || 'cit-1');
                    setIsEvidencePanelOpen(true);
                  }}
                  width={sourcesWidth}
                  onCollapse={() => setIsSourcesPanelOpen(false)}
                />
              )}

              {/* Resizer Splitter between Sources and Chat */}
              {isSourcesPanelOpen && (
                <div
                  style={{
                    width: '6px',
                    cursor: 'col-resize',
                    backgroundColor: isResizingLeft ? 'var(--brand-primary, #6366F1)' : 'transparent',
                    transition: 'background-color 0.15s ease',
                    zIndex: 15,
                    userSelect: 'none',
                    position: 'relative',
                    margin: '0 -3px',
                    borderLeft: '1px solid var(--border-subtle, rgba(255,255,255,0.06))'
                  }}
                  onMouseDown={() => setIsResizingLeft(true)}
                  title="Drag to resize Sources panel"
                />
              )}

              {/* Center Column: AI Tutoring & Chat Workspace */}
              <ChatPanel
                notebookTitle={currentNotebook?.title || 'Active Study Session'}
                messages={messages}
                onSendMessage={handleSendMessage}
                onSelectCitation={handleSelectCitation}
                activeCitationId={activeCitationId}
                tutorMode={tutorMode}
                setTutorMode={setTutorMode}
                activeSourcesCount={activeSources.length}
                onOpenUpload={() => setIsUploadOpen(true)}
                isGenerating={isGenerating}
                onClearChat={handleClearChat}
                onDeleteMessage={handleDeleteMessage}
                isSourcesOpen={isSourcesPanelOpen}
                onToggleSources={() => setIsSourcesPanelOpen((prev) => !prev)}
                isEvidenceOpen={isEvidencePanelOpen}
                onToggleEvidence={() => setIsEvidencePanelOpen((prev) => !prev)}
              />

              {/* Resizer Splitter between Chat and Evidence */}
              {isEvidencePanelOpen && (
                <div
                  style={{
                    width: '6px',
                    cursor: 'col-resize',
                    backgroundColor: isResizingRight ? 'var(--brand-primary, #6366F1)' : 'transparent',
                    transition: 'background-color 0.15s ease',
                    zIndex: 15,
                    userSelect: 'none',
                    position: 'relative',
                    margin: '0 -3px',
                    borderRight: '1px solid var(--border-subtle, rgba(255,255,255,0.06))'
                  }}
                  onMouseDown={() => setIsResizingRight(true)}
                  title="Drag to resize Evidence panel"
                />
              )}

              {/* Right Column: Contextual Evidence & Cited Source Panel */}
              {isEvidencePanelOpen && (
                <EvidencePanel
                  activeCitationId={activeCitationId}
                  onClose={() => setIsEvidencePanelOpen(false)}
                  onNavigateCitation={handleNavigateCitation}
                  activeSources={activeSources}
                  width={evidenceWidth}
                />
              )}
            </div>
          </div>
        )}

        {/* VIEW B: HOME VIEW */}
        {currentView === 'home' && (
          <HomeView
            notebooks={notebooks}
            onSelectNotebook={(nb) => {
              setCurrentNotebook(nb);
              setCurrentView('notebook');
            }}
            onNewNotebook={handleNewNotebook}
            onOpenUpload={() => setIsUploadOpen(true)}
            onOpenFlashcards={() => {
              setStudyToolsTab('flashcards');
              setCurrentView('flashcards');
            }}
            onOpenCommandPalette={() => setIsCommandPaletteOpen(true)}
          />
        )}

        {/* VIEW C: STUDY TOOLS / FLASHCARDS / QUIZZES */}
        {(currentView === 'study-tools' || currentView === 'flashcards' || currentView === 'quizzes') && (
          <StudyToolsView
            initialTab={currentView === 'flashcards' ? 'flashcards' : currentView === 'quizzes' ? 'quiz' : studyToolsTab}
            notebookTitle={currentNotebook?.title || 'Machine Learning Fundamentals'}
            onClose={() => setCurrentView('notebook')}
          />
        )}

        {/* VIEW D: LEARNING PROGRESS & COGNITIVE MEMORY */}
        {currentView === 'progress' && (
          <LearningProgressView
            profile={mockLearnerProfile}
            onPracticeConcept={(concept) => {
              setCurrentView('notebook');
              handleSendMessage(`Give me an exam-style practice problem on ${concept}`);
            }}
          />
        )}
      </div>

      {/* Global Modals */}
      <UploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onAddSource={handleAddSource}
      />

      <CommandPalette
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
        notebooks={notebooks}
        onSelectNotebook={(nb) => {
          setCurrentNotebook(nb);
          setCurrentView('notebook');
        }}
        onNewNotebook={handleNewNotebook}
        onOpenUpload={() => setIsUploadOpen(true)}
        onOpenFlashcards={() => {
          setStudyToolsTab('flashcards');
          setCurrentView('flashcards');
        }}
        onOpenQuiz={() => {
          setStudyToolsTab('quiz');
          setCurrentView('quizzes');
        }}
        onOpenProgress={() => setCurrentView('progress')}
        onToggleTheme={toggleTheme}
        theme={theme}
      />

      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        theme={theme}
        onToggleTheme={toggleTheme}
        tutorMode={tutorMode}
        setTutorMode={setTutorMode}
      />
    </div>
  );
}
