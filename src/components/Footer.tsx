import { h, FunctionComponent } from "preact";

import "./Footer.css";

const Footer: FunctionComponent = () => (
  <footer className="footer" role="contentinfo">
    <a className="footer-designer" href="https://novosylov.livejournal.com/">
      Валя Новоселов<br/>дизайнер
    </a>
    <div className="footer-feedback">
      В любой непонятной ситуации пишите<br/>
      <a href="https://habr.com/ru/users/Boomburum/">Boomburum</a> (на Хабре или в Telegram)
    </div>
  </footer>
);

export default Footer;
