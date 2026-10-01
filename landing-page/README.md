# Sitio de HotPlate

React, TypeScript y Vite. Se publica en
<https://krisskira.github.io/smd-soldering-hotplate/>.

```bash
npm install
npm run dev
npm run build
```

- Texto y secciones: `content/landing.json`
- Nombre, SEO y enlaces: `content/site.json`
- Traducción al inglés: `content/en.json` (la clave es el texto en español, exacto)
- Colores y fuentes: `content/theme.css`
- Imágenes y video: `public/media/`

## Publicar

El workflow `.github/workflows/pages.yml` construye y publica en GitHub Pages
cada push a `main` que toque `landing-page/`. En el repositorio:
**Settings → Pages → Source: GitHub Actions**.
