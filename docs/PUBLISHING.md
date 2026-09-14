# Publishing this repository

Suggested repository name: `px13-linux-audio`

Suggested description:

> Documented ASUS ProArt PX13 HN7306EAC speaker workaround for Ubuntu 26.04: verified firmware extraction, UCM correction, PCI recovery, diagnostics, and rollback.

Create an empty repository under your GitHub account. Do not initialize the remote with another README or license. Then, from this local directory:

```bash
git add .
git commit -m "Document PX13 HN7306EAC speaker repair and add repair tools"
git remote add origin https://github.com/YOUR-USERNAME/px13-linux-audio.git
git push -u origin main
```

Replace `YOUR-USERNAME` with your GitHub account. If this directory came from the ZIP rather than the prepared Git repository, first run `git init -b main`.

Before pushing, inspect `git diff --cached --stat` and `git ls-files`. Firmware, downloaded driver packages, and personal logs must not be included. Ignore rules are included, but still review staged content.

The README is the project landing page. The issue template will be available in GitHub's Issues interface. The upstream issue in `docs/UPSTREAM-ISSUE.md` is a draft for a separate maintainer report, not a report that has already been filed.
