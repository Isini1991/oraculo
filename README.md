# ORÁCULO — private website concept

## Open
Extract the complete ZIP, then double-click `index.html`. Keep its adjacent files and assets folder together. No install or build is required.

Optional local server: `python -m http.server 8768 --bind 127.0.0.1`
Open http://127.0.0.1:8768/

## Included
- Custom Three.js vinyl sculpture with procedural groove shader, pointer response, scroll response, free mouse-drag front/back rotation, adaptive smaller size centered below the title, standard 33 1/3 RPM LP spin and pause controls.
- Six authentic release covers, searchable catalogue and accessible release dialogs.
- Optional official Bandcamp player loaded only on request; direct official release links.
- Label introduction, Nico Cabañas / Estado de Bienestar feature, six selected artist links, Ombra section, social links and source credits.
- Local fonts, local Three.js, reduced-motion behavior, offscreen rendering pause and static WebGL fallback.

## Verified
Chrome software WebGL: 55 checks passed with no JavaScript console errors. Viewports: 375, 768, 1024 and 1440px. Checked search including accents and empty state, modal content and Escape, menu navigation, animation pause/manual redraw, reduced motion, images, no horizontal document overflow, static fallback and file:// opening.
See verification/FINAL-REPORT.json. Final screenshot files are included separately in the project verification directory. Final automated vision inspection was unavailable; do not treat the artifact as independently visually approved.
Bandcamp embedded audio playback has NOT been verified end-to-end on this network. The external link remains available even when the player is blocked.

## Rights and launch
Private speculative concept by Esi, not an official Oráculo website. Not publicly deployed. Artwork and editorial imagery require rights-holder permission before publication; credits do not confer permission. See assets-manifest.json for original URLs, exact file metadata and hashes. The KEYI article does not identify the portrait photographer.
No fabricated prices, stock claims or upcoming festival dates. No payments, analytics or form submissions.

## Editing
`site.css`: presentation and responsive styles.
`scene.js`: Three.js scene.
`site.js`: search, dialogs, player and navigation.
`build_site.py`: optional source generator; reads assets-manifest.json and rebuilds index.html. Python stdlib only.
`verify_site.py`: Chrome/CDP test runner (requires websocket-client and the local HTTP server).
`licenses/`: Three.js MIT and font SIL OFL notices.

Speed selector: 33 1/3, 45 and 78 RPM; default 33 1/3. Enlarged centered vinyl with limited title overlap permitted.

User-supplied Bandcamp profile image preserved unchanged in The label section. Vinyl overlaps heading by 38px desktop / 18px mobile at initial pose. Mobile controls sit below the record.

Latest revision: flat front-facing initial pose; default 16 2/3 RPM (half LP speed), with standard speed options retained. Focused verification: 11 checks, observed 16.79 RPM.
