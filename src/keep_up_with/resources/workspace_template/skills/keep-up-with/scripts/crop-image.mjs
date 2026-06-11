#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import path from "node:path";

function usage() {
  return [
    "Usage:",
    "  node scripts/crop-image.mjs --in <input.png> --out <output.png> --box <x,y,w,h>",
    "",
    "Box values can be normalized decimals or raw pixels:",
    "  --box 0.189,0.339,0.671,0.444",
    "  --box 415,825,1470,1080",
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
  if (typeof value !== "string" || !value) throw new Error(`Missing --${key}`);
  return value;
}

function imageSize(input) {
  const result = spawnSync("sips", ["-g", "pixelWidth", "-g", "pixelHeight", input], { encoding: "utf8" });
  if (result.status !== 0) {
    throw new Error([`sips could not read image dimensions: ${input}`, result.stdout, result.stderr].filter(Boolean).join("\n"));
  }
  const width = Number.parseInt(result.stdout.match(/pixelWidth:\s*(\d+)/)?.[1] || "", 10);
  const height = Number.parseInt(result.stdout.match(/pixelHeight:\s*(\d+)/)?.[1] || "", 10);
  if (!Number.isFinite(width) || !Number.isFinite(height)) {
    throw new Error(`Could not parse image dimensions from sips output:\n${result.stdout}`);
  }
  return { width, height };
}

function parseBox(value, size) {
  const parts = value.split(",").map((part) => Number.parseFloat(part.trim()));
  if (parts.length !== 4 || parts.some((part) => !Number.isFinite(part))) {
    throw new Error("--box must be x,y,w,h");
  }
  const normalized = parts.every((part) => part >= 0 && part <= 1);
  const [x, y, w, h] = normalized
    ? [
        Math.round(parts[0] * size.width),
        Math.round(parts[1] * size.height),
        Math.round(parts[2] * size.width),
        Math.round(parts[3] * size.height),
      ]
    : parts.map((part) => Math.round(part));
  return { x, y, w, h, normalized };
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    console.log(usage());
    return;
  }
  const input = path.resolve(requireArg(args, "in"));
  const output = path.resolve(requireArg(args, "out"));
  const size = imageSize(input);
  const box = parseBox(requireArg(args, "box"), size);

  const result = spawnSync(
    "sips",
    ["-c", String(box.h), String(box.w), "--cropOffset", String(box.y), String(box.x), input, "--out", output],
    { encoding: "utf8" },
  );
  if (result.status !== 0) {
    throw new Error([`sips crop failed: ${input}`, result.stdout, result.stderr].filter(Boolean).join("\n"));
  }
  console.log(JSON.stringify({ input, output, image: size, crop: box }, null, 2));
}

try {
  main();
} catch (error) {
  console.error(error.stack || error.message || String(error));
  console.error(usage());
  process.exit(1);
}
