import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';
import type { Project, Chapter, Section } from '../db/types';
import * as db from '../db';

interface AppContextType {
  projects: Project[];
  loadProjects: () => Promise<void>;
  currentProject: Project | null;
  setCurrentProject: (p: Project | null) => void;
  chapters: Chapter[];
  loadChapters: (projectId: string) => Promise<void>;
  sections: Record<string, Section[]>;
  loadSections: (chapterId: string) => Promise<void>;
  selectedChapterId: string | null;
  setSelectedChapterId: (id: string | null) => void;
  selectedSectionId: string | null;
  setSelectedSectionId: (id: string | null) => void;
  selectedLocale: string;
  setSelectedLocale: (locale: string) => void;
}

const AppContext = createContext<AppContextType | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [currentProject, setCurrentProject] = useState<Project | null>(null);
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [sections, setSections] = useState<Record<string, Section[]>>({});
  const [selectedChapterId, setSelectedChapterId] = useState<string | null>(null);
  const [selectedSectionId, setSelectedSectionId] = useState<string | null>(null);
  const [selectedLocale, setSelectedLocale] = useState('en');

  const loadProjects = useCallback(async () => {
    const list = await db.getProjects();
    setProjects(list.sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()));
  }, []);

  const loadChapters = useCallback(async (projectId: string) => {
    const list = await db.getChaptersByProject(projectId);
    setChapters(list);
  }, []);

  const loadSections = useCallback(async (chapterId: string) => {
    const list = await db.getSectionsByChapter(chapterId);
    setSections((prev) => ({ ...prev, [chapterId]: list }));
  }, []);

  return (
    <AppContext.Provider value={{
      projects, loadProjects,
      currentProject, setCurrentProject,
      chapters, loadChapters,
      sections, loadSections,
      selectedChapterId, setSelectedChapterId,
      selectedSectionId, setSelectedSectionId,
      selectedLocale, setSelectedLocale,
    }}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp must be used within AppProvider');
  return ctx;
}
