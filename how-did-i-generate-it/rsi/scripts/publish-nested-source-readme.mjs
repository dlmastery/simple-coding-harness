// Preserve the frozen README and give its published copy working navigation.
import {readFileSync, writeFileSync, existsSync} from 'node:fs';
import {resolve, dirname, relative} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';

const repo = resolve(dirname(fileURLToPath(import.meta.url)), '../../..');
const archive = resolve(repo, 'rsi/evidence/2026-09-22/nested-research-evaluation');
const published = resolve(archive, 'source/README.md');
const original = published + '.original';
const manifest = resolve(archive, 'ARCHIVE-MANIFEST.csv');
const previousManifest = resolve(archive, 'ARCHIVE-MANIFEST.before-navigation.csv');
if (existsSync(original) || existsSync(previousManifest)) throw new Error('Publication already prepared; do not overwrite originals');
const raw = readFileSync(published);
const digest = createHash('sha256').update(raw).digest('hex');
const manifestRaw = readFileSync(manifest);
const rows = manifestRaw.toString('utf8').trimEnd().split(/\r?\n/);
if (rows.shift() !== 'path,bytes,sha256') throw new Error('Unexpected archive manifest schema');
const expected = 'source/README.md,' + raw.length + ',' + digest;
if (rows.filter(row => row === expected).length !== 1) throw new Error('Original README identity differs');
const originalContext = resolve(repo, 'rsi/experiments/real-tabular/nested');
let corrected = 0;
const content = raw.toString('utf8').replace(/\[([^\]]*)\]\(([^)\n]+)\)/g, (whole, label, target) => {
  if (!target.startsWith('../')) return whole;
  const destination = resolve(originalContext, target);
  if (!existsSync(destination) || relative(repo, destination).startsWith('..')) throw new Error('Missing or outside target: ' + target);
  corrected++;
  return '[' + label + '](' + relative(dirname(published), destination).replaceAll('\\', '/') + ')';
});
if (corrected !== 6) throw new Error('Unexpected link count: ' + corrected);
const banner = '> Historical source documentation, frozen before evaluation. Its status and run prompt describe that earlier point. The study is now closed; read the [completed report](../README.md). This reading copy corrects six relocated links. [The original bytes](README.md.original) retain the identity recorded in [STUDY-FREEZE.csv](../STUDY-FREEZE.csv). Do not use this archived prompt to restart the study.\n\n';
writeFileSync(original, raw);
writeFileSync(previousManifest, manifestRaw);
writeFileSync(published, banner + content);
// original_path records the name in the completed workspace. The SHA and size
// still describe that exact original, now stored with the .original suffix.
const mapped = rows.map(row => {
  if (row.split(',').length !== 3) throw new Error('Unexpected CSV quoting');
  const originalPath = row.split(',')[0];
  const archivedRow = row === expected ? row.replace('source/README.md,', 'source/README.md.original,') : row;
  return archivedRow + ',' + originalPath;
});
writeFileSync(manifest, 'path,bytes,sha256,original_path\n' + mapped.join('\n') + '\n');
console.log('Preserved one frozen README and the prior manifest; corrected six published links.');
