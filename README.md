# ecgmeans.com — source branch

This `source` branch holds the generator. The `main` branch holds ONLY the built static site,
because Cloudways (Lightning/Nginx stack) serves every file in the repo publicly and ignores .htaccess.

## Build + deploy
```
PYTHONHASHSEED=0 python3 build.py   # pages, schema, sitemap, llms.txt -> site/
python3 make_assets.py              # css, icons
node make_og.js                     # 1200x630 social images (needs playwright)
./deploy.sh                         # copies site/ into a main worktree, commits, pushes
```
Content: content/<slug>.txt (@@FIELD@@ format). Set @@UPDATED@@ when a page is medically re-reviewed;
byline, footer, schema dateModified and sitemap lastmod all read that one value.

Server rules (www redirect, security headers) live in Cloudways → Application → Web Rules, not .htaccess.
