Branding assets

- Place your institutional logo files in this folder.
- Recommended: SVG (logo.svg) for crisp rendering on all sizes. PNG fallback also OK (logo.png).

Configure in environment (.env):

APP_BRAND_NAME="PumaSP"
APP_BRAND_TAGLINE="Gestor de Servicios Tecnologicos de la Universidad del Magdalena"
APP_BRAND_LOGO="branding/logo.svg"

If APP_BRAND_LOGO is not set, the app will fall back to using the default favicon.svg.
