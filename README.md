# Offline portfolio copy

A self-contained copy of andrewtranart.com that works with no internet once it has been opened one time.
The published site lives in `docs/` (GitHub Pages: Settings → Pages → Deploy from a branch → `main` / `/docs`).

## On the iPad
1. Open the Pages link in Safari while online.
2. Share → Add to Home Screen.
3. Open the new icon once while online and wait for the green "Ready offline" pill.
4. It now works in airplane mode, in portrait or landscape.

## Rebuilding after the live site changes
```
cd tools
node crawl.js   <captureDir>     # browse the live site at iPad sizes and record everything
node topup.js   <captureDir>     # full-quality copy of every image for lightboxes
python3 optimize.py <captureDir> # lighter encodes of very large stills
node blocks.js  <captureDir>     # answers for blocks the server renders on demand
node build.js   <captureDir> <videoDir>   # writes docs/
node serve.js & node fill.js <captureDir> # catch anything the copy still asked the internet for, then build again
node test-offline.js <screenshotDir>      # load every page with the network cut
```
`src/sw.js` answers every request from the saved copy; `src/offline.js` saves the site to the device and shows progress.
