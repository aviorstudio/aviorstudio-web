# Avior Studio web

The public [avior.studio](https://avior.studio) site. Three static Astro pages:
an index, `/devtools`, and `/games`.

There is no authentication, no application state, no backend and no runtime
environment configuration. The pages ship no JavaScript, which is why there are
no integrations in `astro.config.mjs` and why CI fails on a `<script src>` in
any build output.

## Commands

| Command | Action |
| --- | --- |
| `bun install` | Install dependencies |
| `bun dev` | Start the Astro development server |
| `bun run build` | Generate the static site in `dist/` |
| `bun preview` | Preview the static build |

## Pages

- **`/`** — what the studio is, the two doors, and how the tools and games
  relate. The door lists name their contents rather than saying "and more", so
  the index cannot promise a page something that is not on it.
- **`/devtools`** — GDAM and gdlint, with install commands and links, then the
  fourteen `gd-*` addons on the registry.
- **`/games`** — termcade, Castle Drop, Prizm and Fields of Revik.

`src/components/Entry.astro` is the shared product block used by both inner
pages: a fixed-width head column (name, tagline, status, meta) beside a body
that flows.

The addons on `/devtools` deliberately do not use it. `Entry` is sized for a
product with a status, a platform line and an install command of its own;
fourteen of them would bury the two tools the page is mostly about. They are a
card grid instead, defined as an `addons` array at the top of the page the way
`index.astro` defines its `doors`. The install line is stated once above the
grid because it is `gdam install @aviorstudio/<name>` for all fourteen, and
each card links to its repository rather than carrying its own link row.

## Status and links

Every product on the site is either linkable or explicitly not, and the page
says which. Three of the six product repositories are private, and a link to a
repository a reader cannot open is worse than no link:

| Product | Repository | Public link on the site |
| --- | --- | --- |
| GDAM | public | `gdam.dev` and GitHub |
| gdlint | public | `gdlint.dev` and GitHub |
| termcade | public | GitHub (`termcade.com` is still a placeholder, so it is not linked) |
| Castle Drop | private | none — labelled Prototype |
| Prizm | private | none — labelled Prototype |
| Fields of Revik | private | `fieldsofrevik.com`, which is live |

The status dot is hollow by default and filled only for something a reader can
run today — a difference told by fill rather than by colour, so it survives
greyscale and colour blindness both. Only termcade, GDAM and gdlint are filled.

All fourteen addons are public on GitHub and resolve on the registry, so every
card links to its repository and none carries a status dot: there is no third
state to tell apart. Two more `gd-*` directories exist in the workspace —
`gd-animate` and `gd-storybook` — and are **not** on the page. Both are empty
repositories with a one-line README, no `addon/`, no release and no registry
entry; `api.gdam.dev` returns a placeholder rather than a package for them.
They go on the page when they resolve.

## Copy

Every blurb comes from the product's own repository — the READMEs, the design
docs, and the config that decides defaults — not from a positioning exercise.
The claims worth re-checking when a product changes:

- **GDAM**: the separate `gdam.link.json`, and that publishing is authenticated
  with an owner-scoped secret key while the CLI itself carries none.
- **gdlint**: four rules enabled by default out of sixteen, and that it is
  deliberately not an architecture checker.
- **termcade**: games are sandboxed wasm under wazero with no filesystem and no
  network, a broken one shows up dimmed rather than taking the arcade down, and
  the arcade binary is also the dev kit.
- **Castle Drop**: progression is castle upgrades only; waves, enemies, towers
  and tuning are Inspector-authored resources.
- **Prizm**: no avatar, combat, health, timer or fail state in the MVP.
- **Fields of Revik**: one deterministic core shared by the client and a
  headless Godot server; online play is fully server-authoritative.
- **The addons**: the count. "Fourteen" is written out in the `/devtools`
  headline and intro, in the `/` door list, closing line and first principle,
  and in three meta descriptions, so publishing a fifteenth is a seven-place
  edit. Also each blurb's stated boundary — gd-network leaving auth and
  reconnect to the game, gd-supabase and gd-pocketbase decoding tokens rather
  than verifying them, gd-redis keeping `flushdb` behind an explicit opt-in,
  gd-playwright's CLI being strictly read-only — since those are the claims a
  reader would act on before installing.

## Colour and the mark

The background is `#252424`, sampled out of `src/assets/aviorstudio-logo.png` —
the mark ships with that colour baked in behind it, and matching it is what lets
the ibis sit on the page instead of inside a visible square. The remaining few
shades of difference are handled by fading the image's edges out with a radial
mask rather than by repainting the asset.

Everything else is greyscale on purpose. Each product has a colour of its own —
gdlint wears the Godot editor blue, gdam.dev its slate, Fields of Revik its
parchment — and a studio that invented a seventh would be competing with the six
things it exists to point at.

`public/logo.png`, `public/logo-mark.png` and `public/favicon.png` are generated
from `src/assets/aviorstudio-logo.png`, which is the source of record:

```sh
magick src/assets/aviorstudio-logo.png -resize 512x512 -strip public/logo.png
magick src/assets/aviorstudio-logo.png -crop 810x810+120+112 +repage -resize 96x96  -strip public/logo-mark.png
magick src/assets/aviorstudio-logo.png -crop 810x810+120+112 +repage -resize 256x256 -strip public/favicon.png
```

The crop is tighter for the small sizes: at 30px the uncropped mark is a smudge,
because the artwork's own margin eats most of the space.

Fonts are the platform's own. No font is fetched, so no visitor's IP reaches a
font CDN and no CSP exception is needed to render the pages.

## Domain

The site is `https://avior.studio`. The host appears in exactly three places —
the canonical and structured-data URLs in `src/layouts/Full.astro`, the sitemap
line in `public/robots.txt`, and the three `<loc>` entries in
`public/sitemap.xml` — so moving it is a three-file change.

`aviorstudio.com` is a different domain and is not this site. Nothing here
should point at it.
