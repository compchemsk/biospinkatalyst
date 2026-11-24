# compchemsk.github.io

Personal website of Soumyajit Karmakar. Everything is static: `index.html`, images in `assets/`, and two small data files that the page reads when it loads.

| File | What it controls | How it changes |
|---|---|---|
| `data/publications.json` | New papers from Google Scholar that the curated list does not show yet | Automatically, every day, by the GitHub Action |
| `data/settings.json` | Conferences, conferences outside India, best poster awards, journal covers | From **⚙ Site settings** at the bottom of the website, or by editing the file |

The "journal articles published online" number is counted by the page itself: published journal papers and reviews in the list, plus any new journal paper found on Google Scholar. Preprints, chapters, conference abstracts and manuscripts under review or in preparation are not counted.

## One-time setup

1. Create a public repository named **`compchemsk.github.io`** and upload everything in this folder, keeping the folder structure (including the hidden `.github` folder).
2. **Settings → Pages**: Source = *Deploy from a branch*, Branch = `main`, folder `/ (root)`. The site appears at <https://compchemsk.github.io> within a minute or two.
3. **Settings → Actions → General → Workflow permissions**: choose *Read and write permissions*, so the daily job can save `data/publications.json`.
4. **Actions → Update publications from Google Scholar → Run workflow** once to fill the list straight away.

### Making the Google Scholar update reliable

Google Scholar has no official API and often blocks requests from GitHub's servers. The script tries, in order:

1. **SerpAPI** (recommended). Create a free account at serpapi.com (the free plan's monthly searches are more than enough for one daily check), then add the key under **Settings → Secrets and variables → Actions → New repository secret** with the name `SERPAPI_KEY`.
2. **scholarly**, which reads Google Scholar directly. It works when Scholar does not block the request.
3. **ORCID** (0000-0003-4867-0970), only if both Scholar routes fail. Keep your ORCID record synced with Crossref so new DOIs appear there.

If every source fails on a given day, the file is left as it was and the website keeps showing the last good list.

## Updating conferences and poster awards from the website

Open the site, scroll to the footer, click **⚙ Site settings**, change the numbers and press **Save**. Saving needs a GitHub token the first time:

1. GitHub → **Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token**.
2. Repository access: *Only select repositories* → `compchemsk.github.io`. Permissions → *Contents*: **Read and write**. Nothing else.
3. Paste the token into the settings panel. Tick "Remember the token on this device" only on your own computer.

The token stays in your browser and is sent only to api.github.com. Visitors without a token can open the panel but cannot change anything.

You can also edit `data/settings.json` directly on GitHub; the page picks up the new numbers on the next visit.
