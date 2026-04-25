import { renderHook, act, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Project } from "../../db/types";
import { DEFAULT_PROJECT_CONFIG } from "../../db/types";

const { repositoryMock } = vi.hoisted(() => ({
  repositoryMock: {
    getProjects: vi.fn<() => Promise<Project[]>>(),
    deleteProject: vi.fn<(project: Project) => Promise<void>>(),
  },
}));

vi.mock("../../db", () => ({
  repository: repositoryMock,
}));

import { useProjects } from "../useProjects";

function makeProject(id: string, updatedAt: string, title = "Book"): Project {
  return {
    _id: id,
    type: "project",
    title,
    author: "",
    description: "",
    config: DEFAULT_PROJECT_CONFIG,
    chapterOrder: [],
    createdAt: updatedAt,
    updatedAt,
    _rev: `rev-${id}`,
  };
}

describe("useProjects", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("loads and sorts projects by updatedAt desc", async () => {
    const oldDate = "2026-01-01T00:00:00.000Z";
    const newDate = "2026-02-01T00:00:00.000Z";
    repositoryMock.getProjects.mockResolvedValue([
      makeProject("old", oldDate, "Old"),
      makeProject("new", newDate, "New"),
    ]);

    const { result } = renderHook(() => useProjects());

    await act(async () => {
      await result.current.load();
    });

    expect(result.current.projects.map((p) => p._id)).toEqual(["new", "old"]);
    expect(result.current.loading).toBe(false);
  });

  it("sets loading=true while loading", async () => {
    let resolve!: (projects: Project[]) => void;
    repositoryMock.getProjects.mockReturnValue(
      new Promise<Project[]>((r) => {
        resolve = r;
      }),
    );

    const { result } = renderHook(() => useProjects());

    act(() => {
      void result.current.load();
    });

    expect(result.current.loading).toBe(true);

    resolve([]);
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
  });

  it("removes a project and refreshes list", async () => {
    const project = makeProject("p1", "2026-03-01T00:00:00.000Z");
    repositoryMock.deleteProject.mockResolvedValue();
    repositoryMock.getProjects
      .mockResolvedValueOnce([project])
      .mockResolvedValueOnce([]);

    const { result } = renderHook(() => useProjects());

    await act(async () => {
      await result.current.load();
    });

    await act(async () => {
      await result.current.remove(project);
    });

    expect(repositoryMock.deleteProject).toHaveBeenCalledWith(project);
    expect(repositoryMock.getProjects).toHaveBeenCalledTimes(2);
    expect(result.current.projects).toEqual([]);
  });
});
