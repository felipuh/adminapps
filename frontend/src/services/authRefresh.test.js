// Run from frontend: node --test src/services/authRefresh.test.js
// Real React/ReactDOM and Axios; only the DOM host and HTTP transport are synthetic.
import assert from 'node:assert/strict';
import { test, beforeEach, afterEach } from 'node:test';
import { registerHooks } from 'node:module';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { transformSync } from 'rolldown/utils';
import { act, createElement, StrictMode } from 'react';
import axios from 'axios';
import { authSession } from './authRefresh.js';

const sourceRoot = new URL('../', import.meta.url).href;
registerHooks({
  resolve(specifier, context, nextResolve) {
    if (specifier === '../services/api' && context.parentURL?.startsWith(sourceRoot)) {
      return nextResolve(`${specifier}.jsx`, context);
    }
    return nextResolve(specifier, context);
  },
  load(url, context, nextLoad) {
    if (url.startsWith(sourceRoot) && url.endsWith('.jsx')) {
      const result = transformSync(fileURLToPath(url), readFileSync(new URL(url), 'utf8'), {
        jsx: { runtime: 'automatic' },
        define: { 'import.meta.env.VITE_API_URL': 'undefined' },
      });
      assert.equal(result.errors.length, 0);
      return { format: 'module', source: result.code, shortCircuit: true };
    }
    return nextLoad(url, context);
  },
});

const values = new Map();
const removeFailures = new Map();
const removeCalls = [];
Object.defineProperty(globalThis, 'localStorage', { configurable: true, value: {
  getItem: (key) => values.get(key) ?? null,
  setItem: (key, value) => values.set(key, String(value)),
  removeItem: (key) => {
    removeCalls.push(key);
    const remaining = removeFailures.get(key) || 0;
    if (remaining === Infinity || remaining > 0) {
      if (remaining !== Infinity) removeFailures.set(key, remaining - 1);
      throw new Error(`Synthetic ${key} removal failure`);
    }
    values.delete(key);
  },
  clear: () => values.clear(),
} });
const noop = () => {};
const classes = new Set();
const doc = { nodeType: 9, addEventListener: noop, removeEventListener: noop, activeElement: null };
const element = (tagName) => ({
  nodeType: 1, tagName: tagName.toUpperCase(), nodeName: tagName.toUpperCase(),
  ownerDocument: doc, style: {}, setAttribute: noop, removeAttribute: noop,
  addEventListener: noop, removeEventListener: noop,
  classList: { add: (name) => classes.add(name), remove: (...names) => names.forEach((name) => classes.delete(name)) },
});
doc.createElement = element;
doc.documentElement = element('html');
globalThis.document = doc;
globalThis.window = {
  document: doc, location: { href: '/' }, addEventListener: noop, removeEventListener: noop,
  HTMLElement: class {}, HTMLIFrameElement: class {},
};
globalThis.IS_REACT_ACT_ENVIRONMENT = true;
const { createRoot } = await import('react-dom/client');
let handler;
const calls = [];
axios.defaults.adapter = (config) => {
  calls.push({ ...config });
  return handler(config);
};
const { default: api, authService } = await import('./api.jsx');
const { AuthProvider, useAuth } = await import('../contexts/AuthContext.jsx');
let root;
let context;
function Probe() {
  context = useAuth();
  return null;
}
async function mount(strict = false) {
  root = createRoot(element('div'));
  const provider = createElement(AuthProvider, null, createElement(Probe));
  await act(async () => root.render(strict ? createElement(StrictMode, null, provider) : provider));
}
const deferred = () => {
  let resolve;
  let reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
};
const ok = (config, data = {}) => ({ config, data, status: 200, statusText: 'OK', headers: {} });
const fail = (config, status = 401) => Promise.reject(new axios.AxiosError(
  'Synthetic HTTP failure', 'ERR_BAD_RESPONSE', config, null,
  { config, status, data: {}, headers: {} },
));
const pair = (id) => ({ access: `synthetic-access-${id}`, refresh: `synthetic-refresh-${id}` });
function seed(id = 'old') {
  return authSession.acceptLogin(authSession.beginLogin(), pair(id));
}
function credentialsAre(id) {
  const expected = pair(id);
  assert.ok(localStorage.getItem('access_token') === expected.access, 'expected access credential retained');
  assert.ok(localStorage.getItem('refresh_token') === expected.refresh, 'expected refresh credential retained');
}
function credentialsEmpty() {
  assert.equal(localStorage.getItem('access_token'), null);
  assert.equal(localStorage.getItem('refresh_token'), null);
}
const refreshCalls = () => calls.filter((config) => config.url === '/auth/refresh/');
const rejected = (promise) => promise.then(
  () => { throw new Error('Expected rejection'); },
  () => undefined,
);
const newUser = { id: 'new-user', theme: 'dark', language: 'en' };
async function loginNew() {
  let result;
  await act(async () => { result = await context.login('new@example.invalid', 'synthetic-password'); });
  assert.equal(result.success, true);
}
function newSessionIntact() {
  credentialsAre('new');
  assert.deepEqual(context.user, newUser);
  assert.equal(context.isAuthenticated, true);
  assert.equal(context.loading, false);
  assert.deepEqual(context.featureFlags, { newFlag: true });
  assert.equal(context.featureFlagsLoading, false);
  assert.equal(document.documentElement.lang, 'en');
  assert.ok(classes.has('theme-dark'));
}
beforeEach(() => {
  removeFailures.clear();
  removeCalls.length = 0;
  authSession.clear(authSession.snapshot());
  localStorage.clear();
  calls.length = 0;
  window.location.href = '/';
  classes.clear();
  handler = () => { throw new Error('Unexpected synthetic request'); };
});
afterEach(async () => {
  if (root) await act(async () => root.unmount());
  root = undefined;
  context = undefined;
});

