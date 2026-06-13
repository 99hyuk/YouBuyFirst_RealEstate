import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const erdPath = resolve(root, 'docs/domains/realestate/ERD.md');
const htmlPath = resolve(root, 'docs/domains/realestate/ERD.visual.html');

const markdown = readFileSync(erdPath, 'utf8');
const html = readFileSync(htmlPath, 'utf8');
const match = markdown.match(/```mermaid\r?\n([\s\S]*?)```/);

if (!match) {
  throw new Error(`Mermaid ERD block not found in ${erdPath}`);
}

if (!html.includes('<pre class="mermaid">')) {
  throw new Error(`Existing Mermaid ERD viewer shape not found in ${htmlPath}`);
}

const mermaid = buildRelationFirstMermaid(match[1].trim());
const tableFields = parseEntityFields(mermaid);
const relationCount = (mermaid.match(/^\s{2}[A-Z0-9_]+\s+[|}o{][|}o{]--[|}o{][|}o{]\s+[A-Z0-9_]+\s*:/gm) ?? []).length;
const tableCount = Object.keys(tableFields).length;

const nextHtml = html
  .replace(/<span class="pill strong">\d+ tables<\/span>/, `<span class="pill strong">${tableCount} tables</span>`)
  .replace(/<span class="pill">\d+ relations<\/span>/, `<span class="pill">${relationCount} relations</span>`)
  .replace(/<pre class="mermaid">[\s\S]*?<\/pre>/, `<pre class="mermaid">${escapeHtml(mermaid)}</pre>`)
  .replace(
    /<script type="application\/json" id="table-fields">[\s\S]*?<\/script>/,
    `<script type="application/json" id="table-fields">${escapeHtml(JSON.stringify(tableFields))}</script>`
  );

writeFileSync(htmlPath, nextHtml, 'utf8');
console.log(`Updated Mermaid ERD viewer at ${htmlPath}`);

function buildRelationFirstMermaid(source) {
  const lines = source.split(/\r?\n/);
  const header = lines.shift() ?? 'erDiagram';
  const entities = [];
  const relations = [];
  const other = [];

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    if (/^\s{2}[A-Z0-9_]+\s+\{/.test(line)) {
      const block = [line];
      while (index + 1 < lines.length) {
        index += 1;
        block.push(lines[index]);
        if (/^\s{2}\}/.test(lines[index])) break;
      }
      entities.push(block.join('\n'));
      continue;
    }

    const relationMatch = line.match(/^\s{2}([A-Z0-9_]+)\s+[|}o{][|}o{]--[|}o{][|}o{]\s+([A-Z0-9_]+)\s*:/);
    if (relationMatch) {
      if (relationMatch[1] === relationMatch[2]) continue;
      relations.push(line);
      continue;
    }

    if (line.trim()) other.push(line);
  }

  return [
    header,
    ...relations,
    '',
    ...entities,
    ...other
  ].join('\n').trim();
}

function parseEntityFields(source) {
  const fieldsByTable = {};
  const entityPattern = /^\s{2}([A-Z0-9_]+)\s+\{\r?\n([\s\S]*?)^\s{2}\}/gm;
  for (const match of source.matchAll(entityPattern)) {
    const [, tableName, body] = match;
    fieldsByTable[tableName] = body
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => {
        const [type = '', name = '', key = ''] = line.split(/\s+/);
        return { type, name, key };
      });
  }
  return fieldsByTable;
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}
