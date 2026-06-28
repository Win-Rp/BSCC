export interface RouteSeoMeta {
  title?: string;
  description?: string;
  keywords?: string[] | string;
  robots?: string;
  canonicalPath?: string;
  jsonLd?: Record<string, unknown> | Array<Record<string, unknown>>;
}

export interface ResolvedRouteSeo {
  title: string;
  description: string;
  keywords: string;
  robots: string;
  canonical: string;
  siteTitle: string;
  jsonLd?: RouteSeoMeta["jsonLd"];
}

export interface RouteHeadConfig {
  title: string;
  meta: Array<Record<string, string>>;
  link: Array<Record<string, string>>;
  script: Array<Record<string, unknown>>;
}

const SITE_URL = "https://biaoshu.mxitx.com";
const JSON_LD_ID = "route-jsonld";

function upsertMeta(name: string, content: string, attribute: "name" | "property" = "name") {
  let element = document.head.querySelector<HTMLMetaElement>(`meta[${attribute}="${name}"]`);

  if (!element) {
    element = document.createElement("meta");
    element.setAttribute(attribute, name);
    document.head.appendChild(element);
  }

  element.setAttribute("content", content);
}

function upsertLink(rel: string, href: string) {
  let element = document.head.querySelector<HTMLLinkElement>(`link[rel="${rel}"]`);

  if (!element) {
    element = document.createElement("link");
    element.setAttribute("rel", rel);
    document.head.appendChild(element);
  }

  element.setAttribute("href", href);
}

function removeJsonLd() {
  document.getElementById(JSON_LD_ID)?.remove();
}

function applyJsonLd(jsonLd?: RouteSeoMeta["jsonLd"]) {
  removeJsonLd();

  if (!jsonLd) {
    return;
  }

  const script = document.createElement("script");
  script.id = JSON_LD_ID;
  script.type = "application/ld+json";
  script.text = JSON.stringify(jsonLd);
  document.head.appendChild(script);
}

function resolveTemplate(value: string | undefined, siteTitle: string) {
  if (!value) {
    return siteTitle;
  }

  return value.split("{siteTitle}").join(siteTitle.trim() || "标书查重系统");
}

function toAbsoluteUrl(path: string) {
  if (/^https?:\/\//i.test(path)) {
    return path;
  }

  return `${SITE_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

export function resolveRouteSeo(
  seo: RouteSeoMeta | undefined,
  options?: { siteTitle?: string; currentPath?: string }
): ResolvedRouteSeo {
  const siteTitle = options?.siteTitle?.trim() || "标书查重系统";
  const currentPath = options?.currentPath || "/";
  const title = resolveTemplate(seo?.title, siteTitle);
  const description =
    seo?.description ||
    "提供标书查重、投标文件检查、围标风险排查、相似度比对与原文证据复核，支持 DOCX 与可复制文本 PDF。";
  const keywords = Array.isArray(seo?.keywords) ? seo?.keywords.join(",") : seo?.keywords;
  const robots = seo?.robots || "index,follow";
  const canonical = toAbsoluteUrl(seo?.canonicalPath || currentPath);

  return {
    title,
    description,
    keywords: keywords || "标书查重,免费标书查重,标书检查,标书合规,投标文件查重,围标风险排查",
    robots,
    canonical,
    siteTitle,
    jsonLd: seo?.jsonLd
  };
}

export function createHeadConfig(resolved: ResolvedRouteSeo): RouteHeadConfig {
  const jsonLdEntries = resolved.jsonLd
    ? (Array.isArray(resolved.jsonLd) ? resolved.jsonLd : [resolved.jsonLd]).map((entry, index) => ({
        key: `route-jsonld-${index}`,
        type: "application/ld+json",
        textContent: entry
      }))
    : [];

  return {
    title: resolved.title,
    meta: [
      { name: "description", content: resolved.description },
      { name: "keywords", content: resolved.keywords },
      { name: "robots", content: resolved.robots },
      { name: "application-name", content: resolved.siteTitle },
      { property: "og:title", content: resolved.title },
      { property: "og:description", content: resolved.description },
      { property: "og:type", content: "website" },
      { property: "og:url", content: resolved.canonical },
      { property: "og:locale", content: "zh_CN" }
    ],
    link: [{ rel: "canonical", href: resolved.canonical }],
    script: jsonLdEntries
  };
}

export function applyRouteSeo(
  seo: RouteSeoMeta | undefined,
  options?: { siteTitle?: string; currentPath?: string }
) {
  if (typeof document === "undefined") {
    return;
  }

  const resolved = resolveRouteSeo(seo, options);

  document.title = resolved.title;
  upsertMeta("description", resolved.description);
  upsertMeta("keywords", resolved.keywords);
  upsertMeta("robots", resolved.robots);
  upsertMeta("og:title", resolved.title, "property");
  upsertMeta("og:description", resolved.description, "property");
  upsertMeta("og:type", "website", "property");
  upsertMeta("og:url", resolved.canonical, "property");
  upsertMeta("og:locale", "zh_CN", "property");
  upsertMeta("application-name", resolved.siteTitle);
  upsertLink("canonical", resolved.canonical);
  applyJsonLd(resolved.jsonLd);
}
