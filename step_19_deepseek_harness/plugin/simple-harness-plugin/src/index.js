// @ts-check
/**
 * simple-harness-policy: the step 11 permission layer as a dsh plugin.
 *
 * In dsh nothing is privileged. The tool registry publishes a waterfall event
 * `tools/pre-execute` before every tool runs; any plugin can listen and return
 * a decision. This one applies the allow / ask / deny table to the shell tool
 * and delegates everything else with `next()`.
 *
 * It needs no imports: `ctx` is the Cordis context the loader hands every
 * plugin, and the event vocabulary is part of the harness contract.
 *
 *   { kind: 'deny', reason }   the call never runs; the reason is the result
 *   { kind: 'ask' }            the interaction plugin prompts the user
 *   next()                     let the next listener (or the default) decide
 */

import { decide } from './rules.js'

export const name = 'simple-harness-policy'

const SHELL_TOOLS = new Set(['bash', 'pwsh', 'shell', 'run_command'])

/** Pull the command string out of whatever shape the shell tool uses. */
function commandOf(exec) {
  const args = exec.arguments ?? {}
  return String(args.command ?? args.cmd ?? args.script ?? '')
}

/** @param {any} ctx */
export function apply(ctx) {
  ctx.on('tools/pre-execute', async (exec, next) => {
    if (!SHELL_TOOLS.has(exec.name)) return next()
    const command = commandOf(exec)
    const verdict = decide(command)
    if (verdict === 'deny') return { kind: 'deny', reason: `Blocked by policy: ${command}` }
    if (verdict === 'ask') return { kind: 'ask', reason: `run: ${command}` }
    return next()
  })

  // Step 3, the audit line: durable session events are the transcript.
  ctx.on('session/event', (_session, event) => {
    if (event?.type === 'tool/call') {
      console.error(`[simple-harness-policy] tool/call ${event.data?.name ?? ''}`)
    }
  })
}
