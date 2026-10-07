# Build and release testing

This repository deploys Hugo to GitHub Pages from `main` via `.github/workflows/hugo.yaml`.
During the EmDash migration it also deploys the EmDash (Astro) site to Cloudflare Workers
(see [EmDash on Cloudflare Workers](#emdash-on-cloudflare-workers)). Both pipelines run until cutover.

## EmDash on Cloudflare Workers

### Workflows

- `.github/workflows/emdash-deploy.yaml` (push to `main`, manual dispatch): `npm ci`, then
  `npm run deploy` (`astro build && wrangler deploy`). If the `CLOUDFLARE_API_TOKEN` secret
  is not set, the job logs a notice and succeeds without deploying.
  - Wrangler creates the D1 database (`worwood-com`) and R2 bucket (`worwood-com-media`)
    named in `wrangler.jsonc` on the first deploy if they don't exist.
  - EmDash applies its database migrations and the seed schema on the Worker's first
    request (default `auto` migration mode). No migration step runs in CI.
- `.github/workflows/emdash-pr-validate.yaml` (PRs to `main`), job `validate-emdash`:
  - `npm ci`, `emdash seed --validate`, `npm run build`.
  - Starts `astro preview` (workerd with local D1/R2), requests `/` so migrations run,
    loads `seed/seed.json` content into the local D1 sqlite file with `emdash seed`.
  - Runs `.github/scripts/smoke_check_url.py`: `/` returns 200, resume sections render,
    and every local `href`/`src` returns 200. An empty database fails the check.

Reproduce the PR check locally:

```bash
rm -rf .wrangler dist && npm ci && npm run build
npx astro preview --port 4329 &   # wait until http://localhost:4329/ responds
curl -fsS -o /dev/null http://localhost:4329/
npx emdash seed seed/seed.json --database "$(find .wrangler/state/v3/d1/miniflare-D1DatabaseObject -name '*.sqlite' | head -1)"
python3 .github/scripts/smoke_check_url.py http://localhost:4329
npx astro preview stop
```

### One-time Cloudflare setup (owner)

1. **API token**: in Cloudflare → My Profile → API Tokens, create a token from the
   "Edit Cloudflare Workers" template and add **D1: Edit** (account) so Wrangler can
   create and bind the database. Scope it to the worwood account and the `worwood.com` zone.
2. **GitHub secrets** (repo → Settings → Secrets and variables → Actions):
   `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` (Workers & Pages overview, right sidebar).
3. **First deploy**: run *Deploy EmDash site to Cloudflare Workers* from the Actions tab
   (or merge to `main`). Confirm the D1 database `worwood-com` and R2 bucket
   `worwood-com-media` now exist in the dashboard. If R2 isn't enabled on the account yet,
   enable it in the dashboard (R2 → Purchase/enable; the free tier is fine) and re-run.
4. **Encryption key** (Worker secret, never committed):
   ```bash
   npx emdash secrets generate            # prints a new key
   npx wrangler secret put EMDASH_ENCRYPTION_KEY   # paste the key
   ```
   Keep the key in a password manager. Losing it makes stored plugin secrets unreadable.
5. **Custom domain**: add
   `"routes": [{ "pattern": "worwood.com", "custom_domain": true }]` to `wrangler.jsonc`
   in the Cutover task (not before; GitHub Pages still serves the domain). Before running
   the setup wizard on that domain, set `EMDASH_SITE_URL=https://worwood.com` as a Worker
   variable so passkeys bind to the right origin.
6. **Setup wizard**: open `https://<worker>.workers.dev/_emdash/admin` (or the custom domain
   once routed), create the admin account, and choose **start with sample content**. That
   loads the resume entries from `seed/seed.json`; without it the page renders empty.
   Passkeys are tied to the origin where you register them: one created on `workers.dev`
   won't sign you in on `worwood.com`, so add a passkey again after cutover.
7. **Verify**: homepage renders the resume, admin sign-in works, a media upload works, and
   `npx wrangler tail` shows the per-minute cron (`scheduled`) running. `npx emdash doctor`
   checks the cron and scheduled-handler wiring.

## Current pipeline map

- `build` job:
  - Installs Hugo `0.141.0` and Dart Sass.
  - Checks out repository with theme submodule.
  - Runs Hugo production build to `public/`.
  - Runs smoke checks against generated output.
  - Uploads Pages artifact.
- `deploy` job:
  - Deploys uploaded artifact to GitHub Pages.
  - Performs a basic reachability check against `page_url`.

## PR validation pipeline

`.github/workflows/hugo-pr-validate.yaml` runs on pull requests to `main` and:

- Mirrors build inputs used by production (Hugo, Sass, submodules).
- Builds with a deterministic preview base URL.
- Runs the same smoke checks as production.
- Uploads `public/` as a PR artifact for manual inspection.

## Smoke checks

`.github/scripts/smoke_check_public.py` validates:

- `public/index.html` exists.
- HTML output exists and appears valid.
- Local `href` and `src` references resolve to files/directories in `public/`.

## Branch protection settings

`main` is protected to require the PR validation status check:

1. Required status check context: `validate` (workflow: **Validate Hugo build (PR)**).
   Once this migration merges, also require `validate-emdash` (workflow: **Validate EmDash build (PR)**).
2. (Optional) Add required approving reviews in repository settings if desired.

If `gh` commands fail with `HTTP 401: Bad credentials`, unset `GITHUB_TOKEN` from direnv before running GitHub CLI commands.

## Controlled test sequence

Use this sequence to verify build/release safety before relying on it:

1. **Fail test (PR)**: introduce a YAML syntax error in `data/data.yml` on a test branch and open a PR. Confirm validation fails.
2. **Pass test (PR)**: fix YAML and confirm validation succeeds and uploads `hugo-pr-public` artifact.
3. **Deploy test (`main`)**: merge a harmless change and confirm deploy job plus homepage smoke check succeeds.
4. **Regression check**: verify key contact links (including website URL) on the live page.
