import { createContext } from 'react';
import type { Locale } from '../types';
import type { MessageKey } from './messages';

export type I18nValue = {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: MessageKey, vars?: Record<string, string>) => string;
};

export const LocaleContext = createContext<I18nValue | null>(null);
