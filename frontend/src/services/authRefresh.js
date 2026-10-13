// A generation identifies a login/logout boundary; revision identifies rotation
// within that generation. Token equality alone cannot identify a session.
export function createAuthSession({ storage = () => localStorage } = {}) {
  let generation = 0;
  let revision = 0;
  let observed;
  let flight;
  const invalidAccess = new Set();
  const invalidRefresh = new Set();
  const logins = new WeakMap();
  const read = () => ({
    access: storage().getItem('access_token'),
    refresh: storage().getItem('refresh_token'),
  });
  const snapshot = () => {
    const tokens = read();
    // Accommodate legacy consumers that write directly to localStorage.
    if (observed && (tokens.access !== observed.access || tokens.refresh !== observed.refresh)) {
      generation += 1;
      revision = 0;
    }
    observed = tokens;
    return {
      generation,
      revision,
      access: invalidAccess.has(tokens.access) ? null : tokens.access,
      refresh: invalidRefresh.has(tokens.refresh) ? null : tokens.refresh,
    };
  };
  const isCurrent = (session) => snapshot().generation === session.generation;
  const assertCurrent = (session) => {
    if (!isCurrent(session)) throw new Error('La sesión ha cambiado');
  };
  const clear = (session, { throwOnStorageError = false } = {}) => {
    if (!isCurrent(session)) return false;
    let tokens;
    const errors = [];
    try {
      tokens = read();
    } catch (error) {
      errors.push(error);
    }
    for (const token of [session.access, tokens?.access]) {
      if (token) invalidAccess.add(token);
    }
    for (const token of [session.refresh, tokens?.refresh]) {
      if (token) invalidRefresh.add(token);
    }
    generation += 1;
    revision = 0;
    for (const key of ['access_token', 'refresh_token']) {
      let lastError;
      for (let attempt = 0; attempt < 2; attempt += 1) {
        try {
          storage().removeItem(key);
          lastError = undefined;
          break;
        } catch (error) {
          lastError = error;
        }
      }
      if (lastError) errors.push(lastError);
    }
    try {
      observed = read();
    } catch (error) {
      errors.push(error);
    }
    if (throwOnStorageError && errors.length) {
      throw new AggregateError(errors, 'No se pudieron eliminar todas las credenciales locales');
    }
    return true;
  };
  const beginLogin = () => {
    clear(snapshot());
    return snapshot();
  };
  const validToken = (token) => typeof token === 'string' && token.trim().length > 0;
  const save = (session, data) => {
    assertCurrent(session);
    // The configured rotating SimpleJWT endpoint must supply BOTH tokens.
    if (!validToken(data?.access) || !validToken(data?.refresh)) {
      throw new Error('Respuesta de autenticación inválida');
    }
    try {
      storage().setItem('refresh_token', data.refresh);
      storage().setItem('access_token', data.access);
    } finally {
      // A partial storage write is ours, not a new external session.
      observed = read();
    }
    invalidAccess.delete(data.access);
    invalidRefresh.delete(data.refresh);
    revision += 1;
    return snapshot();
  };
  const acceptLogin = (session, data) => {
    assertCurrent(session);
    try {
      if (!data?.requires_2fa) save(session, data);
    } catch (error) {
      clear(session);
      throw error;
    }
    logins.set(data, snapshot());
    return data;
  };
  const isLoginCurrent = (data) => {
    const session = logins.get(data);
    return Boolean(session && !data.requires_2fa && isCurrent(session));
  };
  const renew = (session, requestRefresh, onExpired) => {
    assertCurrent(session);
    const current = snapshot();
    if (flight?.generation === current.generation) return flight.promise;
    if (current.revision !== session.revision) return Promise.resolve(current);

    const pending = { generation: current.generation };
    pending.promise = (async () => {
      try {
        if (!current.refresh) throw new Error('No hay credenciales de renovación');
        const data = await requestRefresh(current.refresh);
        assertCurrent(current);
        if (data?.refresh === current.refresh) throw new Error('El refresh token no fue rotado');
        return save(current, data);
      } catch (error) {
        if (clear(current)) onExpired();
        throw error;
      } finally {
        if (flight === pending) flight = undefined;
      }
    })();
    flight = pending;
    return pending.promise;
  };
  return { snapshot, isCurrent, assertCurrent, beginLogin, clear, acceptLogin, isLoginCurrent, renew };
}

export const authSession = createAuthSession();

const excludedEndpoint = (url = '') => /\/auth\/(?:login|refresh|logout|password-reset(?:\/confirm)?|2fa\/verify)\/?(?:[?#]|$)/.test(url);

export function installAuthInterceptors(api, { session = authSession, requestRefresh, onExpired }) {
  api.interceptors.request.use((config) => {
    if (config._authSession) session.assertCurrent(config._authSession);
    const current = session.snapshot();
    config._authSession = { generation: current.generation, revision: current.revision };
    if (current.access) config.headers.Authorization = `Bearer ${current.access}`;
    else delete config.headers.Authorization;
    return config;
  }, (error) => { throw error; }, { synchronous: true });
  api.interceptors.response.use(
    (response) => {
      // Reject successful responses as well as failures from obsolete sessions.
      if (response.config._authSession) session.assertCurrent(response.config._authSession);
      return response;
    },
    async (error) => {
      const request = error.config;
      if (error.response?.status !== 401 || !request?._authSession || request._retry || excludedEndpoint(request.url)) {
        throw error;
      }
      session.assertCurrent(request._authSession);
      request._retry = true;
      await session.renew(request._authSession, requestRefresh, onExpired);
      // A login/logout can occur between refresh settlement and this continuation.
      session.assertCurrent(request._authSession);
      return api(request);
    },
  );
}