test('AUTH-T01: two successive rotations persist both credentials', async () => {
  seed();
  let rotations = 0;
  handler = async (config) => {
    if (config.url === '/auth/refresh/') {
      const expected = pair(rotations ? 'rotated-1' : 'old');
      assert.ok(JSON.parse(config.data).refresh === expected.refresh, 'uses latest refresh credential');
      return ok(config, pair(`rotated-${++rotations}`));
    }
    return config._retry ? ok(config) : fail(config);
  };
  const generation = authSession.snapshot().generation;
  await api.get('/protected/');
  credentialsAre('rotated-1');
  await api.get('/protected/');
  credentialsAre('rotated-2');
  assert.equal(rotations, 2);
  assert.equal(authSession.snapshot().generation, generation);
});

test('AUTH-T02: five concurrent 401s share one refresh', async () => {
  seed();
  const allFailed = deferred();
  const release = deferred();
  let initial = 0;
  handler = async (config) => {
    if (config.url === '/auth/refresh/') { await release.promise; return ok(config, pair('rotated')); }
    if (!config._retry) {
      if (++initial === 5) allFailed.resolve();
      return fail(config);
    }
    assert.ok(config.headers.Authorization === `Bearer ${pair('rotated').access}`);
    return ok(config);
  };
  const requests = Promise.all(Array.from({ length: 5 }, () => api.get('/protected/')));
  await allFailed.promise;
  release.resolve();
  await requests;
  assert.equal(refreshCalls().length, 1);
  assert.equal(calls.filter((config) => config._retry).length, 5);
  credentialsAre('rotated');
});

test('AUTH-T03: a late 401 reuses credentials without another rotation', async () => {
  seed();
  const late = deferred();
  const entered = deferred();
  handler = async (config) => {
    if (config.url === '/auth/refresh/') return ok(config, pair('rotated'));
    if (config._retry) return ok(config);
    if (config.url === '/late/') { entered.resolve(); await late.promise; }
    return fail(config);
  };
  const pending = api.get('/late/');
  await entered.promise;
  await api.get('/fast/');
  late.resolve();
  await pending;
  assert.equal(refreshCalls().length, 1);
  credentialsAre('rotated');
});

