import rawSite from '../../content/site.json' with { type: 'json' };
import rawLanding from '../../content/landing.json' with { type: 'json' };
import type { Landing, Site } from '../types';

const ENV_TOKEN = /\{\{(VITE_[A-Z0-9_]+)\}\}/g;
const DROP = Symbol('drop');

// "{{VITE_APP_URL}}/login" toma la variable del .env en el build. Si falta,
// el objeto que tiene ese href (botón, enlace) desaparece en vez de quedar roto.
function resolveEnv(value: unknown, key?: string): unknown {
  if (typeof value === 'string') {
    let missing = false;
    const out = value.replace(ENV_TOKEN, (_, name: string) => {
      const found = import.meta.env[name];
      if (!found) missing = true;
      return (found ?? '').replace(/\/$/, '');
    });
    return missing && key === 'href' ? DROP : out;
  }
  if (Array.isArray(value)) {
    return value.map((item) => resolveEnv(item)).filter((item) => item !== DROP);
  }
  if (value && typeof value === 'object') {
    const entries = Object.entries(value).map(([childKey, child]) => [childKey, resolveEnv(child, childKey)] as const);
    if (entries.some(([, child]) => child === DROP)) return DROP;
    return Object.fromEntries(entries);
  }
  return value;
}

export const site = resolveEnv(rawSite) as Site;
export const landing = resolveEnv(rawLanding) as Landing;

export function asset(path?: string) {
  if (!path) return undefined;
  if (/^(https?:|data:|blob:)/.test(path)) return path;
  return `${import.meta.env.BASE_URL}${path.replace(/^\.?\//, '')}`;
}

export function isExternal(href?: string) {
  return /^https?:\/\//.test(href ?? '');
}
