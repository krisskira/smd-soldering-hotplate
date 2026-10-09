import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import type { Connect, Plugin, ResolvedConfig } from 'vite';

type Json = Record<string, any>;

const ROBOTS = 'index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1';

function readJson(root: string, file: string): Json {
  return JSON.parse(readFileSync(resolve(root, 'content', file), 'utf8'));
}

function esc(value: unknown) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function plain(value: unknown) {
  return String(value ?? '').replace(/\*\*(.+?)\*\*/g, '$1').replace(/`(.+?)`/g, '$1');
}

function absolute(base: string, path?: string) {
  if (!path) return undefined;
  if (/^https?:\/\//.test(path)) return path;
  return base ? `${base}/${path.replace(/^\.?\//, '')}` : undefined;
}

function sectionsOf(landing: Json): Json[] {
  return (landing.sections as Json[] | undefined) ?? [];
}

function heroOf(landing: Json) {
  return sectionsOf(landing).find((section) => section.type === 'hero') ?? {};
}

function structuredData(site: Json, landing: Json, base: string) {
  const url = base ? `${base}/` : undefined;
  const author = site.author && { '@type': 'Person', '@id': `${base}/#author`, ...site.author };
  const maker = site.maker && { '@type': 'Organization', '@id': `${base}/#maker`, name: site.maker.name, url: site.maker.url };
  const graph: Json[] = [
    {
      '@type': 'WebSite',
      '@id': `${base}/#website`,
      url,
      name: site.name,
      description: site.description,
      inLanguage: site.lang,
      ...(maker ? { publisher: { '@id': maker['@id'] } } : {}),
    },
  ];

  if (site.schema) {
    graph.push({
      name: site.name,
      description: site.description,
      url,
      image: absolute(base, site.ogImage),
      ...(author ? { author: { '@id': author['@id'] } } : {}),
      ...(maker ? { publisher: { '@id': maker['@id'] } } : {}),
      ...site.schema,
      '@id': `${base}/#product`,
    });
  }
  if (author) graph.push(author);
  if (maker) graph.push(maker);

  const faq = sectionsOf(landing).find((section) => section.type === 'faq');
  const faqItems = (faq?.items as Json[] | undefined) ?? [];
  if (faqItems.length) {
    graph.push({
      '@type': 'FAQPage',
      '@id': `${base}/#faq`,
      mainEntity: faqItems.map((item) => ({
        '@type': 'Question',
        name: plain(item.q),
        acceptedAnswer: { '@type': 'Answer', text: plain(item.a) },
      })),
    });
  }

  return JSON.stringify({ '@context': 'https://schema.org', '@graph': graph }, null, 2);
}

function localeScript(site: Json) {
  const key = JSON.stringify(`${site.slug || 'landing'}-locale`);
  const spanish = JSON.stringify(site.lang || 'es');
  return `(function () {
  try {
    var params = new URLSearchParams(location.search);
    var fromUrl = params.get('lang');
    var stored = localStorage.getItem(${key});
    var locale = fromUrl === 'en' || fromUrl === 'es' ? fromUrl : stored === 'en' || stored === 'es' ? stored : (navigator.language || '').toLowerCase().indexOf('en') === 0 ? 'en' : 'es';
    document.documentElement.lang = locale === 'en' ? 'en' : ${spanish};
  } catch (e) {}
})();`;
}

function themeScript(site: Json) {
  const key = JSON.stringify(`${site.slug || 'landing'}-theme`);
  const fallback = JSON.stringify(site.defaultTheme || 'system');
  return `(function () {
  try {
    var stored = localStorage.getItem(${key});
    var fallback = ${fallback};
    var theme = stored === 'dark' || stored === 'light' ? stored : fallback;
    if (theme === 'system') theme = matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    if (theme === 'dark') document.documentElement.classList.add('dark');
    document.documentElement.style.colorScheme = theme;
  } catch (e) {}
})();`;
}

// Solo un id de contenedor válido llega al HTML: el valor va dentro de un <script>.
function gtmId(site: Json) {
  const id = String(site.gtm ?? '').trim();
  return /^GTM-[A-Z0-9]+$/.test(id) ? id : '';
}

function gtmHead(site: Json) {
  const id = gtmId(site);
  if (!id) return '';
  return `<!-- Google Tag Manager -->
    <script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
    new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
    j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
    'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
    })(window,document,'script','dataLayer','${id}');</script>
    <!-- End Google Tag Manager -->`;
}

function gtmBody(site: Json) {
  const id = gtmId(site);
  if (!id) return '';
  return `<!-- Google Tag Manager (noscript) -->
    <noscript><iframe src="https://www.googletagmanager.com/ns.html?id=${id}"
    height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
    <!-- End Google Tag Manager (noscript) -->`;
}

function gtagId(site: Json) {
  const id = String(site.gtag ?? '').trim();
  return /^G-[A-Z0-9]+$/.test(id) ? id : '';
}

function gtagHead(site: Json) {
  const id = gtagId(site);
  if (!id) return '';
  return `<!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=${id}"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', '${id}');
    </script>`;
}

function headTags(site: Json, landing: Json, base: string) {
  const title = site.title || site.name;
  const canonical = base ? `${base}/` : undefined;
  const image = absolute(base, site.ogImage);
  const color = site.themeColor ?? {};
  const tags = [
    gtmHead(site),
    gtagHead(site),
    `<title>${esc(title)}</title>`,
    `<meta name="description" content="${esc(site.description)}" />`,
    site.keywords?.length ? `<meta name="keywords" content="${esc(site.keywords.join(', '))}" />` : '',
    site.author?.name ? `<meta name="author" content="${esc(site.author.name)}" />` : '',
    `<meta name="robots" content="${ROBOTS}" />`,
    `<meta name="googlebot" content="${ROBOTS}" />`,
    '<meta name="referrer" content="strict-origin-when-cross-origin" />',
    '<meta name="color-scheme" content="light dark" />',
    color.light ? `<meta name="theme-color" media="(prefers-color-scheme: light)" content="${esc(color.light)}" />` : '',
    color.dark ? `<meta name="theme-color" media="(prefers-color-scheme: dark)" content="${esc(color.dark)}" />` : '',
    canonical ? `<link rel="canonical" href="${esc(canonical)}" />` : '',
    canonical ? `<link rel="alternate" hreflang="es" href="${esc(canonical)}" />` : '',
    canonical ? `<link rel="alternate" hreflang="en" href="${esc(canonical.replace(/\/?$/, '/?lang=en'))}" />` : '',
    canonical ? `<link rel="alternate" hreflang="x-default" href="${esc(canonical)}" />` : '',
    site.favicon ? `<link rel="icon" href="./${esc(site.favicon)}" />` : '',
    site.appleTouchIcon ? `<link rel="apple-touch-icon" href="./${esc(site.appleTouchIcon)}" />` : '',
    '<link rel="manifest" href="./site.webmanifest" />',
    '<link rel="author" href="./llms.txt" type="text/plain" />',
    '<meta property="og:type" content="website" />',
    `<meta property="og:locale" content="${esc(site.locale)}" />`,
    '<meta property="og:locale:alternate" content="en_US" />',
    `<meta property="og:site_name" content="${esc(site.name)}" />`,
    canonical ? `<meta property="og:url" content="${esc(canonical)}" />` : '',
    `<meta property="og:title" content="${esc(title)}" />`,
    `<meta property="og:description" content="${esc(site.description)}" />`,
    image ? `<meta property="og:image" content="${esc(image)}" />` : '',
    image ? '<meta property="og:image:width" content="1200" />' : '',
    image ? '<meta property="og:image:height" content="630" />' : '',
    image ? '<meta property="og:image:type" content="image/jpeg" />' : '',
    image && site.ogImageAlt ? `<meta property="og:image:alt" content="${esc(site.ogImageAlt)}" />` : '',
    '<meta name="twitter:card" content="summary_large_image" />',
    `<meta name="twitter:title" content="${esc(title)}" />`,
    `<meta name="twitter:description" content="${esc(site.description)}" />`,
    image ? `<meta name="twitter:image" content="${esc(image)}" />` : '',
    site.fonts?.google ? '<link rel="preconnect" href="https://fonts.googleapis.com" />' : '',
    site.fonts?.google ? '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />' : '',
    site.fonts?.google ? `<link rel="stylesheet" href="${esc(site.fonts.google)}" />` : '',
    `<script type="application/ld+json">\n${structuredData(site, landing, base)}\n</script>`,
    `<script>\n${localeScript(site)}\n${themeScript(site)}\n</script>`,
  ];
  return tags.filter(Boolean).join('\n    ');
}

function noscript(site: Json, landing: Json) {
  const hero = heroOf(landing);
  const sections = sectionsOf(landing)
    .filter((section) => section.type !== 'hero' && section.id && section.title)
    .map((section) => `<li><strong>${esc(plain(section.title))}</strong>${section.lead ? ` — ${esc(plain(section.lead))}` : ''}</li>`)
    .join('\n          ');
  const links = [site.repo && `<li><a href="${esc(site.repo)}">Código fuente</a></li>`, site.author?.email && `<li><a href="mailto:${esc(site.author.email)}">${esc(site.author.email)}</a></li>`]
    .filter(Boolean)
    .join('\n          ');

  return `<noscript>
      <main style="font-family: system-ui, sans-serif; max-width: 720px; margin: 48px auto; padding: 0 20px; line-height: 1.6">
        <h1>${esc(plain([hero.title, hero.highlight].filter(Boolean).join(' ')) || site.name)}</h1>
        <p>${esc(plain(hero.lead || site.description))}</p>
        <ul>
          ${sections}
        </ul>
        <ul>
          ${links}
        </ul>
        <p>Activa JavaScript para ver la página completa.</p>
      </main>
    </noscript>`;
}

function sitemap(base: string) {
  const today = new Date().toISOString().slice(0, 10);
  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>${esc(`${base}/`)}</loc>
    <lastmod>${today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>
`;
}

function robots(base: string) {
  return `User-agent: *
Allow: /

Sitemap: ${base}/sitemap.xml
`;
}

function llms(site: Json, landing: Json, base: string) {
  const sections = sectionsOf(landing)
    .filter((section) => section.id && section.title)
    .map((section) => `- [${plain(section.title)}](${base}/#${section.id})${section.lead ? `: ${plain(section.lead)}` : ''}`)
    .join('\n');
  const links = [
    site.repo && `- Código fuente: ${site.repo}`,
    site.author?.name && `- Autor: ${site.author.name}${site.author.url ? ` (${site.author.url})` : ''}`,
    site.author?.email && `- Contacto: ${site.author.email}`,
    site.maker?.name && `- Estudio: ${site.maker.name}${site.maker.url ? ` (${site.maker.url})` : ''}`,
  ]
    .filter(Boolean)
    .join('\n');

  return `# ${site.name}

${plain(site.description)}

## Secciones

${sections}

## Enlaces

${links}
`;
}

function manifest(site: Json) {
  return JSON.stringify(
    {
      name: site.name,
      short_name: site.shortName || site.name,
      description: site.description,
      lang: site.lang,
      id: './',
      start_url: './',
      scope: './',
      display: 'standalone',
      background_color: site.themeColor?.dark || '#111111',
      theme_color: site.themeColor?.dark || '#111111',
      icons: ((site.icons as Json[] | undefined) ?? []).map((icon) => ({ purpose: 'any', ...icon })),
    },
    null,
    2,
  );
}

/**
 * Genera el <head>, el <noscript>, sitemap.xml, robots.txt, llms.txt y
 * site.webmanifest a partir de content/site.json y content/landing.json.
 * La URL pública sale de VITE_SITE_URL o, si no está, de site.url.
 */
export function landingFiles({ siteUrl }: { siteUrl?: string } = {}): Plugin {
  let config: ResolvedConfig;
  const load = () => {
    const site = readJson(config.root, 'site.json');
    const landing = readJson(config.root, 'landing.json');
    const base = String(siteUrl || site.url || '').replace(/\/$/, '');
    return { site, landing, base };
  };

  return {
    name: 'kriver-landing-files',
    configResolved(resolved) {
      config = resolved;
    },
    configureServer(server) {
      server.middlewares.use((request: Connect.IncomingMessage, response, next) => {
        const path = request.url?.split('?')[0] ?? '';
        const files: Record<string, [string, (loaded: { site: Json; landing: Json; base: string }) => string]> = {
          '/robots.txt': ['text/plain', (c) => robots(c.base)],
          '/sitemap.xml': ['application/xml', (c) => sitemap(c.base)],
          '/llms.txt': ['text/plain', (c) => llms(c.site, c.landing, c.base)],
          '/site.webmanifest': ['application/manifest+json', (c) => manifest(c.site)],
        };
        const file = files[path];
        if (!file) return next();
        response.setHeader('Content-Type', `${file[0]}; charset=utf-8`);
        response.end(file[1](load()));
      });
    },
    transformIndexHtml(html) {
      const { site, landing, base } = load();
      return html
        .replaceAll('%LANG%', esc(site.lang || 'es'))
        .replace('<!-- landing:head -->', headTags(site, landing, base))
        .replace('<!-- landing:body -->', gtmBody(site))
        .replace('<!-- landing:noscript -->', noscript(site, landing));
    },
    closeBundle() {
      if (config.command !== 'build') return;
      const { site, landing, base } = load();
      const outDir = resolve(config.root, config.build.outDir);
      writeFileSync(resolve(outDir, 'site.webmanifest'), manifest(site));
      writeFileSync(resolve(outDir, 'llms.txt'), llms(site, landing, base));
      if (base) {
        writeFileSync(resolve(outDir, 'sitemap.xml'), sitemap(base));
        writeFileSync(resolve(outDir, 'robots.txt'), robots(base));
      }
    },
  };
}