test('AUTH-T04: malformed/rejected refresh clears only its session; retries are bounded', async (t) => {
  for (const mode of ['rejected', 'missing-access', 'missing-refresh', 'empty', 'wrong-type', 'reused-refresh', 'retry-401']) {
    await t.test(mode, async () => {
      seed();
      calls.length = 0;
      window.location.href = '/';
      handler = async (config) => {
        if (config.url !== '/auth/refresh/') return fail(config);
        if (mode === 'rejected') return fail(config);
        const data = { ...pair('rotated') };
        if (mode === 'missing-access') delete data.access;
        if (mode === 'missing-refresh') delete data.refresh;
        if (mode === 'empty') data.access = ' ';
        if (mode === 'wrong-type') data.refresh = {};
        if (mode === 'reused-refresh') data.refresh = pair('old').refresh;
        return ok(config, data);
      };
      await rejected(api.get('/protected/'));
      assert.equal(refreshCalls().length, 1);
      assert.equal(calls.filter((config) => config.url === '/protected/').length, mode === 'retry-401' ? 2 : 1);
      if (mode === 'retry-401') credentialsAre('rotated');
      else { credentialsEmpty(); assert.equal(window.location.href, '/login'); }
    });
  }
});

test('AUTH-T05: logout during refresh prevents token restoration', async () => {
  seed();
  const entered = deferred();
  const release = deferred();
  handler = async (config) => {
    if (config.url === '/auth/logout/') return ok(config);
    if (config.url === '/auth/refresh/') { entered.resolve(); await release.promise; return ok(config, pair('obsolete')); }
    return fail(config);
  };
  const pending = rejected(api.get('/protected/'));
  await entered.promise;
  const logout = authService.logout();
  credentialsEmpty();
  release.resolve();
  await Promise.all([logout, pending]);
  credentialsEmpty();
  assert.equal(window.location.href, '/');
  assert.equal(calls.filter((config) => config.url === '/protected/').length, 1);
});

test('AUTH-T06: mounted AuthContext ignores old checkAuth success and failure after login', async (t) => {
  for (const status of [200, 500, 401]) {
    await t.test(`old response ${status}`, async () => {
      seed();
      const entered = deferred();
      const release = deferred();
      handler = async (config) => {
        if (config.url === '/auth/users/me/') {
          entered.resolve(); await release.promise;
          return status === 200 ? ok(config, { id: 'obsolete-user' }) : fail(config, status);
        }
        if (config.url === '/auth/login/') return ok(config, { ...pair('new'), user: newUser });
        if (config.url === '/feature-flags/') return ok(config, { newFlag: true });
        throw new Error('Unexpected request');
      };
      await mount();
      await entered.promise;
      await loginNew();
      newSessionIntact();
      await act(async () => { release.resolve(); });
      newSessionIntact();
      assert.equal(refreshCalls().length, 0);
      await act(async () => root.unmount());
      root = undefined;
    });
  }
});

test('AUTH-T07: mounted AuthContext logout finally preserves a later login', async (t) => {
  for (const remoteFailure of [false, true]) {
    await t.test(remoteFailure ? 'remote failure' : 'remote success', async () => {
      seed();
      const entered = deferred();
      const release = deferred();
      handler = async (config) => {
        if (config.url === '/auth/users/me/') return ok(config, { id: 'old-user' });
        if (config.url === '/feature-flags/') return ok(config, { newFlag: true });
        if (config.url === '/auth/login/') return ok(config, { ...pair('new'), user: newUser });
        if (config.url === '/auth/logout/') {
          assert.ok(JSON.parse(config.data).refresh === pair('old').refresh);
          assert.ok(config.headers.Authorization === `Bearer ${pair('old').access}`);
          entered.resolve(); await release.promise;
          return remoteFailure ? fail(config, 500) : ok(config);
        }
        throw new Error('Unexpected request');
      };
      await mount();
      let pending;
      await act(async () => { pending = context.logout(); });
      await entered.promise;
      credentialsEmpty();
      assert.equal(context.user, null);
      assert.equal(context.isAuthenticated, false);
      await loginNew();
      await act(async () => { release.resolve(); await pending; });
      newSessionIntact();
      await act(async () => root.unmount());
      root = undefined;
    });
  }
});

