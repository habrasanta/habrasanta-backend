import { h, FunctionComponent } from "preact";

import "./Loading.css";

const Loading: FunctionComponent = () => (
  <div class="loading">
    <div className="ripple" />
  </div>
);

export default Loading;
