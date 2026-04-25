import { renderHook, act, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Chapter, Project, Section } from "../../db/types";
import { DEFAULT_PROJECT_CONFIG } from "../../db/types";
import { BookRepository } from "../../db/repository";

const { repositoryMock } = vi.hoisted(() => ({
  repositoryMock: {
    getProject: vi.fn<(id: string) => Promise<Project>>(),
    getChaptersByProject: vi.fn<(projectId: string) => Promise<Chapter[]>>(),
    getSectionsByChapter: vi.fn<(chapterId: string) => Promise<Section[]>>(),
    saveProject: vi.fn<(project: Project) => Promise<Project>>(),
    saveChapter: vi.fn<(chapter: Chapter) => Promise<Chapter>>(),
    deleteChapter: vi.fn<(chapter: Chapter) => Promise<void>>(),
    saveSection: vi.fn<(section: Section) => Promise<Section>>(),
    deleteSection: vi.fn<(section: Section) => Promise<void>>(),
  },
}));

vi.mock("../../db", () => ({
  repository: repositoryMock,
}));

import { useBookEditor } from "../useBookEditor";

function makeProject(overrides: Partial<Project> = {}): Project {
  const now = "2026-01-01T00:00:00.000Z";
  return {
    _id: "p1",
    type: "project",
    title: "Book",
    author: "",
    description: "",
    config: DEFAULT_PROJECT_CONFIG,
    chapterOrder: ["c1"],
    createdAt: now,
    updatedAt: now,
    _rev: "1-p",
    ...overrides,
  };
}

function makeChapter(overrides: Partial<Chapter> = {}): Chapter {
  const now = "2026-01-01T00:00:00.000Z";
  return {
    _id: "c1",
    type: "chapter",
    projectId: "p1",
    title: "Chapter 1",
    chapterType: "regular",
    sectionOrder: ["s1"],
    languages: [{ locale: "en", content: "<p>Chapter EN</p>" }],
    createdAt: now,
    updatedAt: now,
    _rev: "1-c",
    ...overrides,
  };
}

function makeSection(overrides: Partial<Section> = {}): Section {
  const now = "2026-01-01T00:00:00.000Z";
  return {
    _id: "s1",
    type: "section",
    chapterId: "c1",
    title: "Section 1",
    languages: [{ locale: "en", content: "<p>Section EN</p>" }],
    createdAt: now,
    updatedAt: now,
    _rev: "1-s",
    ...overrides,
  };
}

