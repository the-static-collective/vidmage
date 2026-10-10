import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

export function validateDonorLock(lock) {
  assert.equal(lock?.schema, 'vidmage/donor-lock/v0', 'schema');
  assert.ok(Array.isArray(lock.donors) && lock.donors.length > 0, 'donors required');
  const seen = new Set();
  for (const donor of lock.donors) {
    assert.match(donor.id, /^[a-z][a-z0-9-]+$/);
    assert.ok(!seen.has(donor.id), 'duplicate donor id');
    seen.add(donor.id);
    assert.match(donor.repository, /^[\w.-]+\/[\w.-]+$/);
    assert.match(donor.ref, /^[\w./-]+$/);
    assert.match(donor.sha, /^[a-f0-9]{40}$/);
    const uri = new URL(donor.evidenceRun);
    assert.equal(uri.origin, 'https://github.com');
    assert.ok(uri.pathname.startsWith('/' + donor.repository + '/actions/runs/'), 'run repo mismatch');
    assert.ok(donor.purpose?.length > 15, 'purpose required');
  }
  return lock.donors.length;
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  const lock = JSON.parse(readFileSync(new URL('../donors.lock.json', import.meta.url), 'utf8'));
  console.log('Verified donor lock:', validateDonorLock(lock), 'source pins');
}