test('AUTH-T08: old refresh failure cannot erase a later login or share its flight', async () => {
  seed();
  const entered = deferred();
  const release = deferred();
  handler = async (config) => {
    if (config.url === '/auth/login/') return ok(config, { ...pair('new'), user: newUser });
    if (config.url === '/auth/refresh/') {
      if (JSON.parse(config.data).refresh === pair('old').refresh) {
        entered.resolve(); await release.promise; return fail(config);
      }
      return ok(config, pair('new-rotated'));
    }
    return config._retry ? ok(config) : fail(config);
  };
  const pending = rejected(api.get('/old/'));
  await entered.promise;
  await authService.login('new@example.invalid', 'synthetic-password');
  await api.get('/new/');
  credentialsAre('new-rotated');
  release.resolve();
  await pending;
  credentialsAre('new-rotated');
  assert.equal(refreshCalls().length, 2);
  assert.equal(window.location.href, '/');
});

test('AUTH-T09: excluded endpoints and non-401 errors never refresh', async () => {
  seed();
  handler = (config) => fail(config);
  for (const url of ['/auth/login/', '/auth/refresh/', '/auth/logout/', '/auth/2fa/verify/', '/auth/password-reset/', '/auth/password-reset/confirm/']) {
    await rejected(api.post(url));
  }
  // One explicit refresh request above, no automatic requests.
  assert.equal(refreshCalls().length, 1);
  calls.length = 0;
  await rejected(authService.login('new@example.invalid', 'synthetic-password'));
  await rejected(authService.verify2fa({}, 'synthetic-temporary'));
  for (const status of [400, 403, 404, 429, 500]) {
    handler = (config) => fail(config, status);
    await rejected(api.get('/protected/'));
  }
  handler = (config) => Promise.reject(new axios.AxiosError('Synthetic network failure', 'ERR_NETWORK', config));
  await rejected(api.get('/protected/'));
  assert.equal(refreshCalls().length, 0);
});

test('AUTH-T10: actual api.jsx interceptors inject and retry through synthetic Axios adapter', async () => {
  seed();
  const seen = [];
  handler = async (config) => {
    seen.push({ url: config.url, auth: config.headers.Authorization });
    assert.equal(config.baseURL, '/api');
    if (config.url === '/auth/refresh/') return ok(config, pair('rotated'));
    return config._retry ? ok(config, { integrated: true }) : fail(config);
  };
  const response = await api.get('/integrated/');
  assert.deepEqual(response.data, { integrated: true });
  assert.deepEqual(seen.map(({ url }) => url), ['/integrated/', '/auth/refresh/', '/integrated/']);
  assert.ok(seen[0].auth === `Bearer ${pair('old').access}`);
  assert.equal(seen[1].auth, undefined);
  assert.ok(seen[2].auth === `Bearer ${pair('rotated').access}`);
});

test('AUTH-T04: partial persistence failure clears the owned pair', async () => {
  seed();
  const write = localStorage.setItem;
  localStorage.setItem = (key, value) => {
    if (key === 'access_token') throw new Error('Synthetic storage quota failure');
    write(key, value);
  };
  handler = (config) => config.url === '/auth/refresh/'
    ? Promise.resolve(ok(config, pair('rotated'))) : fail(config);
  try {
    await rejected(api.get('/protected/'));
    credentialsEmpty();
    assert.equal(window.location.href, '/login');
    assert.equal(refreshCalls().length, 1);
  } finally {
    localStorage.setItem = write;
  }
});

