import { h, FunctionComponent } from "preact";
import { useState } from "preact/hooks";

import Button from "./Button";

import giftSent2 from "../images/gift_sent2.png";

import "./WaitingCard.css";

const WaitingCard: FunctionComponent<{
  isClosed: boolean;
  onSubmit: () => void;
}> = props => {
  const [checked, setChecked] = useState(false);

  return (
    <div className="card-front receiving" ng-if="member.santa.is_gift_sent && !member.is_gift_received">
      <img src={giftSent2} alt="Подарок в пути"/>
      <h3>Вам отправили подарок</h3>
      <p>
        Наберись терпения и не&nbsp;забывай проверять почту, твой подарок уже в&nbsp;пути.
      </p>
      {!props.isClosed && (
        <div className="receiving-confirmation">
          <Button className="receiving-button" disabled={!checked} onClick={props.onSubmit}>
            Далее
          </Button>
          <input type="checkbox" checked={checked} />
          <label onClick={() => setChecked(prevState => !prevState)}>Я получил подарок</label>
        </div>
      )}
    </div>
  );
};

export default WaitingCard;
