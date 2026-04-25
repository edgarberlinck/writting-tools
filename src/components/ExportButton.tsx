import { useMemo, useState } from "react";
import { FiDownload } from "react-icons/fi";
import jsPDF from "jspdf";
import html2canvas from "html2canvas";
import {
  SUPPORTED_LOCALES,
  type Chapter,
  type Section,
  type Project,
} from "../db/types";

interface Props {
  project: Project;
  chapter: Chapter | null;
  section: Section | null;
  locale: string;
  chapters: Chapter[];
  sectionsByChapter: Record<string, Section[]>;
}

type ExportMode = "current" | "entire";
type ExportTarget = { title: string; html: string };

const MM_TO_PX = 3.7795275591;

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function sanitizeFilename(value: string): string {
  return value.replace(/[\\/:*?"<>|]/g, "-").trim() || "book";
}

function getLocalizedHtml(entity: Chapter | Section, locale: string): string {
  return (
    entity.languages.find((l) => l.locale === locale)?.content ||
    "<p>No content</p>"
  );
}

export default function ExportButton({
  project,
  chapter,
  section,
  locale,
  chapters,
  sectionsByChapter,
}: Props) {
  const [exporting, setExporting] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [exportMode, setExportMode] = useState<ExportMode>("current");
  const [exportLocale, setExportLocale] = useState(locale);
  const [includeMoodboards, setIncludeMoodboards] = useState(false);

  const hasCurrentSelection = Boolean(chapter);
  const hasBookContent = chapters.length > 0;
  const exportableChapters = includeMoodboards
    ? chapters
    : chapters.filter((ch) => ch.chapterType !== "moodboard");

  const currentSelectionLabel = useMemo(() => {
    if (!chapter) return "No selection";
    if (section) return `${chapter.title} - ${section.title}`;
    return chapter.title;
  }, [chapter, section]);

  const buildCurrentSelectionHtml = (lang: string): ExportTarget | null => {
    if (!chapter || chapter.chapterType === "moodboard") return null;

    if (section) {
      const title = `${chapter.title} - ${section.title}`;
      const html = `
        <article>
          <h1>${escapeHtml(chapter.title)}</h1>
          <h2>${escapeHtml(section.title)}</h2>
          ${getLocalizedHtml(section, lang)}
        </article>
      `;
      return { title, html };
    }

    const chapterSections = sectionsByChapter[chapter._id] || [];
    const html = `
      <article>
        <h1>${escapeHtml(chapter.title)}</h1>
        ${getLocalizedHtml(chapter, lang)}
        ${chapterSections
          .map(
            (s) => `
          <section>
            <h2>${escapeHtml(s.title)}</h2>
            ${getLocalizedHtml(s, lang)}
          </section>
        `,
          )
          .join("")}
      </article>
    `;
    return { title: chapter.title, html };
  };

  const buildEntireBookTargets = (
    lang: string,
  ): { title: string; chapters: ExportTarget[] } | null => {
    if (exportableChapters.length === 0) return null;
    const chapterTargets = exportableChapters.map((ch) => {
      const chapterSections = sectionsByChapter[ch._id] || [];
      const chapterParts = [
        getLocalizedHtml(ch, lang),
        ...chapterSections.map((s) => getLocalizedHtml(s, lang)),
      ].filter((part) => part && part.trim().length > 0);

      const html = `
        <article>
          <h1>${escapeHtml(ch.title)}</h1>
          ${chapterParts
            .map(
              (part, partIdx) => `
            ${partIdx > 0 ? '<div class="section-separator">----</div>' : ""}
            <section>${part}</section>
          `,
            )
            .join("")}
        </article>
      `;
      return { title: ch.title, html };
    });

    return {
      title: `${project.title} - Entire Book`,
      chapters: chapterTargets,
    };
  };

  const createStyledContainer = (
    contentHtml: string,
    contentWidthPx: number,
  ): HTMLDivElement => {
    const container = document.createElement("div");
    container.innerHTML = contentHtml;
    container.style.cssText = `
      position:fixed; top:-9999px; left:-9999px;
      width:${contentWidthPx}px;
      padding:0;
      font-family:${project.config.fonts.body.family};
      font-size:${project.config.fonts.body.size}pt;
      line-height:${project.config.lineSpacing};
      background:#fff; color:#000;
    `;

    const h1 = project.config.fonts.title;
    const h2 = project.config.fonts.subtitle;
    const style = document.createElement("style");
    style.innerHTML = `
      h1 {
        margin: 0 0 12px;
        font-family: ${h1.family};
        font-size: ${h1.size}pt;
        font-weight: ${h1.bold ? "700" : "400"};
      }
      h2 {
        margin: 24px 0 10px;
        font-family: ${h2.family};
        font-size: ${h2.size}pt;
        font-weight: ${h2.bold ? "700" : "400"};
      }
      .section-separator {
        margin: 22px 0;
        text-align: center;
        color: #666;
        letter-spacing: 0.15em;
        font-family: ${project.config.fonts.subtitle.family};
        font-size: ${Math.max(10, project.config.fonts.subtitle.size - 2)}pt;
        font-weight: ${project.config.fonts.subtitle.bold ? "700" : "400"};
      }
      p { margin: 0 0 10px; }
    `;
    container.appendChild(style);
    return container;
  };

  const renderContainerToCanvas = async (
    container: HTMLDivElement,
  ): Promise<HTMLCanvasElement> => {
    document.body.appendChild(container);
    try {
      return await html2canvas(container, {
        scale: 2,
        useCORS: true,
        backgroundColor: "#ffffff",
      });
    } finally {
      document.body.removeChild(container);
    }
  };

  const addCanvasToPdf = (
    pdf: jsPDF,
    canvas: HTMLCanvasElement,
    contentWidthMm: number,
    pageHeightMm: number,
  ) => {
    const imgData = canvas.toDataURL("image/png");
    const imgWidthMm = contentWidthMm;
    const imgHeightMm = (canvas.height * imgWidthMm) / canvas.width;
    const usableHeightMm = Math.max(
      1,
      pageHeightMm - project.config.margins.top - project.config.margins.bottom,
    );

    let renderedHeight = 0;
    while (renderedHeight < imgHeightMm) {
      if (renderedHeight > 0) pdf.addPage();
      const offsetY = project.config.margins.top - renderedHeight;
      pdf.addImage(
        imgData,
        "PNG",
        project.config.margins.left,
        offsetY,
        imgWidthMm,
        imgHeightMm,
      );
      renderedHeight += usableHeightMm;
    }
  };

  const handleExport = async () => {
    const singleTarget =
      exportMode === "current" ? buildCurrentSelectionHtml(exportLocale) : null;
    const entireTarget =
      exportMode === "entire" ? buildEntireBookTargets(exportLocale) : null;
    if (!singleTarget && !entireTarget) return;

    setExporting(true);
    try {
      const pageSize = project.config.pageSize.toLowerCase();
      const format =
        pageSize === "letter" ? "letter" : (pageSize as "a4" | "a5");
      const pdf = new jsPDF({ format, unit: "mm" });
      const pageWidthMm = pdf.internal.pageSize.getWidth();
      const pageHeightMm = pdf.internal.pageSize.getHeight();

      const contentWidthMm = Math.max(
        1,
        pageWidthMm -
          project.config.margins.left -
          project.config.margins.right,
      );
      const contentWidthPx = contentWidthMm * MM_TO_PX;

      if (singleTarget) {
        const container = createStyledContainer(
          singleTarget.html,
          contentWidthPx,
        );
        const canvas = await renderContainerToCanvas(container);
        addCanvasToPdf(pdf, canvas, contentWidthMm, pageHeightMm);
        pdf.save(`${sanitizeFilename(singleTarget.title)}.pdf`);
      } else if (entireTarget) {
        for (const [index, chapterTarget] of entireTarget.chapters.entries()) {
          if (index > 0) pdf.addPage();
          const container = createStyledContainer(
            chapterTarget.html,
            contentWidthPx,
          );
          const canvas = await renderContainerToCanvas(container);
          addCanvasToPdf(pdf, canvas, contentWidthMm, pageHeightMm);
        }
        pdf.save(`${sanitizeFilename(entireTarget.title)}.pdf`);
      }
      setMenuOpen(false);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setMenuOpen((v) => !v)}
        disabled={exporting || !hasBookContent}
        className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50 transition-colors"
      >
        <FiDownload className="w-4 h-4" />
        {exporting ? "Exporting..." : "Export to PDF"}
      </button>

      {menuOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-white border border-gray-200 rounded-xl shadow-xl z-20 p-4 space-y-4">
          <div>
            <p className="text-sm font-semibold text-gray-900">Export Mode</p>
            <div className="mt-2 space-y-2">
              <label className="flex items-start gap-2 text-sm text-gray-700">
                <input
                  type="radio"
                  name="export-mode"
                  checked={exportMode === "current"}
                  onChange={() => setExportMode("current")}
                  disabled={!hasCurrentSelection}
                  className="mt-1"
                />
                <span>
                  <span className="font-medium">Current selection</span>
                  <span className="block text-xs text-gray-500">
                    {hasCurrentSelection
                      ? currentSelectionLabel
                      : "Select a chapter or section first"}
                  </span>
                </span>
              </label>

              <label className="flex items-start gap-2 text-sm text-gray-700">
                <input
                  type="radio"
                  name="export-mode"
                  checked={exportMode === "entire"}
                  onChange={() => setExportMode("entire")}
                  className="mt-1"
                />
                <span>
                  <span className="font-medium">Entire Book</span>
                  <span className="block text-xs text-gray-500">
                    Export all chapters and sections
                  </span>
                </span>
              </label>
            </div>
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-900 mb-2">
              Language
            </label>
            <select
              value={exportLocale}
              onChange={(e) => setExportLocale(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {SUPPORTED_LOCALES.map((l) => (
                <option
                  key={l.code}
                  value={l.code}
                >{`${l.label} (${l.code})`}</option>
              ))}
            </select>
          </div>

          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input
              type="checkbox"
              checked={includeMoodboards}
              onChange={(e) => setIncludeMoodboards(e.target.checked)}
            />
            <span>Include Moodboards</span>
          </label>

          <div className="flex justify-end gap-2">
            <button
              onClick={() => setMenuOpen(false)}
              className="px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg"
            >
              Cancel
            </button>
            <button
              onClick={handleExport}
              disabled={
                exporting || (exportMode === "current" && !hasCurrentSelection)
              }
              className="px-3 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
            >
              {exporting ? "Exporting..." : "Export"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
