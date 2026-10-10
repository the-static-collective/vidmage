import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { validateDonorLock } from '../scripts/check-donors.mjs';

const lock = JSON.parse(readFileSync(new URL('../donors.lock.json', import.meta.url), 'utf8'));

test('VIDMAGE donor lock has exact immutable SHAs and run references', () => {
  assert.equal(validateDonorLock(lock), 5);
  assert.ok(lock.donors.some(d => d.id === 'blender-composite'));
  assert.ok(lock.donors.some(d => d.id === 'blender-zero-dollar'));
  assert.ok(lock.donors.some(d => d.id === 'blender-cockpit'));
  assert.ok(lock.donors.some(d => d.id === 'toaster-lbranch'));
});

test('rejects branch-only evidence without an exact commit SHA', () => {
  const altered = structuredClone(lock);
  altered.donors[0].sha = 'main';
  assert.throws(() => validateDonorLock(altered));
});

test('rejects proof links pointing to another repo', () => {
  const altered = structuredClone(lock);
  altered.donors[0].evidenceRun = 'https://github.com/other/repo/actions/runs/123';
  assert.throws(() => validateDonorLock(altered));
});

test('rejects duplicates even when branches differ', () => {
  const altered = structuredClone(lock);
  altered.donors.push({ ...altered.donors[0], ref: 'different/branch' });
  assert.throws(() => validateDonorLock(altered));
});
