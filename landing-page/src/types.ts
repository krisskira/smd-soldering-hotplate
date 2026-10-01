export type Locale = 'es' | 'en';

export type Action = {
  href: string;
  label: string;
  variant?: string;
  icon?: string;
};

export type Media = {
  type?: string;
  src?: string;
  alt?: string;
  poster?: string;
  frame?: string;
  width?: number;
  height?: number;
  autoplay?: boolean;
  muted?: boolean;
  pixelated?: boolean;
  webm?: string;
  title?: string;
  caption?: string;
};

export type ContentItem = {
  label?: string;
  value?: string;
  title?: string;
  text?: string;
  icon?: string;
  href?: string;
  q?: string;
  a?: string;
  note?: string;
  unit?: string;
  src?: string;
  alt?: string;
  caption?: string;
  frame?: string;
  width?: number;
  height?: number;
  type?: string;
  media?: Media;
};

export type SpecGroup = {
  title: string;
  rows: [string, string][];
};

export type Section = {
  type: string;
  id?: string;
  nav?: string;
  title?: string;
  lead?: string;
  kicker?: string;
  tone?: string;
  align?: string;
  body?: string | string[];
  badge?: string;
  highlight?: string;
  reverse?: boolean;
  columns?: number;
  actions?: Action[];
  items: ContentItem[];
  stats?: { label: string; value: string }[];
  media?: Media;
  next?: { href: string; label: string };
  tabs: { label: string; code: string }[];
  groups: SpecGroup[];
  bullets?: string[];
  video?: Media;
};

export type NavLink = { href: string; label: string };

export type Site = {
  slug?: string;
  name: string;
  title?: string;
  description?: string;
  keywords?: string[];
  lang?: string;
  locale?: string;
  logo?: string;
  badge?: string;
  ogImageAlt?: string;
  repo?: string;
  defaultTheme?: string;
  themeColor?: { light?: string; dark?: string };
  cta?: NavLink;
  nav?: NavLink[];
  author?: { name?: string; email?: string; url?: string };
  maker?: { name: string; url: string };
  footer?: {
    text?: string;
    rights?: string;
    columns?: { title: string; links: NavLink[] }[];
  };
};

export type Landing = {
  sections: Section[];
};
