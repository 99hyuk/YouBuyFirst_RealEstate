const svgDataUrl = (svg: string) => `data:image/svg+xml,${encodeURIComponent(svg)}`;

const iconSvg = (body: string) =>
  svgDataUrl(
    `<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">${body}</svg>`
  );

const sourceIcons: Record<string, string> = {
  'v.daum.net': iconSvg(
    '<rect x="5" y="6" width="22" height="20" rx="6" fill="#f59e0b"/><path d="M10 12h12M10 17h9M10 22h6" stroke="#fff" stroke-width="2.2" stroke-linecap="round"/>'
  ),
  'www.google.co.kr': iconSvg(
    '<circle cx="16" cy="16" r="10" fill="none" stroke="#4285f4" stroke-width="4"/><path d="M17 16h8" stroke="#34a853" stroke-width="4" stroke-linecap="round"/><path d="M9 23a10 10 0 0 1 0-14" stroke="#fbbc05" stroke-width="4" stroke-linecap="round"/><path d="M9 9a10 10 0 0 1 14 0" stroke="#ea4335" stroke-width="4" stroke-linecap="round"/>'
  ),
  'news.google.com': iconSvg(
    '<rect x="5" y="6" width="22" height="20" rx="5" fill="#4285f4"/><path d="M10 12h12M10 17h12M10 22h8" stroke="#fff" stroke-width="2.1" stroke-linecap="round"/><path d="M23 9v14" stroke="#34a853" stroke-width="2.4" stroke-linecap="round"/>'
  ),
  'www.youtube.com': iconSvg(
    '<rect x="4" y="9" width="24" height="14" rx="4.5" fill="#ff0033"/><path d="M14 13v6l6-3z" fill="#fff"/>'
  ),
  'blog.naver.com': iconSvg(
    '<rect x="6" y="6" width="20" height="20" rx="5" fill="#03c75a"/><path d="M10 12h12v2.5H10zm0 5h9v2.5h-9z" fill="#fff"/><path d="M19 21.5l4-4 1.8 1.8-4 4-2.5.7z" fill="#fff"/>'
  ),
  'news8253.tistory.com': iconSvg(
    '<rect x="6" y="6" width="20" height="20" rx="5" fill="#f97316"/><path d="M10 12h12M10 17h9M10 22h7" stroke="#fff" stroke-width="2.1" stroke-linecap="round"/>'
  ),
  'auctionguide.tistory.com': iconSvg(
    '<rect x="6" y="6" width="20" height="20" rx="5" fill="#f97316"/><path d="M10 12h12M10 17h9M10 22h7" stroke="#fff" stroke-width="2.1" stroke-linecap="round"/>'
  ),
  'cafe.naver.com': iconSvg(
    '<path d="M8 12h14v7a5.5 5.5 0 0 1-5.5 5.5h-3A5.5 5.5 0 0 1 8 19z" fill="#03c75a"/><path d="M22 14h2.2a3.2 3.2 0 0 1 0 6.4H22" fill="none" stroke="#03c75a" stroke-width="2.6"/><path d="M10 8.5h10" stroke="#03c75a" stroke-width="2.6" stroke-linecap="round"/><path d="M12 16h6" stroke="#fff" stroke-width="2.2" stroke-linecap="round"/>'
  ),
  'cafe.daum.net': iconSvg(
    '<path d="M6 9h20v13H16l-6 5v-5H6z" fill="#f97316"/><circle cx="13" cy="15.5" r="1.8" fill="#fff"/><circle cx="19" cy="15.5" r="1.8" fill="#fff"/>'
  ),
  'new.land.naver.com': iconSvg(
    '<path d="M6 25h20V13L16 6 6 13z" fill="#0f9f6e"/><path d="M12 25v-8h8v8M11 14h3M18 14h3" stroke="#fff" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"/>'
  ),
  'www.molit.go.kr': iconSvg(
    '<path d="M16 5 5 12h22zM7 14h18v3H7zm2 5h4v8H9zm7 0h4v8h-4zm7 0h4v8h-4zM6 28h22v2H6z" fill="#2563eb"/>'
  ),
  'www.reb.or.kr': iconSvg(
    '<path d="M7 17 16 9l9 8v10H7z" fill="#0f766e"/><path d="M12 24h3v-5h3v5h3M10 15l6-5 6 5" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round"/><path d="M23 25v-8M20 25v-5" stroke="#99f6e4" stroke-width="2" stroke-linecap="round"/>'
  ),
  'www.data.go.kr': iconSvg(
    '<ellipse cx="16" cy="8" rx="10" ry="4" fill="#7c3aed"/><path d="M6 8v15c0 2.4 4.5 4 10 4s10-1.6 10-4V8" fill="#7c3aed"/><path d="M6 15c0 2.4 4.5 4 10 4s10-1.6 10-4M6 22c0 2.4 4.5 4 10 4s10-1.6 10-4" fill="none" stroke="#ddd6fe" stroke-width="1.8"/>'
  ),
  'www.korea.kr': iconSvg(
    '<path d="M10 5h13v22H10z" fill="#1d4ed8"/><path d="M14 11h6M14 16h6M14 21h4" stroke="#fff" stroke-width="2.2" stroke-linecap="round"/><path d="M23 5l3 3v19h-3z" fill="#60a5fa"/>'
  ),
  'kbthink.com': iconSvg(
    '<rect x="5" y="6" width="22" height="20" rx="5" fill="#facc15"/><path d="M10 21V11M15 21v-6l6 6M16 15l5-4" stroke="#44330b" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>'
  ),
  'kremap.krihs.re.kr': iconSvg(
    '<rect x="5" y="6" width="22" height="20" rx="5" fill="#2563eb"/><path d="M10 22V12h12M10 18h9M10 14h5" stroke="#fff" stroke-width="2.1" stroke-linecap="round"/><path d="M20 22l4-5" stroke="#bfdbfe" stroke-width="2.1" stroke-linecap="round"/>'
  ),
  'www.cerik.re.kr': iconSvg(
    '<rect x="5" y="6" width="22" height="20" rx="5" fill="#0f766e"/><path d="M10 21h12M11 17l4-5 4 5 3-3" fill="none" stroke="#fff" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"/>'
  ),
  'cerik.re.kr': iconSvg(
    '<rect x="5" y="6" width="22" height="20" rx="5" fill="#0f766e"/><path d="M10 21h12M11 17l4-5 4 5 3-3" fill="none" stroke="#fff" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"/>'
  ),
  'www.bok.or.kr': iconSvg(
    '<circle cx="16" cy="16" r="11" fill="#1d4ed8"/><path d="M10 18h12M12 22h8M11 14l5-5 5 5" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>'
  ),
  'www.applyhome.co.kr': iconSvg(
    '<path d="M6 17 16 7l10 10v10H6z" fill="#ea580c"/><path d="m12 18 3 3 6-8" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'
  ),
  'www.khug.or.kr': iconSvg(
    '<path d="M6 16 16 7l10 9v10H6z" fill="#0f766e"/><path d="M11 20h10M13 24h6M11 16l5-4 5 4" stroke="#fff" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"/>'
  ),
  'www.hankyung.com': iconSvg(
    '<rect x="5" y="6" width="22" height="20" rx="5" fill="#1f4f8f"/><path d="M10 12h12M10 17h9M10 22h12" stroke="#fff" stroke-width="2.1" stroke-linecap="round"/>'
  ),
  'magazine.hankyung.com': iconSvg(
    '<rect x="5" y="5" width="22" height="22" rx="5" fill="#1f4f8f"/><path d="M10 11h12M10 16h10M10 21h7" stroke="#fff" stroke-width="2.1" stroke-linecap="round"/>'
  ),
  'www.mk.co.kr': iconSvg(
    '<rect x="5" y="6" width="22" height="20" rx="5" fill="#0f172a"/><path d="M10 22V11l6 5 6-5v11" fill="none" stroke="#fbbf24" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"/>'
  ),
  'www.sedaily.com': iconSvg(
    '<rect x="5" y="6" width="22" height="20" rx="5" fill="#ef4444"/><path d="M11 12h10M11 17h8M11 22h11" stroke="#fff" stroke-width="2.1" stroke-linecap="round"/>'
  ),
  'biz.chosun.com': iconSvg(
    '<rect x="5" y="6" width="22" height="20" rx="5" fill="#334155"/><path d="M10 12h12M10 17h12M10 22h7" stroke="#fff" stroke-width="2.1" stroke-linecap="round"/>'
  ),
  'realty.chosun.com': iconSvg(
    '<path d="M6 18 16 8l10 10v9H6z" fill="#f97316"/><path d="M11 27v-7h4v7M18 27v-9h4v9" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
  ),
  'www.yna.co.kr': iconSvg(
    '<circle cx="16" cy="16" r="11" fill="#2563eb"/><path d="M10 17c4-8 8-8 12 0M10 17c4 7 8 7 12 0" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round"/>'
  ),
  'news.kbs.co.kr': iconSvg(
    '<rect x="5" y="6" width="22" height="20" rx="5" fill="#1d4ed8"/><path d="M10 12h12M10 17h12M10 22h8" stroke="#fff" stroke-width="2.1" stroke-linecap="round"/>'
  ),
  'news.einfomax.co.kr': iconSvg(
    '<rect x="5" y="6" width="22" height="20" rx="5" fill="#0f172a"/><path d="M10 21h12M11 18l4-4 3 3 4-6" fill="none" stroke="#38bdf8" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>'
  ),
  'imnews.imbc.com': iconSvg(
    '<rect x="5" y="6" width="22" height="20" rx="5" fill="#dc2626"/><circle cx="16" cy="16" r="6" fill="#fff"/><circle cx="16" cy="16" r="3" fill="#2563eb"/>'
  ),
  'www.arunews.com': iconSvg(
    '<path d="M6 18 16 8l10 10v9H6z" fill="#16a34a"/><path d="M11 22h10M12 17h8" stroke="#fff" stroke-width="2.1" stroke-linecap="round"/>'
  ),
  'www.joongang.co.kr': iconSvg(
    '<rect x="5" y="6" width="22" height="20" rx="5" fill="#1e3a8a"/><path d="M11 12h10M11 17h10M11 22h7" stroke="#fff" stroke-width="2.1" stroke-linecap="round"/>'
  ),
  'www.seoul.co.kr': iconSvg(
    '<rect x="5" y="6" width="22" height="20" rx="5" fill="#ef4444"/><path d="M10 13h12M10 18h9M10 23h12" stroke="#fff" stroke-width="2.1" stroke-linecap="round"/><path d="M23 8v18" stroke="#2563eb" stroke-width="2.2" stroke-linecap="round"/>'
  ),
  'www.donga.com': iconSvg(
    '<rect x="5" y="6" width="22" height="20" rx="5" fill="#2563eb"/><path d="M10 12h12M10 17h8M10 22h12" stroke="#fff" stroke-width="2.1" stroke-linecap="round"/>'
  ),
  'www.hani.co.kr': iconSvg(
    '<rect x="5" y="6" width="22" height="20" rx="5" fill="#f97316"/><path d="M11 12h10M11 17h10M11 22h6" stroke="#fff" stroke-width="2.1" stroke-linecap="round"/>'
  ),
  'www.khan.co.kr': iconSvg(
    '<rect x="5" y="6" width="22" height="20" rx="5" fill="#15803d"/><path d="M11 12h10M11 17h8M11 22h11" stroke="#fff" stroke-width="2.1" stroke-linecap="round"/>'
  ),
  'www.ytn.co.kr': iconSvg(
    '<rect x="5" y="6" width="22" height="20" rx="5" fill="#0ea5e9"/><path d="M13 12v8l7-4z" fill="#fff"/><path d="M10 23h12" stroke="#dbeafe" stroke-width="2.1" stroke-linecap="round"/>'
  ),
  'www.mt.co.kr': iconSvg(
    '<rect x="5" y="6" width="22" height="20" rx="5" fill="#be123c"/><path d="M10 22V11l6 6 6-6v11" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>'
  ),
  'www.fetv.co.kr': iconSvg(
    '<rect x="5" y="6" width="22" height="20" rx="5" fill="#7c3aed"/><path d="M10 12h12M10 17h7M10 22h12" stroke="#fff" stroke-width="2.1" stroke-linecap="round"/><circle cx="22" cy="17" r="2" fill="#c4b5fd"/>'
  ),
  'www.chosun.com': iconSvg(
    '<rect x="5" y="6" width="22" height="20" rx="5" fill="#334155"/><path d="M10 12h12M10 17h12M10 22h8" stroke="#fff" stroke-width="2.1" stroke-linecap="round"/>'
  ),
  'www.sjsori.com': iconSvg(
    '<rect x="5" y="6" width="22" height="20" rx="5" fill="#0f766e"/><path d="M16 10c3 0 5 2 5 4.8 0 3.7-5 7.2-5 7.2s-5-3.5-5-7.2C11 12 13 10 16 10z" fill="#fff"/><circle cx="16" cy="15" r="1.8" fill="#0f766e"/>'
  ),
  'www.dnews.co.kr': iconSvg(
    '<rect x="5" y="6" width="22" height="20" rx="5" fill="#92400e"/><path d="M10 22h12M12 19v-5l4-3 4 3v5" fill="none" stroke="#fff" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"/>'
  ),
  'www.kbfg.com': iconSvg(
    '<rect x="5" y="6" width="22" height="20" rx="5" fill="#facc15"/><path d="M10 21V11M15 21v-6l6 6M16 15l5-4" stroke="#44330b" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>'
  ),
  'www.kbstar.com': iconSvg(
    '<rect x="5" y="6" width="22" height="20" rx="5" fill="#facc15"/><path d="M10 21V11M15 21v-6l6 6M16 15l5-4" stroke="#44330b" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>'
  ),
  'www.hanaif.re.kr': iconSvg(
    '<rect x="5" y="6" width="22" height="20" rx="5" fill="#009178"/><path d="M10 21V11M22 11v10M10 16h12" stroke="#fff" stroke-width="2.2" stroke-linecap="round"/>'
  ),
  'hanaif.re.kr': iconSvg(
    '<rect x="5" y="6" width="22" height="20" rx="5" fill="#009178"/><path d="M10 21V11M22 11v10M10 16h12" stroke="#fff" stroke-width="2.2" stroke-linecap="round"/>'
  ),
  'www.wfri.re.kr': iconSvg(
    '<rect x="5" y="6" width="22" height="20" rx="5" fill="#0ea5e9"/><path d="M10 14c3-4 9-4 12 0M10 19c3 4 9 4 12 0" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round"/>'
  ),
  'wfri.re.kr': iconSvg(
    '<rect x="5" y="6" width="22" height="20" rx="5" fill="#0ea5e9"/><path d="M10 14c3-4 9-4 12 0M10 19c3 4 9 4 12 0" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round"/>'
  ),
  'researcher.hf.go.kr': iconSvg(
    '<rect x="5" y="6" width="22" height="20" rx="5" fill="#0f766e"/><path d="M10 12h12M10 17h10M10 22h7" stroke="#fff" stroke-width="2.1" stroke-linecap="round"/><path d="M22 21l3 3" stroke="#bbf7d0" stroke-width="2.1" stroke-linecap="round"/>'
  ),
  'www.kif.re.kr': iconSvg(
    '<circle cx="16" cy="16" r="11" fill="#334155"/><path d="M10 21V11M15 16l6-5M15 16l6 5" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>'
  ),
  'kif.re.kr': iconSvg(
    '<circle cx="16" cy="16" r="11" fill="#334155"/><path d="M10 21V11M15 16l6-5M15 16l6 5" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>'
  ),
  'www.shinhan.com': iconSvg(
    '<rect x="5" y="6" width="22" height="20" rx="5" fill="#2563eb"/><path d="M12 12h9l-5 4 5 4h-9" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>'
  ),
  'www.woorifg.com': iconSvg(
    '<rect x="5" y="6" width="22" height="20" rx="5" fill="#0ea5e9"/><path d="M10 14c3-4 9-4 12 0M10 19c3 4 9 4 12 0" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round"/>'
  ),
  'www.nhwm.com': iconSvg(
    '<rect x="5" y="6" width="22" height="20" rx="5" fill="#16a34a"/><path d="M10 21V11l12 10V11" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>'
  ),
  'www.miraeasset.com': iconSvg(
    '<rect x="5" y="6" width="22" height="20" rx="5" fill="#0f3b8f"/><path d="M10 21l6-10 6 10M13 17h6" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>'
  )
};

