import { h, FunctionComponent } from "preact";

import giftSent from "../images/gift_sent.png";

const GiftSentCard: FunctionComponent = () => (
  <div className="card-front card-gift-sent">
    <img src={giftSent} alt="Подарок в пути"/>
    <h3>Вы отправили подарок</h3>
    <p>
      Осталось дождаться пока получатель подтвердит получение подарка.
    </p>
  </div>
);

export default GiftSentCard;
