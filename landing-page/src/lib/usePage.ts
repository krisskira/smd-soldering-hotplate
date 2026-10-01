import { useMemo } from 'react';
import { useI18n } from '../i18n/useI18n';
import { localize } from '../i18n/localize';
import type { Landing, Site } from '../types';
import { landing, site } from './content';

// site y landing en el idioma activo. El español es el contenido original.
export function usePage() {
  const { locale } = useI18n();
  return useMemo(
    () => ({
      site: localize(site, locale) as Site,
      landing: localize(landing, locale) as Landing,
    }),
    [locale],
  );
}
