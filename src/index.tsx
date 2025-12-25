if (process.env.NODE_ENV !== "production") {
  require("preact/debug");
}

import { h, render } from "preact";

import "./index.css"; // include before the App component

import App from "./App";

document.addEventListener("DOMContentLoaded", (event) => {
  render(<App />, document.getElementById("root")!);
});