test('AUTH-T06: AuthContext itself guards unfiltered success/error continuations', async (t) => {
  // Deliberately bypass Axios rejection to exercise both guards in the actual
  // mounted component, in addition to the full transport integration above.
  for (const outcome of ['success', 'error', 'logout']) {
    await t.test(outcome, async () => {
      seed();
      const release = deferred();
      const original = authService.getCurrentUser;
      authService.getCurrentUser = () => release.promise;
      handler = async (config) => {
        if (config.url === '/auth/login/') return ok(config, { ...pair('new'), user: newUser });
        if (config.url === '/feature-flags/') return ok(config, { newFlag: true });
        if (config.url === '/auth/logout/') return ok(config);
        throw new Error('Unexpected request');
      };
      try {
        await mount();
        if (outcome === 'logout') await act(async () => context.logout());
        else await loginNew();
        await act(async () => {
          if (outcome === 'error') release.reject(new Error('Synthetic stale failure'));
          else release.resolve({ id: 'obsolete-user' });
        });
        if (outcome === 'logout') {
          credentialsEmpty();
          assert.equal(context.user, null);
          assert.equal(context.isAuthenticated, false);
          assert.equal(context.loading, false);
        } else newSessionIntact();
      } finally {
        authService.getCurrentUser = original;
        await act(async () => root.unmount());
        root = undefined;
      }
    });
  }
});

test('AUTH-T06: stale feature flags and checkAuth completion preserve newer loading state', async () => {
  seed();
  const oldFlags = deferred();
  const newFlags = deferred();
  let flagRequests = 0;
  handler = async (config) => {
    if (config.url === '/auth/users/me/') return ok(config, { id: 'old-user' });
    if (config.url === '/auth/login/') return ok(config, { ...pair('new'), user: newUser });
    if (config.url === '/feature-flags/') {
      await (++flagRequests === 1 ? oldFlags.promise : newFlags.promise);
      return ok(config, { newFlag: true });
    }
    throw new Error('Unexpected request');
  };
  await mount();
  let pending;
  await act(async () => { pending = context.login('new@example.invalid', 'synthetic-password'); });
  assert.equal(context.featureFlagsLoading, true);
  await act(async () => { oldFlags.resolve(); });
  assert.equal(context.featureFlagsLoading, true);
  assert.deepEqual(context.user, newUser);
  await act(async () => { newFlags.resolve(); await pending; });
  newSessionIntact();
});

test('AUTH-T08: obsolete successful refresh does not restore tokens or replace a new flight', async () => {
  seed();
  const oldEntered = deferred();
  const oldRelease = deferred();
  const newEntered = deferred();
  const newRelease = deferred();
  handler = async (config) => {
    if (config.url === '/auth/login/') return ok(config, { ...pair('new'), user: newUser });
    if (config.url === '/auth/refresh/') {
      const old = JSON.parse(config.data).refresh === pair('old').refresh;
      (old ? oldEntered : newEntered).resolve();
      await (old ? oldRelease : newRelease).promise;
      return ok(config, pair(old ? 'obsolete' : 'new-rotated'));
    }
    return config._retry ? ok(config) : fail(config);
  };
  const oldPending = rejected(api.get('/old/'));
  await oldEntered.promise;
  await authService.login('new@example.invalid', 'synthetic-password');
  const newPending = api.get('/new/');
  await newEntered.promise;
  oldRelease.resolve();
  await oldPending;
  credentialsAre('new');
  const another = api.get('/another/');
  newRelease.resolve();
  await Promise.all([newPending, another]);
  credentialsAre('new-rotated');
  assert.equal(refreshCalls().length, 2);
  assert.equal(window.location.href, '/');
});

test('AUTH-T08: generation distinguishes a new login with identical token values', async () => {
  seed();
  const entered = deferred();
  const release = deferred();
  handler = async (config) => {
    if (config.url === '/auth/login/') return ok(config, { ...pair('old'), user: newUser });
    if (config.url === '/auth/refresh/') { entered.resolve(); await release.promise; return fail(config); }
    return fail(config);
  };
  const oldGeneration = authSession.snapshot().generation;
  const pending = rejected(api.get('/protected/'));
  await entered.promise;
  await authService.login('new@example.invalid', 'synthetic-password');
  assert.notEqual(authSession.snapshot().generation, oldGeneration);
  release.resolve();
  await pending;
  credentialsAre('old');
  assert.equal(window.location.href, '/');
});

