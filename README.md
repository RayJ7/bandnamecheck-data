# Band name occupancy data — 2026-10-21

A snapshot of **2,075 band name candidates across 16 genres**, each one run against four sources before it was ever shown to anyone:

| layer | question it answers | how |
|---|---|---|
| `.com` | is the domain still yours to take? | Verisign RDAP |
| Bandcamp handle | is the URL already registered? | `<slug>.bandcamp.com` redirect target |
| SoundCloud handle | is the URL already registered? | `soundcloud.com/<slug>` status |
| same-name artist | does a band already use this name? | Bandcamp site search (Discogs cross-check, Metal Archives when it answers) |

The site that uses this data: **https://bandnamecheck.com**

## What is in this repo

```
data/verified-2026-10-21.csv      2,075 names with every layer's result
data/bc_bands_2026-10-21.json     raw Bandcamp search response per name (dated snapshot)
tools/                            the scripts that produced both
```

### Columns

| column | value | meaning |
|---|---|---|
| `name` | text | the candidate band name |
| `genre` | metal, rock, punk-rock, … | which genre pool it belongs to |
| `com` | `free` / `taken` | RDAP lookup for `<slug>.com` |
| `bandcamp_handle` | `free` / `taken` / `unknown` | `<slug>.bandcamp.com` is unclaimed or not |
| `soundcloud` | `free` / `taken` / `unknown` | `soundcloud.com/<slug>` exists or not |
| `bandcamp_same_name` | integer | artists on Bandcamp whose name matches **exactly** |
| `discogs_same_name` | integer | artists on Discogs whose title matches **exactly** |
| `metal_archives_same_name` | integer | bands on Metal Archives with this exact name (0 when MA was down) |
| `status` | `open` / `taken` | `taken` = same-name artist found **or** Bandcamp handle already registered |

`unknown` is deliberate: it means the source could not be read. It is never written as `free` or `taken`.

## How each check is done

**`.com`** — `GET https://rdap.verisign.com/com/v1/domain/<slug>.com` → `404` = unregistered, `200` = registered.

**Bandcamp handle** — request `https://<slug>.bandcamp.com/` and follow redirects. Final URL `https://bandcamp.com/signup?new_domain=<slug>` = unclaimed; a URL still on `<slug>.bandcamp.com` (store front, album, track) = claimed.

> Do not batch this with `curl --parallel`. Under concurrency Bandcamp serves a bot challenge **on the subdomain**, which looks exactly like a claimed store page. One parallel run marked 1,000+ free handles as taken. Sequential requests, 120 per chunk, with each chunk written to disk, is the only reliable way.

**SoundCloud** — `GET https://soundcloud.com/<slug>` → `200` = taken, `404` = free. A page titled "Something went wrong on SoundCloud" with "We can't find that user" is a free handle.

**Same-name artist (Bandcamp)** — `POST https://bandcamp.com/api/bcsearch_public_api/1/autocomplete_elastic` with:
```json
{"search_text": "<name>", "search_filter": "", "full_page": false, "fan_id": null}
```
Keep only results with `type == "b"` (bands). A hit counts only when

```python
re.sub(r'[^a-z0-9]', '', candidate.lower()) == re.sub(r'[^a-z0-9]', '', result_name.lower())
```

Spaces, punctuation and case are stripped on both sides; anything that merely looks similar is **not** counted. The API also returns genre tags and location, which is where the "who has it" column on the site comes from.

**Discogs** — `GET https://api.discogs.com/database/search?q=<name>&type=artist` (no key needed). Exact title match only.

**Metal Archives** — in-site band search, browser only (the site refuses curl behind Cloudflare). It was down for this entire run (HTTP 521, then "Under maintenance"), so it contributes 0 rows. It is treated as a bonus layer, not a required one.

## What counts as "not checked"

- A source that errors, times out, returns a challenge page, or answers with a non-JSON body ⇒ `unknown`, and the name is **held back**: it is not shown on the site at all.
- A name only reaches the generator when all four controllable layers returned a real answer. Currently 1 of 2,075 names is held back for that reason.

## What this run found

- **2,074 names rollable**, 1,185 free on every layer, 269 already taken, 1 held back.
- **158 names** have an exact same-name artist on Bandcamp; 8 on Discogs; 6 on Metal Archives (from a partial run before it went down).
- **37 of 297 "taken" handle verdicts were wrong — 12.5%.** A random 20 were opened by hand first (19 correct, 1 wrong: `Basalt Lantern` was marked taken but is a signup page), then all 297 were re-opened one by one. Cause: the same bot challenge described above, sneaking past a serial run.
- Ratio thresholds do not catch this. Every batch stayed under the 15% alarm threshold; the errors were scattered. The only thing that caught it was opening individual pages.

## Limits you should know before using this data

- Bandcamp search only knows artists who have a Bandcamp page. A defunct or offline band is invisible. That is why the site says *"no same-name artist on Bandcamp"* and never *"no band with this name exists"*.
- Discogs indexes released music, so a new band with no release is usually absent.
- Domain and handle status changes daily. This file is a dated snapshot, not a live feed.
- `status = open` means the four checked layers are clear. It is not a trademark clearance.

## Re-running it

```bash
python3 tools/genre_pools.py     # build the candidate pools (16 genres)
python3 tools/bc_check.py        # same-name artist search + dated snapshot
python3 tools/quick_check.py     # .com + SoundCloud
python3 tools/bc_handle.py       # Bandcamp handles (sequential, chunked)
python3 tools/discogs_batch.py   # Discogs
python3 tools/recheck_taken.py   # re-open every "taken" handle by hand (browser)
python3 tools/merge.py           # join the four layers into one dataset
```

Every script resumes: it skips names that already have a result, and writes to disk as it goes.

## License

Code: MIT. Data: CC0 — take it, cite `https://bandnamecheck.com` if you can.

Contact: wuzhihun_shen@outlook.com
