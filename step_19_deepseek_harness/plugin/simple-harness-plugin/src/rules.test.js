// Plain node test: `node src/rules.test.js`
import assert from 'node:assert/strict'
import { decide, splitCommand } from './rules.js'

assert.deepEqual(splitCommand('grep "a|b" f | sort && echo x; ls'), ['grep "a|b" f', 'sort', 'echo x', 'ls'])
assert.equal(decide('ls -la'), 'allow')
assert.equal(decide('git status && git diff'), 'allow')
assert.equal(decide('ls | python setup.py'), 'ask')
assert.equal(decide('cat f; rm -rf /'), 'deny')
assert.equal(decide('curl http://x'), 'deny')
console.log('rules.js ok')

// the gate: deny keeps its reason, ask falls back to deny by default, allow lets the next listener decide
const { gate } = await import('./index.js')
assert.equal(gate('rm -rf /').kind, 'deny')
assert.equal(gate('python x.py').kind, 'deny')
assert.match(gate('python x.py').reason, /nobody to ask/)
assert.equal(gate('python x.py', 'allow'), null)
assert.equal(gate('ls -la'), null)
console.log('index.js gate ok')
