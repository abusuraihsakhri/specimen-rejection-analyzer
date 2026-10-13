/* Minimal DOM smoke test for the standalone Pages application (Node built-ins only). */
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const html = fs.readFileSync("web/index.html", "utf8");
const match = html.match(/<script>([\s\S]*?)<\/script>/);
assert.ok(match, "inline browser application exists");
assert.ok(!/<script[^>]+src\s*=/i.test(html), "no external JavaScript is needed");
new vm.Script(match[1]);

class Element {
  constructor(tag) {
    this.tag = tag;
    this.children = [];
    this.handlers = {};
    this.style = {};
    this.textContent = "";
    this.value = "";
    this.disabled = false;
    this.className = "";
  }
  addEventListener(name, fn) { this.handlers[name] = fn; }
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this.children = nodes; }
  remove() {}
  click() { if (this.handlers.click) this.handlers.click(); }
}
const elements = new Map();
const doc = {
  getElementById(id) {
    if (!elements.has(id)) elements.set(id, new Element(id));
    return elements.get(id);
  },
  createElement(tag) { return new Element(tag); },
  body: new Element("body"),
};
let downloadCalled = false;
let downloadedBlob = null;
const originalCreateElement = doc.createElement;
doc.createElement = function (tag) {
  const result = originalCreateElement(tag);
  if (tag === "a") result.click = () => { downloadCalled = true; };
  return result;
};
vm.runInNewContext(match[1], {
  document: doc, Blob, URL: {
    createObjectURL(blob) { downloadedBlob = blob; return "blob:fake"; },
    revokeObjectURL() {},
  },
  setTimeout() {},
  console,
});
const el = (id) => doc.getElementById(id);
el("demo").click();
assert.equal(el("total").textContent, "10");
assert.equal(el("rejected").textContent, "6");
assert.equal(el("rate").textContent, "60.0%");
assert.equal(el("categories").textContent, "4");
assert.equal(el("table-body").children.length, 4);
assert.equal(el("table-body").children[0].children[1].textContent, "3");
assert.equal(el("export").disabled, false);
el("export").click();
assert.equal(downloadCalled, true);

el("clear").click();
assert.equal(el("total").textContent, "—");
assert.equal(el("export").disabled, true);

(async () => {
  const fileInput = el("csv-file");
  fileInput.files = [{
    name: "custom.csv", size: 80,
    async text() { return 'reason,status,date\n"Broken, tube",rejected,2026-02-03\n,accepted,2026-02-03'; },
  }];
  await fileInput.handlers.change({target: fileInput});
  assert.equal(el("total").textContent, "2");
  assert.equal(el("rejected").textContent, "1");
  assert.equal(el("rate").textContent, "50.0%");
  assert.equal(el("table-body").children[0].children[0].textContent, "Broken, tube");

  fileInput.files = [{name: "formula.csv", size: 70, async text() { return "reason,status\n=2+2,rejected"; }}];
  await fileInput.handlers.change({target: fileInput});
  el("export").click();
  assert.ok((await downloadedBlob.text()).includes("\"'=2+2\""), "CSV formula neutralized");

  fileInput.files = [{name: "bad.csv", size: 30, async text() { return "unexpected\nvalue"; }}];
  await fileInput.handlers.change({target: fileInput});
  assert.match(el("message").textContent, /Missing reason/);
  assert.equal(el("export").disabled, true);
  console.log("Browser smoke tests passed.");
})().catch((error) => { console.error(error); process.exitCode = 1; });
