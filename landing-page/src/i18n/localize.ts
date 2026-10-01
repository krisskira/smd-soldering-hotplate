import catalog from '../../content/en.json' with { type: 'json' };
import type { Locale } from '../types';

// El español de content/ es la fuente. En inglés, cada texto se busca tal cual
// en content/en.json. Lo que no esté se queda en español.
const phrases = catalog as Record<string, string>;

const KEEP = new Set([
  'slug',
  'id',
  'icon',
  'href',
  'to',
  'src',
  'poster',
  'frame',
  'type',
  'variant',
  'tone',
  'align',
  'lang',
  'locale',
  'url',
  'logo',
  'favicon',
  'ogImage',
  'repo',
  'width',
  'height',
  'columns',
  'defaultTheme',
  '@type',
  'applicationCategory',
]);

function keepAsIs(key: string, value: unknown) {
  if (KEEP.has(key)) return true;
  return (
    typeof value === 'string' &&
    (/^https?:/.test(value) ||
      value.startsWith('/') ||
      /^\+\d[\d\s()-]{6,}$/.test(value) ||
      value.startsWith('media/') ||
      value.startsWith('{{') ||
      value.includes('@') ||
      /^#[0-9a-fA-F]{3,8}$/.test(value))
  );
}

function isLocaleMessage(value: object): value is { es: string; en: string } {
  const record = value as Record<string, unknown>;
  const keys = Object.keys(record);
  return keys.length === 2 && typeof record.es === 'string' && typeof record.en === 'string';
}

export function localize(value: unknown, locale: Locale): unknown {
  if (Array.isArray(value)) return value.map((item) => localize(item, locale));
  if (value && typeof value === 'object') {
    if (isLocaleMessage(value)) return value[locale] || value.es;
    return Object.fromEntries(
      Object.entries(value).map(([childKey, item]) => [childKey, keepAsIs(childKey, item) ? item : localize(item, locale)]),
    );
  }
  if (typeof value === 'string' && locale === 'en') return phrases[value] ?? value;
  return value;
}
