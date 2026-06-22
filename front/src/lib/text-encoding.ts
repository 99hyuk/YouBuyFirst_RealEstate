const mojibakePattern = /[\u0080-\u00ff]{2,}/;
const hangulPattern = /[가-힣]/g;
const replacementPattern = /\uFFFD/g;

export function repairMojibake(value?: string | null): string {
  if (value === null || value === undefined || value === '') return '';
  if (!mojibakePattern.test(value)) return value;

  const bytes: number[] = [];
  for (const char of value) {
    const code = char.codePointAt(0) ?? 0;
    if (code > 255) return value;
    bytes.push(code);
  }

  try {
    const decoded = new TextDecoder('utf-8', { fatal: false }).decode(new Uint8Array(bytes));
    const decodedHangul = decoded.match(hangulPattern)?.length ?? 0;
    const originalHangul = value.match(hangulPattern)?.length ?? 0;
    const decodedReplacements = decoded.match(replacementPattern)?.length ?? 0;

    return decodedHangul > originalHangul && decodedReplacements <= 1 ? decoded : value;
  } catch {
    return value;
  }
}
