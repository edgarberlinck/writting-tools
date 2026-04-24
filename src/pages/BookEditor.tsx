import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FiSettings, FiArrowLeft } from 'react-icons/fi';
import { useApp } from '../context/AppContext';
import Sidebar from '../components/Sidebar';
import Editor from '../components/Editor';
import LanguageTabs from '../components/LanguageTabs';
import ExportButton from '../components/ExportButton';
import {
  getProject, saveProject, saveChapter, deleteChapter as dbDeleteChapter,
  saveSection, deleteSection as dbDeleteSection, generateId,
} from '../db';
import type { Chapter, Section, ChapterType, LanguageContent } from '../db/types';

export default function BookEditor() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const {
    currentProject, setCurrentProject,
    chapters, loadChapters,
    sections, loadSections,
    selectedChapterId, setSelectedChapterId,
    selectedSectionId, setSelectedSectionId,
    selectedLocale, setSelectedLocale,
  } = useApp();

  const [loading, setLoading] = useState(true);
  const [saveTimer, setSaveTimer] = useState<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (id) {
      (async () => {
        const project = await getProject(id);
        setCurrentProject(project);
        await loadChapters(id);
        setLoading(false);
      })();
    }
  }, [id]);

  useEffect(() => {
    chapters.forEach((ch) => loadSections(ch._id));
  }, [chapters]);

  const orderedChapters = currentProject
    ? [...chapters].sort((a, b) => {
        const ai = currentProject.chapterOrder.indexOf(a._id);
        const bi = currentProject.chapterOrder.indexOf(b._id);
        return (ai === -1 ? 999 : ai) - (bi === -1 ? 999 : bi);
      })
    : chapters;

  const selectedChapter = chapters.find((c) => c._id === selectedChapterId) || null;
  const selectedSection = selectedSectionId
    ? (sections[selectedChapterId || ''] || []).find((s) => s._id === selectedSectionId) || null
    : null;

  const getContent = () => {
    const target = selectedSection || selectedChapter;
    if (!target) return '';
    return target.languages.find((l) => l.locale === selectedLocale)?.content || '';
  };

  const editorContent = getContent();

  function updateLocale(langs: LanguageContent[], locale: string, content: string): LanguageContent[] {
    const existing = langs.find((l) => l.locale === locale);
    if (existing) return langs.map((l) => l.locale === locale ? { ...l, content } : l);
    return [...langs, { locale, content }];
  }

  const handleContentChange = useCallback(async (html: string) => {
    if (saveTimer) clearTimeout(saveTimer);
    const timer = setTimeout(async () => {
      if (!selectedChapterId) return;
      if (selectedSection) {
        const updated: Section = {
          ...selectedSection,
          languages: updateLocale(selectedSection.languages, selectedLocale, html),
        };
        await saveSection(updated);
        await loadSections(selectedChapterId);
      } else if (selectedChapter) {
        const updated: Chapter = {
          ...selectedChapter,
          languages: updateLocale(selectedChapter.languages, selectedLocale, html),
        };
        await saveChapter(updated);
        await loadChapters(id!);
      }
    }, 800);
    setSaveTimer(timer);
  }, [selectedChapterId, selectedSectionId, selectedLocale, selectedChapter, selectedSection]);

  const handleAddChapter = async (type: ChapterType) => {
    if (!id || !currentProject) return;
    const now = new Date().toISOString();
    const chapter: Chapter = {
      _id: generateId('chapter'),
      type: 'chapter',
      projectId: id,
      title: `New ${type.replace(/_/g, ' ')}`,
      chapterType: type,
      sectionOrder: [],
      languages: [],
      createdAt: now,
      updatedAt: now,
    };
    const saved = await saveChapter(chapter);
    const updatedProject = {
      ...currentProject,
      chapterOrder: [...currentProject.chapterOrder, saved._id],
    };
    const savedProject = await saveProject(updatedProject);
    setCurrentProject(savedProject);
    await loadChapters(id);
    setSelectedChapterId(saved._id);
    setSelectedSectionId(null);
  };

  const handleDeleteChapter = async (chapter: Chapter) => {
    if (!currentProject) return;
    if (!confirm(`Delete chapter "${chapter.title}"?`)) return;
    await dbDeleteChapter(chapter);
    const updatedProject = {
      ...currentProject,
      chapterOrder: currentProject.chapterOrder.filter((cid) => cid !== chapter._id),
    };
    const savedProject = await saveProject(updatedProject);
    setCurrentProject(savedProject);
    await loadChapters(id!);
    if (selectedChapterId === chapter._id) {
      setSelectedChapterId(null);
      setSelectedSectionId(null);
    }
  };

  const handleRenameChapter = async (chapter: Chapter, title: string) => {
    await saveChapter({ ...chapter, title });
    await loadChapters(id!);
  };

  const handleReorderChapters = async (newIds: string[]) => {
    if (!currentProject) return;
    const updatedProject = { ...currentProject, chapterOrder: newIds };
    const savedProject = await saveProject(updatedProject);
    setCurrentProject(savedProject);
    await loadChapters(id!);
  };

  const handleAddSection = async (chapter: Chapter) => {
    const now = new Date().toISOString();
    const section: Section = {
      _id: generateId('section'),
      type: 'section',
      chapterId: chapter._id,
      title: 'New Section',
      languages: [],
      createdAt: now,
      updatedAt: now,
    };
    const saved = await saveSection(section);
    const updatedChapter = {
      ...chapter,
      sectionOrder: [...chapter.sectionOrder, saved._id],
    };
    await saveChapter(updatedChapter);
    await loadChapters(id!);
    await loadSections(chapter._id);
    setSelectedChapterId(chapter._id);
    setSelectedSectionId(saved._id);
  };

  const handleDeleteSection = async (section: Section) => {
    if (!confirm(`Delete section "${section.title}"?`)) return;
    const chapter = chapters.find((c) => c._id === section.chapterId);
    if (chapter) {
      await saveChapter({ ...chapter, sectionOrder: chapter.sectionOrder.filter((sid) => sid !== section._id) });
    }
    await dbDeleteSection(section);
    await loadChapters(id!);
    await loadSections(section.chapterId);
    if (selectedSectionId === section._id) setSelectedSectionId(null);
  };

  const handleRenameSection = async (section: Section, title: string) => {
    await saveSection({ ...section, title });
    await loadSections(section.chapterId);
  };

  const handleReorderSections = async (chapter: Chapter, newIds: string[]) => {
    await saveChapter({ ...chapter, sectionOrder: newIds });
    await loadChapters(id!);
    await loadSections(chapter._id);
  };

  const getOrderedSections = (chapter: Chapter) => {
    const chSections = sections[chapter._id] || [];
    return [...chSections].sort((a, b) => {
      const ai = chapter.sectionOrder.indexOf(a._id);
      const bi = chapter.sectionOrder.indexOf(b._id);
      return (ai === -1 ? 999 : ai) - (bi === -1 ? 999 : bi);
    });
  };

  const orderedSections: Record<string, Section[]> = {};
  orderedChapters.forEach((ch) => {
    orderedSections[ch._id] = getOrderedSections(ch);
  });

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-800 flex items-center justify-center">
        <div className="text-gray-400">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white border-b border-gray-200 px-4 py-2.5 flex items-center gap-3 flex-shrink-0">
        <button onClick={() => navigate('/')} className="p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors">
          <FiArrowLeft className="w-5 h-5" />
        </button>
        <div className="flex-1 min-w-0">
          <h1 className="text-base font-semibold text-gray-900 truncate">{currentProject?.title}</h1>
          {currentProject?.author && <p className="text-xs text-gray-500">{currentProject.author}</p>}
        </div>
        <LanguageTabs selectedLocale={selectedLocale} onChange={setSelectedLocale} />
        {currentProject && (
          <ExportButton
            project={currentProject}
            chapter={selectedChapter}
            section={selectedSection}
            locale={selectedLocale}
          />
        )}
        <button
          onClick={() => navigate(`/projects/${id}/settings`)}
          className="p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          title="Settings"
        >
          <FiSettings className="w-5 h-5" />
        </button>
      </header>

      <div className="flex flex-1 overflow-hidden">
        <Sidebar
          chapters={orderedChapters}
          sections={orderedSections}
          selectedChapterId={selectedChapterId}
          selectedSectionId={selectedSectionId}
          onSelectChapter={(cid) => { setSelectedChapterId(cid); setSelectedSectionId(null); }}
          onSelectSection={(cid, sid) => { setSelectedChapterId(cid); setSelectedSectionId(sid); }}
          onAddChapter={handleAddChapter}
          onDeleteChapter={handleDeleteChapter}
          onRenameChapter={handleRenameChapter}
          onReorderChapters={handleReorderChapters}
          onAddSection={handleAddSection}
          onDeleteSection={handleDeleteSection}
          onRenameSection={handleRenameSection}
          onReorderSections={handleReorderSections}
        />

        <div className="flex-1 overflow-y-auto p-6">
          {selectedChapter ? (
            <div>
              <div className="mb-4">
                <h2 className="text-xl font-bold text-gray-900">
                  {selectedSection ? selectedSection.title : selectedChapter.title}
                </h2>
                {selectedSection && (
                  <p className="text-sm text-gray-500 mt-0.5">Section of: {selectedChapter.title}</p>
                )}
              </div>
              <Editor key={`${selectedChapterId}-${selectedSectionId}-${selectedLocale}`} content={editorContent} onChange={handleContentChange} />
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-center py-20">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                <FiSettings className="w-8 h-8 text-gray-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-500">Select a chapter</h3>
              <p className="text-gray-400 mt-1 text-sm">Choose a chapter from the sidebar to start writing.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
