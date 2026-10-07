import type { Section as PageSection } from '../types';
import { ArrowUpRight } from 'lucide-react';
import { Icon } from '../components/Icon';
import { BrandBar, Paragraphs, Reveal, Rich, Section } from '../components/ui';
import { useI18n } from '../i18n/useI18n';
import { focusRing } from '../lib/styles';

export function Author({ section }: { section: PageSection }) {
  const { t } = useI18n();
  const initials = (section.badge ?? '').slice(0, 2);

  return (
    <Section section={section}>
      <Reveal className="grid items-center gap-10 rounded-3xl border border-line/60 bg-card p-8 sm:p-10 lg:grid-cols-[auto_minmax(0,1fr)] lg:gap-14 lg:p-14">
        <div
          aria-hidden="true"
          className="mx-auto flex h-32 w-32 items-center justify-center rounded-full bg-[linear-gradient(135deg,var(--accent),var(--accent-2))] font-display text-4xl font-semibold text-on-accent shadow-card lg:h-40 lg:w-40 lg:text-5xl"
        >
          {initials}
        </div>
        <div>
          {section.kicker ? (
            <p className="flex items-center gap-3 text-sm font-semibold uppercase tracking-[0.18em] text-accent">
              <BrandBar />
              {section.kicker}
            </p>
          ) : null}
          <h2 id={`${section.id}-title`} className="mt-4 font-display text-3xl font-semibold leading-tight tracking-[-0.01em] text-fg sm:text-4xl">
            <Rich text={section.title} />
          </h2>
          {section.highlight ? <p className="mt-2 font-semibold text-accent">{section.highlight}</p> : null}
          <div className="mt-5 text-lg leading-relaxed text-muted">
            <Paragraphs text={section.body} />
          </div>
          <ul className="mt-8 flex flex-wrap gap-3">
            {section.items.map((link) => (
              <li key={link.href}>
                <a
                  href={link.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`inline-flex h-11 items-center gap-2 rounded-full border border-line px-4 text-sm font-semibold text-fg transition hover:border-accent hover:text-accent ${focusRing}`}
                >
                  <Icon name={link.icon} size={18} />
                  {link.label}
                  <ArrowUpRight size={14} aria-hidden="true" className="opacity-60" />
                  <span className="sr-only">{t('external')}</span>
                </a>
              </li>
            ))}
          </ul>
        </div>
      </Reveal>
    </Section>
  );
}
