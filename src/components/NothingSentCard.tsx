import { h, FunctionComponent } from "preact";

import nothingSent from "../images/nothing_sent.png";

const NothingSentCard: FunctionComponent = () => (
  <div className="card-front card-nothing-sent">
    <img src={nothingSent} />
    Вам пока ничего<br />не отправили
  </div>
);

export default NothingSentCard;
