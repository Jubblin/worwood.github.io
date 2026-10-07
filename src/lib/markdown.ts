import { marked } from "marked";

// Mirrors Hugo's `markdownify`: renders markdown (raw HTML allowed, as hugo.yaml sets
// goldmark unsafe: true) and unwraps a lone paragraph.
export function md(text?: string | null): string {
  if (!text) return "";
  // ponytail: only in-word apostrophes get Hugo's typographer treatment (I'm -> I’m);
  // swap in a smartypants extension if quotes/dashes ever need matching too.
  const html = (marked.parse(String(text).trim(), { async: false }) as string).trim().replace(/(\w)(?:'|&#39;)(\w)/g, "$1’$2");
  const m = html.match(/^<p>([\s\S]*)<\/p>$/);
  return m && !m[1].includes("<p>") ? m[1] : html;
}
