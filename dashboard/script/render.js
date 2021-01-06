// makeshift html render function which allows
// the html generation to be in-situ with the surrounding source
export default function (root, args) {
  const renderModule = root.querySelector("script.render");

  if (!renderModule) {
    throw new Error(
      `Could not find <script class="render">...</script> tag in root`
    );
  }

  let __renderFunction;

  const source = renderModule.innerText.replace(
    "export default",
    "__renderFunction = "
  );
  eval(source);

  if (typeof __renderFunction !== "function") {
    throw new Error(
      `Render function did not evaluate to a function: ${source}`
    );
  }

  const html = __renderFunction.apply(this, args);
  const dom = document.createElement("div");
  dom.innerHTML = html;

  for (const child of Array.from(root.childNodes)) {
    if (child !== renderModule) {
      root.removeChild(child);
    }
  }

  for (const child of Array.from(dom.childNodes)) {
    root.appendChild(child);
  }
}
