import { describe, expect, it } from 'vitest';

import { sourceIconUrl } from '../lib/source-icons';

const decodeIcon = (url: string) => decodeURIComponent(url.replace('data:image/svg+xml,', ''));

describe('source icons', () => {
  it('renders pictogram source icons instead of alphabet labels', () => {
    const youtubeIcon = decodeIcon(sourceIconUrl('www.youtube.com'));
    const publicDataIcon = decodeIcon(sourceIconUrl('www.data.go.kr'));

    expect(youtubeIcon).toContain('path d="M14 13v6l6-3z"');
    expect(publicDataIcon).toContain('<ellipse');
    expect(youtubeIcon).not.toContain('<text');
    expect(publicDataIcon).not.toContain('<text');
  });

  it('falls back to a neutral link icon for unknown domains', () => {
    const fallbackIcon = decodeIcon(sourceIconUrl('unknown.example.com'));

    expect(fallbackIcon).toContain('stroke="#64748b"');
    expect(fallbackIcon).not.toContain('<text');
  });

  it('covers newsroom batch and official schedule source domains', () => {
    const googleNewsIcon = decodeIcon(sourceIconUrl('news.google.com'));
    const bokIcon = decodeIcon(sourceIconUrl('www.bok.or.kr'));
    const hugIcon = decodeIcon(sourceIconUrl('www.khug.or.kr'));
    const tistoryIcon = decodeIcon(sourceIconUrl('news8253.tistory.com'));
    const auctionTistoryIcon = decodeIcon(sourceIconUrl('auctionguide.tistory.com'));
    const kbThinkIcon = decodeIcon(sourceIconUrl('kbthink.com'));
    const krihsIcon = decodeIcon(sourceIconUrl('kremap.krihs.re.kr'));
    const wfriIcon = decodeIcon(sourceIconUrl('www.wfri.re.kr'));
    const hfIcon = decodeIcon(sourceIconUrl('researcher.hf.go.kr'));
    const kifIcon = decodeIcon(sourceIconUrl('www.kif.re.kr'));

    expect(googleNewsIcon).toContain('#4285f4');
    expect(bokIcon).toContain('#1d4ed8');
    expect(hugIcon).toContain('#0f766e');
    expect(tistoryIcon).toContain('#f97316');
    expect(auctionTistoryIcon).toContain('#f97316');
    expect(kbThinkIcon).toContain('#facc15');
    expect(krihsIcon).toContain('#2563eb');
    expect(wfriIcon).toContain('#0ea5e9');
    expect(hfIcon).toContain('#0f766e');
    expect(kifIcon).toContain('#334155');
    expect(googleNewsIcon).not.toContain('stroke="#64748b"');
    expect(bokIcon).not.toContain('stroke="#64748b"');
    expect(hugIcon).not.toContain('stroke="#64748b"');
    expect(tistoryIcon).not.toContain('stroke="#64748b"');
    expect(auctionTistoryIcon).not.toContain('stroke="#64748b"');
    expect(kbThinkIcon).not.toContain('stroke="#64748b"');
    expect(krihsIcon).not.toContain('stroke="#64748b"');
    expect(wfriIcon).not.toContain('stroke="#64748b"');
    expect(hfIcon).not.toContain('stroke="#64748b"');
    expect(kifIcon).not.toContain('stroke="#64748b"');
  });

  it('covers live real-time news publisher domains from the newsroom feed', () => {
    const domains = [
      'news.einfomax.co.kr',
      'imnews.imbc.com',
      'www.arunews.com',
      'www.joongang.co.kr',
      'www.seoul.co.kr',
      'www.donga.com',
      'www.hani.co.kr',
      'www.khan.co.kr',
      'www.ytn.co.kr',
      'www.mt.co.kr',
      'www.fetv.co.kr',
      'www.chosun.com',
      'www.sjsori.com',
      'www.dnews.co.kr'
    ];

    for (const domain of domains) {
      const icon = decodeIcon(sourceIconUrl(domain));

      expect(icon).not.toContain('stroke="#64748b"');
      expect(icon).not.toContain('<text');
    }
  });
});
