import PouchDB from 'pouchdb-browser';
import type { Project, Chapter, Section } from './types';

const db = new PouchDB('writing-tools');

export async function getProjects(): Promise<Project[]> {
  const result = await db.allDocs({ include_docs: true });
  return result.rows
    .map((r) => r.doc as unknown as Project)
    .filter((doc) => doc && doc.type === 'project');
}

export async function getProject(id: string): Promise<Project> {
  return db.get(id) as unknown as Promise<Project>;
}

export async function saveProject(project: Project): Promise<Project> {
  project.updatedAt = new Date().toISOString();
  const result = await db.put(project);
  return { ...project, _rev: result.rev };
}

export async function deleteProject(project: Project): Promise<void> {
  const chapters = await getChaptersByProject(project._id);
  for (const chapter of chapters) {
    await deleteChapter(chapter);
  }
  await db.remove(project._id, project._rev!);
}

export async function getChaptersByProject(projectId: string): Promise<Chapter[]> {
  const result = await db.allDocs({ include_docs: true });
  return result.rows
    .map((r) => r.doc as unknown as Chapter)
    .filter((doc) => doc && doc.type === 'chapter' && doc.projectId === projectId);
}

export async function getChapter(id: string): Promise<Chapter> {
  return db.get(id) as unknown as Promise<Chapter>;
}

export async function saveChapter(chapter: Chapter): Promise<Chapter> {
  chapter.updatedAt = new Date().toISOString();
  const result = await db.put(chapter);
  return { ...chapter, _rev: result.rev };
}

export async function deleteChapter(chapter: Chapter): Promise<void> {
  const sections = await getSectionsByChapter(chapter._id);
  for (const section of sections) {
    await deleteSection(section);
  }
  await db.remove(chapter._id, chapter._rev!);
}

export async function getSectionsByChapter(chapterId: string): Promise<Section[]> {
  const result = await db.allDocs({ include_docs: true });
  return result.rows
    .map((r) => r.doc as unknown as Section)
    .filter((doc) => doc && doc.type === 'section' && doc.chapterId === chapterId);
}

export async function getSection(id: string): Promise<Section> {
  return db.get(id) as unknown as Promise<Section>;
}

export async function saveSection(section: Section): Promise<Section> {
  section.updatedAt = new Date().toISOString();
  const result = await db.put(section);
  return { ...section, _rev: result.rev };
}

export async function deleteSection(section: Section): Promise<void> {
  await db.remove(section._id, section._rev!);
}

export function generateId(prefix: string): string {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
}
