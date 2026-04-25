import { beforeEach, describe, expect, it, vi } from "vitest";

const pouchCtor = vi.fn(function MockPouchDB(
  this: Record<string, unknown>,
  _name: string,
) {
  return {};
});

vi.mock("pouchdb-browser", () => ({
  default: pouchCtor,
}));

describe("db/index", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("creates repository singleton with the expected PouchDB name", async () => {
    const mod = await import("../index");

    expect(pouchCtor).toHaveBeenCalledWith("writing-tools");
    expect(mod.repository).toBeInstanceOf(mod.BookRepository);
  });

  it("exports the same singleton across imports", async () => {
    const first = await import("../index");
    const second = await import("../index");

    expect(first.repository).toBe(second.repository);
  });
});
