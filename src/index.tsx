if (import.meta.env.DEV) {
  import("preact/debug");
}

import { h, render } from "preact";

import "./index.css"; // include before the App component

import App from "./App";

// Used by the frontend.html frontend template.
import "./images/apple-touch-icon.png?no-inline";
import "./images/favicon-16x16.png?no-inline";
import "./images/favicon-32x32.png?no-inline";
import "./images/social.jpg?no-inline";

document.addEventListener("DOMContentLoaded", (event) => {
  render(<App />, document.getElementById("root")!);
});