const defaultSourceIcon = iconSvg(
  '<circle cx="16" cy="16" r="10" fill="none" stroke="#64748b" stroke-width="3"/><path d="M12 16h8M16 12v8" stroke="#64748b" stroke-width="3" stroke-linecap="round"/>'
);

export type SourceIconFallback = 'news' | 'report' | 'video' | 'link';

const fallbackSourceIcons: Record<SourceIconFallback, string> = {
  news: iconSvg(
    '<rect x="5" y="6" width="22" height="20" rx="5" fill="#1d4ed8"/><path d="M10 12h12M10 17h11M10 22h8" stroke="#fff" stroke-width="2.1" stroke-linecap="round"/>'
  ),
  report: iconSvg(
    '<rect x="5" y="6" width="22" height="20" rx="5" fill="#0f766e"/><path d="M10 21h12M11 17l4-4 4 4 3-6" fill="none" stroke="#fff" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"/>'
  ),
  video: iconSvg(
    '<rect x="4" y="9" width="24" height="14" rx="4.5" fill="#ff0033"/><path d="M14 13v6l6-3z" fill="#fff"/>'
  ),
  link: iconSvg(
    '<rect x="5" y="6" width="22" height="20" rx="5" fill="#7c3aed"/><path d="M12 16h8M10 20h7M15 12h7" stroke="#fff" stroke-width="2.1" stroke-linecap="round"/>'
  )
};

