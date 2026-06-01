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
});
