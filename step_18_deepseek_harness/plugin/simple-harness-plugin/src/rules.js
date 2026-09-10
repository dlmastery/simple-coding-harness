// @ts-check
/**
 * The step 12 allow / ask / deny table, ported to JavaScript so it can run
 * inside the dsh process. Same patterns, same "last match wins", same
 * "strictest part of a compound command wins".
 */

/** @type {Array<[string, 'allow' | 'ask' | 'deny']>} */
export const BASH_RULES = [
  ['*', 'ask'],
  // read-only
  ['ls*', 'allow'], ['pwd', 'allow'], ['cat *', 'allow'], ['head *', 'allow'], ['tail *', 'allow'],
  ['wc *', 'allow'], ['grep *', 'allow'], ['rg *', 'allow'], ['find *', 'allow'], ['tree*', 'allow'],
  ['which *', 'allow'], ['echo *', 'allow'], ['sort*', 'allow'], ['uniq*', 'allow'], ['cut *', 'allow'],
  ['git status*', 'allow'], ['git diff*', 'allow'], ['git log*', 'allow'], ['git show*', 'allow'],
  ['git branch*', 'allow'], ['git ls-files*', 'allow'],
  ['pytest*', 'allow'], ['python -m pytest*', 'allow'],
  // never
  ['rm *', 'deny'], ['sudo *', 'deny'], ['chmod *', 'deny'], ['chown *', 'deny'],
  ['curl *', 'deny'], ['wget *', 'deny'],
  ['git push*', 'deny'], ['git reset*', 'deny'], ['git clean*', 'deny'], ['git checkout -- *', 'deny'],
]

/** fnmatch-style glob: `*` matches anything, everything else is literal. */
export function globMatch(text, pattern) {
  const escaped = pattern.split('*').map(s => s.replace(/[.+?^${}()|[\]\\]/g, '\\$&')).join('.*')
  return new RegExp(`^${escaped}$`).test(text)
}

/** Split on | || ; & && - but not inside quotes. */
export function splitCommand(command) {
  const parts = []
  let current = ''
  let quote = null
  for (let i = 0; i < command.length; i++) {
    const ch = command[i]
    if (quote) {
      current += ch
      if (ch === quote) quote = null
    } else if (ch === '\\' && i + 1 < command.length) {
      current += ch + command[++i]
    } else if (ch === '"' || ch === "'") {
      quote = ch
      current += ch
    } else if (ch === '&' || ch === '|' || ch === ';') {
      parts.push(current)
      current = ''
      while (i + 1 < command.length && (command[i + 1] === '&' || command[i + 1] === '|')) i++
    } else {
      current += ch
    }
  }
  parts.push(current)
  return parts.map(p => p.trim()).filter(Boolean)
}

/** @returns {'allow' | 'ask' | 'deny'} */
export function decide(command) {
  const verdicts = splitCommand(command).map(part => {
    let action = 'ask'
    for (const [pattern, rule] of BASH_RULES) if (globMatch(part, pattern)) action = rule
    return action
  })
  if (verdicts.includes('deny')) return 'deny'
  if (verdicts.includes('ask')) return 'ask'
  return 'allow'
}
