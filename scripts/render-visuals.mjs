#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { pathToFileURL } from "node:url";

function usage() {
  return [
    "Usage:",
    "  node scripts/render-visuals.mjs --html <render.html> --out-dir <dir> --visuals <id,id,...> [options]",
    "",
    "Options:",
    "  --width <px>        Viewport width. Default: 1280",
    "  --height <px>       Viewport height. Default: 720",
    "  --param <name>      Query parameter used to select the visual. Default: visual",
    "  --prefix <text>     Prefix for output filenames. Default: empty",
    "  --chrome <path>     Chrome/Chromium executable. Default: $CHROME or common macOS path",
    "",
    "Example:",
    "  node scripts/render-visuals.mjs --html outputs/assets/render.html --out-dir outputs/assets --visuals post-1,post-2",
  ].join("\n");
}

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    const key = argv[i];
    if (!key.startsWith("--")) throw new Error(`Unexpected argument: ${key}`);
    const value = argv[i + 1];
    if (!value || value.startsWith("--")) {
      args[key.slice(2)] = true;
    } else {
      args[key.slice(2)] = value;
      i += 1;
    }
  }
  return args;
}

function requireArg(args, key) {
  const value = args[key];
  if (typeof value !== "string" || value.length === 0) {
    throw new Error(`Missing --${key}`);
  }
  return value;
}

function chromePath(args) {
  if (args.chrome) return args.chrome;
  if (process.env.CHROME) return process.env.CHROME;
  const mac = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
  if (fs.existsSync(mac)) return mac;
  return "google-chrome";
}

function baseUrl(input) {
  if (/^https?:\/\//.test(input) || input.startsWith("file://")) return input;
  return pathToFileURL(path.resolve(input)).href;
}

function withVisualParam(url, param, visual) {
  const target = new URL(url);
  target.searchParams.set(param, visual);
  return target.href;
}

function safeName(value) {
  return String(value).trim().replace(/[^A-Za-z0-9._-]+/g, "-").replace(/^-+|-+$/g, "");
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    console.log(usage());
    return;
  }

  const html = requireArg(args, "html");
  const outDir = path.resolve(requireArg(args, "out-dir"));
  const visuals = requireArg(args, "visuals").split(",").map((v) => v.trim()).filter(Boolean);
  if (!visuals.length) throw new Error("--visuals must include at least one id");

  const width = Number.parseInt(args.width || "1280", 10);
  const height = Number.parseInt(args.height || "720", 10);
  const param = args.param || "visual";
  const prefix = args.prefix || "";
  const chrome = chromePath(args);
  const url = baseUrl(html);

  fs.mkdirSync(outDir, { recursive: true });

  const rendered = [];
  for (const visual of visuals) {
    const output = path.join(outDir, `${prefix}${safeName(visual)}.png`);
    const result = spawnSync(
      chrome,
      [
        "--headless",
        "--disable-gpu",
        "--hide-scrollbars",
        `--window-size=${width},${height}`,
        `--screenshot=${output}`,
        withVisualParam(url, param, visual),
      ],
      { encoding: "utf8" },
    );
    if (result.status !== 0) {
      throw new Error([`Chrome render failed for ${visual}`, result.stdout, result.stderr].filter(Boolean).join("\n"));
    }
    rendered.push({ visual, output });
  }

  console.log(JSON.stringify({ html: path.resolve(html), outDir, width, height, rendered }, null, 2));
}

try {
  main();
} catch (error) {
  console.error(error.stack || error.message || String(error));
  console.error(usage());
  process.exit(1);
}
