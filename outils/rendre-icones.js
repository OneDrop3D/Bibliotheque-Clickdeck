// Lancé par prusaslicer.py avec Electron : rastérise des SVG en PNG 96×96.
// Un PNG garde ses couleurs partout : l'application inverse les SVG en thème
// sombre, et le boîtier ignore la couleur de fond d'une touche.
const { app, BrowserWindow } = require('electron');
const fs = require('fs');
const path = require('path');

app.disableHardwareAcceleration();
app.whenReady().then(async () => {
  const [liste, dossier] = process.argv.slice(-2);
  const icones = JSON.parse(fs.readFileSync(liste, 'utf8'));
  const fenetre = new BrowserWindow({ show: false, webPreferences: { offscreen: true } });
  await fenetre.loadURL('about:blank');
  for (const [nom, svg] of Object.entries(icones)) {
    const png = await fenetre.webContents.executeJavaScript(`new Promise((ok, ko) => {
      const image = new Image();
      image.onload = () => {
        const toile = document.createElement('canvas');
        toile.width = toile.height = 96;
        toile.getContext('2d').drawImage(image, 0, 0, 96, 96);
        ok(toile.toDataURL('image/png').split(',')[1]);
      };
      image.onerror = () => ko(new Error('SVG illisible'));
      image.src = 'data:image/svg+xml;base64,' + ${JSON.stringify(Buffer.from(svg).toString('base64'))};
    })`);
    fs.writeFileSync(path.join(dossier, `${nom}.png`), Buffer.from(png, 'base64'));
  }
  app.quit();
});
