const svgDataUrl = (svg: string) => `data:image/svg+xml,${encodeURIComponent(svg)}`;

const iconSvg = (body: string) =>
  svgDataUrl(
    `<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">${body}</svg>`
  );

const sourceIcons: Record<string, string> = {
  'www.youtube.com': iconSvg(
    '<rect x="4" y="9" width="24" height="14" rx="4.5" fill="#ff0033"/><path d="M14 13v6l6-3z" fill="#fff"/>'
  ),
  'blog.naver.com': iconSvg(
    '<rect x="6" y="6" width="20" height="20" rx="5" fill="#03c75a"/><path d="M10 12h12v2.5H10zm0 5h9v2.5h-9z" fill="#fff"/><path d="M19 21.5l4-4 1.8 1.8-4 4-2.5.7z" fill="#fff"/>'
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
  'www.applyhome.co.kr': iconSvg(
    '<path d="M6 17 16 7l10 10v10H6z" fill="#ea580c"/><path d="m12 18 3 3 6-8" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'
  )
};

const defaultSourceIcon = iconSvg(
  '<circle cx="16" cy="16" r="10" fill="none" stroke="#64748b" stroke-width="3"/><path d="M12 16h8M16 12v8" stroke="#64748b" stroke-width="3" stroke-linecap="round"/>'
);

export const sourceIconUrl = (domain: string) => sourceIcons[domain] ?? defaultSourceIcon;
