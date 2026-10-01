# ecgmeans.com

Static site for **ECG Means** — plain-English explanations of the phrases printed on ECG/EKG
reports, reviewed by Dr. Faisal Irshad, MBBS (PMDC 54440-S).

## Structure
- Pages are pre-built static HTML (one `index.html` per directory) at the repo root.
- `content/` + `build.py` + `make_assets.py` are the source generator (kept in the repo,
  blocked from the web by `.htaccess` and `robots.txt`).
- `sitemap.xml`, `robots.txt`, `llms.txt`, `llms-full.txt`, `.htaccess`, `index.php`, `404.html`.

## Build locally
```
pip install markdown pillow --break-system-packages
python3 build.py && python3 make_assets.py
```
Output is written in place (repo root).

## Deploy
Push to `main`. The GitHub Action (`.github/workflows/deploy.yml`) triggers a Cloudways
git pull into the application webroot (server 1638726, app 6684252) and purges the cache.
Requires repo secrets `CLOUDWAYS_EMAIL` and `CLOUDWAYS_API_KEY`.