test('AUTH-T09: login response after logout cannot resurrect a session', async () => {
  const entered = deferred();
  const release = deferred();
  handler = async (config) => {
    if (config.url === '/auth/login/') {
      entered.resolve(); await release.promise;
      return ok(config, { ...pair('obsolete'), user: newUser });
    }
    throw new Error('Unexpected request');
  };
  const pending = rejected(authService.login('new@example.invalid', 'synthetic-password'));
  await entered.promise;
  await authService.logout();
  release.resolve();
  await pending;
  credentialsEmpty();
});

test('AUTH-T10: request identity is captured before a synchronous login boundary', async () => {
  seed();
  handler = (config) => {
    if (config.url === '/auth/login/') return Promise.resolve(ok(config, { ...pair('new'), user: newUser }));
    if (config.url === '/old/') {
      assert.ok(config.headers.Authorization === `Bearer ${pair('old').access}`);
      assert.deepEqual(Object.keys(config._authSession).sort(), ['generation', 'revision']);
      return fail(config);
    }
    throw new Error('Old request must not refresh or cross into the new session');
  };
  const pending = rejected(api.get('/old/'));
  await authService.login('new@example.invalid', 'synthetic-password');
  await pending;
  credentialsAre('new');
  assert.equal(refreshCalls().length, 0);
  assert.equal(calls.filter((config) => config.url === '/old/').length, 1);
});

test('AUTH-T11: StrictMode stale failure cannot clear the current session', async () => {
  seed();
  const first = deferred();
  const second = deferred();
  const secondStarted = deferred();
  let userRequests = 0;
  handler = async (config) => {
    if (config.url === '/auth/users/me/') {
      const requestNumber = ++userRequests;
      if (requestNumber === 2) secondStarted.resolve();
      await (requestNumber === 1 ? first.promise : second.promise);
      return requestNumber === 1
        ? fail(config, 500)
        : ok(config, { id: 'strict-user', theme: 'dark', language: 'en' });
    }
    if (config.url === '/feature-flags/') return ok(config, { strictFlag: true });
    throw new Error('Unexpected request');
  };
  await mount(true);
  await secondStarted.promise;
  await act(async () => second.resolve());
  assert.equal(context.user.id, 'strict-user');
  assert.equal(context.isAuthenticated, true);
  assert.deepEqual(context.featureFlags, { strictFlag: true });
  await act(async () => first.resolve());
  credentialsAre('old');
  assert.equal(context.user.id, 'strict-user');
  assert.equal(context.isAuthenticated, true);
  assert.equal(authSession.snapshot().access, pair('old').access);
});

test('AUTH-T12: unmounted provider failure cannot affect its remounted successor', async () => {
  seed();
  const oldRequest = deferred();
  const newRequest = deferred();
  const newStarted = deferred();
  let userRequests = 0;
  handler = async (config) => {
    if (config.url === '/auth/users/me/') {
      const requestNumber = ++userRequests;
      if (requestNumber === 2) newStarted.resolve();
      await (requestNumber === 1 ? oldRequest.promise : newRequest.promise);
      return requestNumber === 1
        ? fail(config, 500)
        : ok(config, { id: 'remounted-user', theme: 'dark', language: 'en' });
    }
    if (config.url === '/feature-flags/') return ok(config, { remountedFlag: true });
    throw new Error('Unexpected request');
  };
  await mount();
  await act(async () => root.unmount());
  root = undefined;
  context = undefined;
  await mount();
  await newStarted.promise;
  await act(async () => newRequest.resolve());
  assert.equal(context.user.id, 'remounted-user');
  assert.equal(context.isAuthenticated, true);
  await act(async () => oldRequest.resolve());
  credentialsAre('old');
  assert.equal(context.user.id, 'remounted-user');
  assert.equal(context.isAuthenticated, true);
  assert.deepEqual(context.featureFlags, { remountedFlag: true });
});