describe("useBookEditor", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    repositoryMock.getProject.mockResolvedValue(makeProject());
    repositoryMock.getChaptersByProject.mockResolvedValue([makeChapter()]);
    repositoryMock.getSectionsByChapter.mockResolvedValue([makeSection()]);
    repositoryMock.saveProject.mockImplementation(async (p) => p);
    repositoryMock.saveChapter.mockImplementation(async (c) => c);
    repositoryMock.saveSection.mockImplementation(async (s) => s);
    repositoryMock.deleteChapter.mockResolvedValue();
    repositoryMock.deleteSection.mockResolvedValue();
  });

  it("loads project/chapters/sections and exposes derived state", async () => {
    const { result } = renderHook(() => useBookEditor("p1"));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
      expect(result.current.project?._id).toBe("p1");
    });

    act(() => {
      result.current.setSelectedChapterId("c1");
      result.current.setSelectedSectionId("s1");
    });

    await waitFor(() => {
      expect(result.current.selectedChapter?.title).toBe("Chapter 1");
      expect(result.current.selectedSection?.title).toBe("Section 1");
      expect(result.current.editorContent).toContain("Section EN");
    });
  });

  it("adds chapter and selects it", async () => {
    const idSpy = vi
      .spyOn(BookRepository, "generateId")
      .mockReturnValue("c_new");
    const project = makeProject();
    repositoryMock.getProject.mockResolvedValue(project);
    repositoryMock.saveChapter.mockResolvedValue(
      makeChapter({ _id: "c_new", title: "New regular" }),
    );

    const { result } = renderHook(() => useBookEditor("p1"));
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.addChapter("regular");
    });

    expect(repositoryMock.saveChapter).toHaveBeenCalled();
    expect(repositoryMock.saveProject).toHaveBeenCalledWith(
      expect.objectContaining({ chapterOrder: ["c1", "c_new"] }),
    );
    expect(result.current.selectedChapterId).toBe("c_new");

    idSpy.mockRestore();
  });

  it("adds section and selects it", async () => {
    const idSpy = vi
      .spyOn(BookRepository, "generateId")
      .mockReturnValue("s_new");
    const chapter = makeChapter({ sectionOrder: [] });
    repositoryMock.getChaptersByProject.mockResolvedValue([chapter]);
    repositoryMock.saveSection.mockResolvedValue(
      makeSection({ _id: "s_new", chapterId: "c1", title: "New Section" }),
    );

    const { result } = renderHook(() => useBookEditor("p1"));
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.addSection(chapter);
    });

    expect(repositoryMock.saveSection).toHaveBeenCalled();
    expect(repositoryMock.saveChapter).toHaveBeenCalledWith(
      expect.objectContaining({ _id: "c1", sectionOrder: ["s_new"] }),
    );
    expect(result.current.selectedSectionId).toBe("s_new");

    idSpy.mockRestore();
  });

  it("saves chapter content with selected locale", async () => {
    const chapter = makeChapter({ languages: [] });
    repositoryMock.getChaptersByProject.mockResolvedValue([chapter]);
    repositoryMock.getSectionsByChapter.mockResolvedValue([]);

    const { result } = renderHook(() => useBookEditor("p1"));
    await waitFor(() => expect(result.current.loading).toBe(false));

    act(() => {
      result.current.setSelectedChapterId("c1");
      result.current.setSelectedLocale("pt-BR");
    });

    await act(async () => {
      await result.current.saveContent("<p>Ola</p>");
    });

    expect(repositoryMock.saveChapter).toHaveBeenCalledWith(
      expect.objectContaining({
        _id: "c1",
        languages: [{ locale: "pt-BR", content: "<p>Ola</p>" }],
      }),
    );
  });

  it("saves section content for explicit locale and returns localized content", async () => {
    const section = makeSection({
      languages: [{ locale: "fr", content: "<p>Bonjour</p>" }],
    });
    repositoryMock.getSectionsByChapter.mockResolvedValue([section]);

    const { result } = renderHook(() => useBookEditor("p1"));
    await waitFor(() => expect(result.current.loading).toBe(false));

    act(() => {
      result.current.setSelectedChapterId("c1");
      result.current.setSelectedSectionId("s1");
    });

    expect(result.current.getContentForLocale("fr")).toContain("Bonjour");

    await act(async () => {
      await result.current.saveContentForLocale("<p>Salut</p>", "fr");
    });

    expect(repositoryMock.saveSection).toHaveBeenCalledWith(
      expect.objectContaining({
        _id: "s1",
        languages: [{ locale: "fr", content: "<p>Salut</p>" }],
      }),
    );
  });

  it("deletes selected section and clears current selection", async () => {
    const section = makeSection();

    const { result } = renderHook(() => useBookEditor("p1"));
    await waitFor(() => expect(result.current.loading).toBe(false));

    act(() => {
      result.current.setSelectedChapterId("c1");
      result.current.setSelectedSectionId("s1");
    });

    await act(async () => {
      await result.current.deleteSection(section);
    });

    expect(repositoryMock.deleteSection).toHaveBeenCalledWith(section);
    expect(result.current.selectedSectionId).toBeNull();
  });

  it("deletes selected chapter, updates order and clears selection", async () => {
    const chapter = makeChapter({ _id: "c1" });

    const { result } = renderHook(() => useBookEditor("p1"));
    await waitFor(() => expect(result.current.loading).toBe(false));

    act(() => {
      result.current.setSelectedChapterId("c1");
    });

    await act(async () => {
      await result.current.deleteChapter(chapter);
    });

    expect(repositoryMock.deleteChapter).toHaveBeenCalledWith(chapter);
    expect(repositoryMock.saveProject).toHaveBeenCalledWith(
      expect.objectContaining({ chapterOrder: [] }),
    );
    expect(result.current.selectedChapterId).toBeNull();
    expect(result.current.selectedSectionId).toBeNull();
  });

  it("reorders chapters", async () => {
    const { result } = renderHook(() => useBookEditor("p1"));
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.reorderChapters(["c2", "c1"]);
    });

    expect(repositoryMock.saveProject).toHaveBeenCalledWith(
      expect.objectContaining({ chapterOrder: ["c2", "c1"] }),
    );
  });

  it("saveContentForLocale updates chapter content when no section is selected", async () => {
    repositoryMock.getSectionsByChapter.mockResolvedValue([]);

    const { result } = renderHook(() => useBookEditor("p1"));
    await waitFor(() => expect(result.current.loading).toBe(false));

    act(() => {
      result.current.setSelectedChapterId("c1");
      result.current.setSelectedSectionId(null);
    });

    await act(async () => {
      await result.current.saveContentForLocale("<p>Hola</p>", "es");
    });

    expect(repositoryMock.saveChapter).toHaveBeenCalledWith(
      expect.objectContaining({
        _id: "c1",
        languages: expect.arrayContaining([
          expect.objectContaining({ locale: "es", content: "<p>Hola</p>" }),
        ]),
      }),
    );
  });

  it("returns empty content when nothing is selected", async () => {
    const { result } = renderHook(() => useBookEditor("p1"));
    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.getContentForLocale("en")).toBe("");
  });

  it("is a no-op for mutating actions when projectId is undefined", async () => {
    const chapter = makeChapter();
    const section = makeSection();

    const { result } = renderHook(() => useBookEditor(undefined));

    await act(async () => {
      await result.current.addChapter("regular");
      await result.current.deleteChapter(chapter);
      await result.current.renameChapter(chapter, "Renamed");
      await result.current.reorderChapters(["c2"]);
      await result.current.addSection(chapter);
      await result.current.deleteSection(section);
      await result.current.reorderSections(chapter, ["s2"]);
      await result.current.saveContent("<p>x</p>");
      await result.current.saveContentForLocale("<p>x</p>", "en");
    });

    expect(repositoryMock.saveProject).not.toHaveBeenCalled();
    expect(repositoryMock.saveChapter).not.toHaveBeenCalled();
    expect(repositoryMock.saveSection).not.toHaveBeenCalled();
    expect(repositoryMock.deleteChapter).not.toHaveBeenCalled();
    expect(repositoryMock.deleteSection).not.toHaveBeenCalled();
  });
});
