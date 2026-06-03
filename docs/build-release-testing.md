# Build and release testing

This repository deploys Hugo to GitHub Pages from `main` via `.github/workflows/hugo.yaml`.

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

## Branch protection settings (manual)

In GitHub repository settings, branch protection for `main` should require:

1. Status check: `Validate Hugo build (PR) / validate`
2. (Optional) At least one approving review for content/config/workflow changes.

## Controlled test sequence

Use this sequence to verify build/release safety before relying on it:

1. **Fail test (PR)**: introduce a YAML syntax error in `data/data.yml` on a test branch and open a PR. Confirm validation fails.
2. **Pass test (PR)**: fix YAML and confirm validation succeeds and uploads `hugo-pr-public` artifact.
3. **Deploy test (`main`)**: merge a harmless change and confirm deploy job plus homepage smoke check succeeds.
4. **Regression check**: verify key contact links (including website URL) on the live page.
