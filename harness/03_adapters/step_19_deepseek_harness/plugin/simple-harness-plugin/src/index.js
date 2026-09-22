// @ts-check
/**
 * simple-harness-policy: the step 11 permission layer as a dsh plugin.
 *
 * In dsh nothing is privileged. The tool registry publishes a waterfall event
 * `tools/pre-execute` before every tool runs; any plugin can listen and return
 * a decision. This one applies the allow / ask / deny table to the shell tool
 * and delegates everything else with `next()`.
 *
 * `ctx` is the Cordis context the loader hands every plugin, and the event
 * vocabulary is part of the harness contract:
 *
 *   { kind: 'deny', reason }   the call never runs; the reason is the result
 *   { kind: 'ask', reason }    the runtime's approval service asks its answerers
 *   next()                     let the next listener (or the default) decide
 *
 * There is a catch with `ask`. The SDK profiles have no answerer: the JSON-RPC
 * server never sends a question to the Python client, so the approval service
 * fails closed and the model reads "requires approval, but no approval channel
 * is available". That is a deny with a confusing name. ASK_FALLBACK says what
 * an `ask` verdict becomes here instead: 'deny' keeps the stage 11 line (only
 * allow-listed commands run on their own); 'allow' lets them through with an
 * audit line on stderr, which is what the sdk-minimal profile's
 * danger-full-access sandbox mode already permits.
 */

import { decide } from './rules.js'

export const name = 'simple-harness-policy'

const SHELL_TOOLS = new Set(['bash', 'pwsh', 'shell', 'run_command'])

/** What an `ask` verdict becomes without a human to ask: 'deny' or 'allow'. */
export const ASK_FALLBACK = 'deny'

/** Pull the command string out of whatever shape the shell tool uses. */
function commandOf(exec) {
  const args = exec.arguments ?? {}
  return String(args.command ?? args.cmd ?? args.script ?? '')
}

/** The decision for one shell command; exported so the node test can drive it. */
export function gate(command, askFallback = ASK_FALLBACK) {
  const verdict = decide(command)
  if (verdict === 'deny') return { kind: 'deny', reason: `Blocked by policy: ${command}` }
  if (verdict === 'ask' && askFallback === 'deny') {
    return { kind: 'deny', reason: `needs approval, and this profile has nobody to ask: ${command}. Only allow-listed commands run.` }
  }
  return null // allow, or ask-as-allow: let the next listener decide
}

/** @param {any} ctx */
export function apply(ctx) {
  ctx.on('tools/pre-execute', async (exec, next) => {
    if (!SHELL_TOOLS.has(exec.name)) return next()
    const command = commandOf(exec)
    const decision = gate(command)
    if (decision) return decision
    if (decide(command) === 'ask') console.error(`[simple-harness-policy] ask, allowed without a human: ${command}`)
    return next()
  })

  // Step 3, the audit line: durable session events are the transcript.
  ctx.on('session/event', (_session, event) => {
    if (event?.type === 'tool/call') {
      console.error(`[simple-harness-policy] tool/call ${event.data?.name ?? ''}`)
    }
  })
}
