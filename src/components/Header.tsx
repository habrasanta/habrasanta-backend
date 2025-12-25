import { h, FunctionComponent } from "preact";

import Logo from "./Logo";
import Milestone from "./Milestone";
import Plural from "./Plural";

import "./Header.css";

const Header: FunctionComponent<{
  year: number;
  memberCount: number;
  shippedCount: number;
  deliveredCount: number;
  signupsStart: string;
  signupsEnd: string;
  shipBy: string;
  debug: boolean;
}> = props => (
  <header className="header" role="banner">
    <Logo className="header-logo" year={props.year} debug={props.debug} />
    <div className="header-inner">
      <ul className="counters header-counters">
        <li>
          <b>{props.memberCount}</b>
          <Plural n={props.memberCount} one="участник" few="участника" many="участников" />
        </li>
        <li>
          <b>{props.shippedCount}</b>
          <Plural n={props.shippedCount} one="отправил" few="отправили" many="отправили" />
        </li>
        <li>
          <b>{props.deliveredCount}</b>
          <Plural n={props.deliveredCount} one="получил" few="получили" many="получили" />
        </li>
      </ul>
      <ul className="usercontrols header-usercontrols">
        <li className="usercontrols-item usercontrols-source">
          <a target="_blank" href="https://github.com/habrasanta" title="Исходный код"></a>
        </li>
        <li className="usercontrols-item usercontrols-help">
          <a target="_blank" href="https://ru.wikipedia.org/wiki/Тайный_Санта" title="Помощь"></a>
        </li>
        <li className="usercontrols-item usercontrols-logout">
          <a href={"/backend/logout?next=%2F" + props.year + "%2F"} title="Выйти"></a>
        </li>
      </ul>
      <ul className="timetable header-timetable">
        <li>
          <b><Milestone date={props.signupsStart} /></b>
          Открытие сезона
        </li>
        <li>
          <b><Milestone date={props.signupsEnd} /></b>
          Жеребьевка адресов
        </li>
        <li>
          <b><Milestone date={props.shipBy} /></b>
          Закрытие сезона
        </li>
      </ul>
    </div>
  </header>
);

export default Header;
