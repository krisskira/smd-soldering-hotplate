import { useEffect, useState } from 'react';
import { Pause, Play } from 'lucide-react';
import type { ContentItem } from '../types';
import { useI18n } from '../i18n/useI18n';
import { asset } from '../lib/content';
import { focusRing } from '../lib/styles';
import { Rich } from './ui';

const INTERVAL_MS = 2600;

export function Carousel({ items }: { items: ContentItem[] }) {
  const { t } = useI18n();
  const [active, setActive] = useState(0);
  const [playing, setPlaying] = useState(() => !window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  const [hover, setHover] = useState(false);
  const first = items[0];

  useEffect(() => {
    if (!playing || hover || items.length < 2) return undefined;
    const timer = window.setInterval(() => setActive((index) => (index + 1) % items.length), INTERVAL_MS);
    return () => window.clearInterval(timer);
  }, [playing, hover, items.length]);

  if (!first) return null;
  const current = items[active];

  return (
    <figure aria-roledescription="carousel" aria-label={t('carousel.label')} onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)}>
      <div className="rounded-[22px] bg-[linear-gradient(145deg,#2b2f35,#16181c)] p-3 shadow-card ring-1 ring-white/10 sm:p-4">
        <div className="relative overflow-hidden rounded-lg ring-1 ring-black/60" style={{ aspectRatio: `${first.width} / ${first.height}` }}>
          {items.map((item, index) => (
            <img
              key={item.src}
              src={asset(item.src)}
              alt={index === active ? (item.alt ?? '') : ''}
              aria-hidden={index === active ? undefined : true}
              loading="lazy"
              decoding="async"
              width={item.width}
              height={item.height}
              className={`pixelated absolute inset-0 block h-full w-full transition-opacity duration-500 ${index === active ? 'opacity-100' : 'opacity-0'}`}
            />
          ))}
        </div>
      </div>
      <div className="mt-4 flex items-center gap-4">
        <button
          type="button"
          onClick={() => setPlaying(!playing)}
          aria-label={playing ? t('carousel.pause') : t('carousel.play')}
          className={`inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-line/60 text-fg transition hover:border-accent hover:text-accent ${focusRing}`}
        >
          {playing ? <Pause size={16} aria-hidden="true" /> : <Play size={16} aria-hidden="true" />}
        </button>
        <div className="flex gap-1.5">
          {items.map((item, index) => (
            <button
              key={item.src}
              type="button"
              onClick={() => setActive(index)}
              aria-label={t('carousel.go', { n: String(index + 1) })}
              aria-current={index === active ? 'true' : undefined}
              className={`h-2 rounded-full transition-all ${focusRing} ${index === active ? 'w-6 bg-accent' : 'w-2 bg-line hover:bg-muted'}`}
            />
          ))}
        </div>
      </div>
      {current.caption ? (
        <figcaption aria-live="polite" className="mt-3 min-h-[3em] text-sm leading-relaxed text-muted">
          <Rich text={current.caption} />
        </figcaption>
      ) : null}
    </figure>
  );
}