const faviconIconUrl = (domain: string) =>
  `https://www.google.com/s2/favicons?domain=${encodeURIComponent(domain)}&sz=64`;

const normalizeDomain = (domain: string) => {
  const normalized = domain.trim().toLowerCase();
  if (!normalized) return '';

  try {
    const parsed = new URL(normalized.includes('://') ? normalized : `https://${normalized}`);
    return parsed.hostname.replace(/\.$/, '');
  } catch {
    return normalized.split('/')[0].replace(/:\d+$/, '').replace(/\.$/, '');
  }
};

const domainCandidates = (domain: string) => {
  const normalized = normalizeDomain(domain);
  if (!normalized) return [];
  const withoutPrefix = normalized.replace(/^(www\.|m\.)/, '');
  return [
    normalized,
    withoutPrefix,
    `www.${withoutPrefix}`,
    `m.${withoutPrefix}`
  ];
};

export const sourceIconUrl = (domain: string, fallback?: SourceIconFallback) => {
  const siteDomain = normalizeDomain(domain);
  if (fallback && siteDomain) return faviconIconUrl(siteDomain);

  for (const candidate of domainCandidates(domain)) {
    const icon = sourceIcons[candidate];
    if (icon) return icon;
  }
  return fallback ? fallbackSourceIcons[fallback] : defaultSourceIcon;
};
