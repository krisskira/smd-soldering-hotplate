import type { ComponentType } from 'react';
import type { Section } from '../types';
import { Code } from './Code';
import { Cta } from './Cta';
import { Faq } from './Faq';
import { Features } from './Features';
import { Gallery } from './Gallery';
import { Hero } from './Hero';
import { Showcase } from './Showcase';
import { Specs } from './Specs';
import { Split } from './Split';
import { Stats } from './Stats';
import { Steps } from './Steps';
import { Video } from './Video';

/** "type" en content/landing.json → componente. */
export const sections: Record<string, ComponentType<{ section: Section }>> = {
  hero: Hero,
  features: Features,
  split: Split,
  showcase: Showcase,
  video: Video,
  steps: Steps,
  stats: Stats,
  specs: Specs,
  code: Code,
  faq: Faq,
  gallery: Gallery,
  cta: Cta,
};
