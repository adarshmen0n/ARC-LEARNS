// Copies the static frontend into www/ so Capacitor can bundle it into the APK.
const fs = require("fs");
const path = require("path");

const src = path.resolve(__dirname, "../../frontend");
const dest = path.resolve(__dirname, "../www");

fs.rmSync(dest, { recursive: true, force: true });
fs.cpSync(src, dest, { recursive: true });
console.log(`Copied ${src} -> ${dest}`);
