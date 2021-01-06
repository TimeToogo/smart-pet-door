import render from "./render.js";

export default class Modal {
  static root() {
    return document.querySelector(".modal");
  }

  static init(cfg) {
    console.log("init modal...");
    const root = Modal.root();

    root.querySelector(".close").addEventListener("click", Modal.close);
  }

  static show(cfg, event) {
    console.log("show modal...");

    const root = Modal.root();
    render(root.querySelector(".body"), [event]);
    root.classList.add("active");
  }

  static close() {
    console.log("hide modal...");

    const root = Modal.root();
    root.classList.remove("active");
  }
}
