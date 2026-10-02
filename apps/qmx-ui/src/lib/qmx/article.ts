/**
 * Load and prepare a Library article for reading. Today the text comes from
 * the dev-only demo route (/__demo/mql5/<id>, behind QMX_DEMO_MQL5_DIR);
 * the daemon's Library replaces it. Scraped markup is always sanitised.
 */
import { marked } from "marked";
import DOMPurify from "dompurify";

export type ArticleText =
  | {
      status: "ready";
      html: string;
      toc: { id: string; text: string; level: number }[];
      figures: string[];
    }
  | { status: "no-text" };

/** Drop front matter and the scraped page chrome above the first section. */
export function cleanArticle(md: string): string {
  let body = md.replace(/\r\n?/g, "\n").replace(/^---\n[\s\S]*?\n---\n/, "");
  const first = body.search(/^#{2,3} (?!Contents\b)/m);
  if (first >= 0) body = body.slice(first);
  return body;
}

export async function loadArticleText(
  id: string | number,
): Promise<ArticleText> {
  const res = await fetch(
    `/__demo/mql5/${encodeURIComponent(String(id))}`,
  ).catch(() => null);
  if (!res?.ok) return { status: "no-text" };
  const raw = await marked.parse(cleanArticle(await res.text()), { gfm: true });
  const doc = new DOMParser().parseFromString(
    DOMPurify.sanitize(raw, { FORBID_TAGS: ["style", "form", "iframe"] }),
    "text/html",
  );
  const toc: { id: string; text: string; level: number }[] = [];
  doc.querySelectorAll("h2, h3").forEach((h, i) => {
    if (!h.textContent?.trim()) {
      h.remove();
      return;
    }
    h.id = `s-${i}`;
    toc.push({
      id: h.id,
      text: h.textContent ?? "",
      level: h.tagName === "H2" ? 2 : 3,
    });
  });
  doc.querySelectorAll("a").forEach((a) => {
    a.setAttribute("target", "_blank");
    a.setAttribute("rel", "noopener noreferrer");
  });
  const figures: string[] = [];
  doc.querySelectorAll("img").forEach((img) => {
    img.setAttribute("loading", "lazy");
    const src = img.getAttribute("src");
    if (
      src &&
      !src.endsWith(".svg") &&
      !src.includes("icons") &&
      !src.includes("overlay")
    )
      figures.push(src);
  });
  return {
    status: "ready",
    html: doc.body.innerHTML,
    toc,
    figures: figures.slice(0, 12),
  };
}
