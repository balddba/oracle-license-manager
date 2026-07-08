import { readFileSync } from "node:fs";
import { createCanvas } from "canvas";
import * as echarts from "echarts";

const payload = JSON.parse(readFileSync(0, "utf8"));
const { width, height, option } = payload;

const canvas = createCanvas(width, height);
const chart = echarts.init(canvas, null, {
  renderer: "canvas",
  width,
  height,
});

chart.setOption(option);
process.stdout.write(canvas.toBuffer("image/png"));
chart.dispose();
