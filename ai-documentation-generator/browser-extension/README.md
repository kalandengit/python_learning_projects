# Browser Extension MVP (Sprint 13)

Manifest V3 Chrome/Edge extension for visible-tab, region, and experimental segmented full-page capture.

## Setup
1. In the web app, apply migration `013_sprint13_browser_extension.sql`.
2. Open **Settings → Browser extension access**, generate a token, and copy it.
3. `cd browser-extension && npm install && npm run build`.
4. Open `chrome://extensions`, enable Developer mode, choose **Load unpacked**, and select `browser-extension/dist`.
5. Paste the web app URL and token into the popup.

## Security
Tokens are random 256-bit bearer credentials; only SHA-256 hashes are stored. Tokens are workspace/user scoped, revocable, and limited to capture, project-read, and job-read scopes. Never place a service-role key in the extension.

## Known limitations
Full-page capture scrolls and stitches viewport images. Sticky elements, lazy-loaded areas, browser internal pages, and pages that block scripting may produce imperfect output. Visible-tab and region capture are the recommended beta modes.
