import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { site } from '../lib/content';
import type { Locale } from '../types';
import { LocaleContext } from './context';
import { translate, type MessageKey } from './messages';

const STORAGE_KEY = `${site.slug || 'landing'}-locale`;

function readLocale(): Locale {
  const fromUrl = new URLSearchParams(window.location.search).get('lang');
  if (fromUrl === 'en' || fromUrl === 'es') return fromUrl;
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === 'en' || stored === 'es') return stored;
  return navigator.language?.toLowerCase().startsWith('en') ? 'en' : 'es';
}

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocale] = useState<Locale>(readLocale);
  const value = useMemo(
    () => ({
      locale,
      setLocale,
      t: (key: MessageKey, vars?: Record<string, string>) => translate(locale, key, vars),
    }),
    [locale],
  );

  useEffect(() => {
    document.documentElement.lang = locale === 'en' ? 'en' : site.lang || 'es';
    localStorage.setItem(STORAGE_KEY, locale);
    const url = new URL(window.location.href);
    if (url.searchParams.get('lang') !== locale) {
      url.searchParams.set('lang', locale);
      window.history.replaceState(window.history.state, '', url);
    }
  }, [locale]);

  return <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>;
}