test('AUTH-T13: partial storage failures are retried and residual credentials stay unusable', async (t) => {
  await t.test('a transient failure retries cleanup of both credentials', async () => {
    seed();
    removeFailures.set('access_token', 1);
    const callsBefore = removeCalls.length;
    authSession.clear(authSession.snapshot());
    assert.deepEqual(removeCalls.slice(callsBefore), ['access_token', 'access_token', 'refresh_token']);
    credentialsEmpty();
    handler = (config) => fail(config);
    await rejected(api.get('/after-clear/'));
    assert.equal(refreshCalls().length, 0);
    assert.equal(calls.find((config) => config.url === '/after-clear/').headers.Authorization, undefined);
  });

  await t.test('a residual refresh value is blocked after bounded cleanup failure', async () => {
    seed();
    removeFailures.set('refresh_token', Infinity);
    const refreshRemovalStart = removeCalls.filter((key) => key === 'refresh_token').length;
    authSession.clear(authSession.snapshot());
    assert.equal(values.get('refresh_token'), pair('old').refresh);
    assert.equal(authSession.snapshot().refresh, null);
    assert.equal(removeCalls.filter((key) => key === 'refresh_token').length, refreshRemovalStart + 2);
    handler = (config) => fail(config);
    await rejected(api.get('/residual-refresh/'));
    assert.equal(refreshCalls().length, 0);
    assert.equal(calls.find((config) => config.url === '/residual-refresh/').headers.Authorization, undefined);
    assert.equal(removeCalls.filter((key) => key === 'refresh_token').length, refreshRemovalStart + 4);
  });
});

test('AUTH-T14: logout attempts remote revocation with the captured refresh after local failure', async (t) => {
  for (const remoteFailure of [false, true]) {
    await t.test(remoteFailure ? 'remote request fails' : 'remote request succeeds synthetically', async () => {
      seed();
      removeFailures.set('access_token', Infinity);
      removeFailures.set('refresh_token', Infinity);
      const remoteEntered = deferred();
      const remoteRelease = deferred();
      handler = async (config) => {
        if (config.url === '/auth/login/') return ok(config, { ...pair('new'), user: newUser });
        if (config.url === '/auth/logout/') {
          assert.equal(JSON.parse(config.data).refresh, pair('old').refresh);
          assert.ok(config.headers.Authorization.endsWith(pair('old').access));
          remoteEntered.resolve();
          await remoteRelease.promise;
          return remoteFailure ? fail(config, 500) : ok(config);
        }
        throw new Error('Unexpected request');
      };
      const pendingLogout = authService.logout();
      await remoteEntered.promise;
      await authService.login('new@example.invalid', 'synthetic-password');
      remoteRelease.resolve();
      let logoutError;
      try {
        await pendingLogout;
      } catch (error) {
        logoutError = error;
      }
      assert.ok(logoutError instanceof AggregateError);
      credentialsAre('new');
      assert.equal(calls.filter((config) => config.url === '/auth/logout/').length, 1);
    });
  }
});

test('AUTH-T15: persistent storage failures fail closed only within this runtime', async () => {
  seed();
  removeFailures.set('access_token', Infinity);
  removeFailures.set('refresh_token', Infinity);
  const accessRemovalStart = removeCalls.filter((key) => key === 'access_token').length;
  const refreshRemovalStart = removeCalls.filter((key) => key === 'refresh_token').length;
  authSession.clear(authSession.snapshot());
  assert.equal(values.get('access_token'), pair('old').access);
  assert.equal(values.get('refresh_token'), pair('old').refresh);
  assert.equal(authSession.snapshot().access, null);
  assert.equal(authSession.snapshot().refresh, null);
  handler = (config) => fail(config);
  await rejected(api.get('/persistent-failure/'));
  const request = calls.find((config) => config.url === '/persistent-failure/');
  assert.equal(request.headers.Authorization, undefined);
  assert.equal(refreshCalls().length, 0);
  assert.equal(removeCalls.filter((key) => key === 'access_token').length, accessRemovalStart + 4);
  assert.equal(removeCalls.filter((key) => key === 'refresh_token').length, refreshRemovalStart + 4);
});
