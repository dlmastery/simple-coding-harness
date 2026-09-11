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
