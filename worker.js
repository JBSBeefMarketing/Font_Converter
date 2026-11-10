// Runs Python (Pyodide + fontTools) off the main thread so the page stays responsive.
importScripts("https://cdn.jsdelivr.net/pyodide/v0.27.2/full/pyodide.js");

const ready = (async () => {
  const py = await loadPyodide();
  postMessage({ type: "loaded", stage: 0.5 });
  await py.loadPackage("fonttools");
  py.FS.writeFile("convert.py", await (await fetch("convert.py")).text());
  py.runPython("import convert");
  postMessage({ type: "loaded", stage: 1 });
  return py.globals.get("convert");
})();
ready.catch(e => postMessage({ type: "error", message: "Couldn't load the converter. Check your internet connection and refresh." }));

function cleanError(e) {
  // Show just the final Python error line, not the traceback.
  return String(e.message).trim().split("\n").pop().replace(/^[\w.]+Error: /, "");
}

onmessage = async ({ data: { files } }) => {
  const convert = await ready;
  const names = [], outputs = [];
  for (let i = 0; i < files.length; i++) {
    const { name, data } = files[i];
    const report = frac => postMessage({ type: "progress", value: (i + frac) / files.length, label: name });
    report(0);
    try {
      const result = convert.convert_bytes(data, report);
      outputs.push(result.toJs());
      result.destroy();
      names.push(name.replace(/\.otf$/i, "") + ".ttf");
    } catch (e) {
      postMessage({ type: "error", message: `${name}: ${cleanError(e)}` });
      return;
    }
  }
  if (outputs.length === 1) {
    postMessage({ type: "done", name: names[0], bytes: outputs[0], mime: "font/ttf" });
  } else {
    const zip = convert.zip_files(names, outputs);
    postMessage({ type: "done", name: "converted-fonts.zip", bytes: zip.toJs(), mime: "application/zip" });
    zip.destroy();
  }
};
