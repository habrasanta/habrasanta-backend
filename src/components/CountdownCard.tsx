import { h, Fragment, FunctionComponent } from "preact";

import Plural from "./Plural";
import Milestone from "./Milestone";

import anonymous from "../images/anonymous.png";

const CountdownCard: FunctionComponent<{
  timeleft: number;
  matched: boolean;
  signupsEnd: string;
}> = props => (
  <div className="card-front card-waiting">
    <img src={anonymous} alt="Аноним"/>
    {props.timeleft ? (
      <Fragment>
        <h3>
          {props.timeleft} <Plural n={props.timeleft} one="день" few="дня" many="дней" /> до старта
        </h3>
        <p>
          <Milestone date={props.signupsEnd} /> будет проведена
          жеребьевка адресов, где каждому участнику будет назначен свой
          получатель.
        </p>
      </Fragment>
    ) : props.matched ? (
      <Fragment>
        <h3>
          Адреса уже розданы
        </h3>
        <p>
          Подписывайтесь на обновления <a href="https://habr.com/users/clubadm/" target="_blank">@clubadm</a>,
          чтобы не&nbsp;пропустить регистрацию на&nbsp;следующий год.
        </p>
      </Fragment>
    ) : (
      <Fragment>
        <h3>
          Адреса скоро будут розданы
        </h3>
        <p>
          Это произойдет автоматически, нужно только немножко подождать.
        </p>
      </Fragment>
    )}
  </div>
);

export default CountdownCard;
