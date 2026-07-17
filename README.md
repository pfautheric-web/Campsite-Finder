# Northeast Campsite Finder — self-updating site

A single-page campsite finder for the Northeast US that updates its own availability
data server-side every 30 minutes. Visitors see live "sites open / full" badges with
no button-pressing and nothing for you to maintain.

## How it works

- `index.html` — the whole site (116 campgrounds, location-aware distances, filters,
  weekend scanner, booking cheat sheet, direct per-park booking links).
- `scripts/fetch_availability.py` — pulls per-site availability for all Recreation.gov
  campgrounds (White Mountains, Green Mountains, Acadia, Evans Notch, Winhall Brook)
  for the next ~4 months and writes `availability.json`.
- `.github/workflows/availability.yml` — runs that script on GitHub's servers every
  30 minutes, free, forever. When fresh data exists, the page shows badges instantly;
  if the data is ever stale or missing, the page falls back to checking from the
  visitor's browser, so it degrades gracefully instead of breaking.

State-park systems (ReserveAmerica, Vermont, Maine, New Jersey) offer no public
availability data — those rows link directly to each park's booking page instead.
See "Full state-park coverage" below for the paid path.

## Deploy (one time, ~5 minutes, free)

1. Create a GitHub account if you don't have one, then create a new **public**
   repository (e.g. `campsite-finder`).
2. Upload the contents of this folder to the repository (drag-and-drop works on
   github.com: "uploading an existing file"). Make sure the `.github` folder comes
   along — if you upload via the web UI, create the file
   `.github/workflows/availability.yml` manually with "Add file → Create new file".
3. Repo **Settings → Pages** → Source: "Deploy from a branch" → Branch: `main`,
   folder `/ (root)` → Save.
4. Repo **Actions** tab → enable workflows if prompted → open "Update availability"
   → "Run workflow" once to seed the data.

Your site is now live at `https://<your-username>.github.io/campsite-finder/`
and keeps itself updated. Share the URL with anyone.

## Full state-park coverage (optional, paid)

ReserveAmerica-based state parks (MA, NH, NY, CT, PA) publish no API and are behind
bot protection. The legitimate route to their data is a licensed feed: ReserveAmerica
is operated by **Aspira**, which offers partner/affiliate API access — contact them
via reserveamerica.com (Partnerships) if you want to pursue it. Services like Campnab
($10/mo) monitor those parks but only send personal alerts; they don't provide data
feeds that could power this page.

## Notes

- The updater identifies itself politely and throttles to ~1 request/second.
- GitHub Actions' scheduler can drift 5–15 minutes under load; the page shows the
  data's actual age.
- To add/remove campgrounds, edit the `DB` array in `index.html`. Recreation.gov
  entries with a `recId` are picked up by the updater automatically on its next run.
