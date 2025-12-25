import { h, FunctionComponent, Fragment } from "preact";
import { useEffect, useState } from "preact/hooks";
import { route } from "preact-router";

import { User, Season } from "../models";

import Logo from "../components/Logo";
import Footer from "../components/Footer";
import Button from "../components/Button";

import "./Landing.css";
import { useUser } from "../contexts/UserContext";

const Landing: FunctionComponent<{
  year: string;
}> = props => {
  const user = useUser();
  const [season] = useState<Season>(JSON.parse(document.getElementById("season").textContent));

  if (user.is_authenticated) {
    route("/" + props.year + "/profile/", true);
    return null;
  }

  const loginUrl = "/backend/login?next=%2F" + props.year + "%2Fprofile%2F";

  return season ? (
    <Fragment>
      {season.is_closed && (
        <div className="alert">
          Внимание! АДМ-{season.id} уже завершен, вы смотрите архивную версию!
        </div>
      )}
      <header className="banner" role="banner">
        <div className="banner-inner">
          <div className="members banner-members">
            участников<br/>{ season.member_count }
          </div>
          <div className="banner-logo">
          <Logo year={season.id} debug={user.is_debug} />
          </div>
          <h3 className="banner-welcome">
            Рады видеть тебя в нашем клубе Анонимных Дедов Морозов
          </h3>
          <Button className="banner-button" primary href={loginUrl}>
            Войти через Хабр
          </Button>
        </div>
      </header>
      <main className="promo" role="main">
        <h4 className="promo-welcome">О клубе</h4>
        <ul className="promo-list">
          <li className="feature feature-description promo-feature">
            <div class="feature-content">
              <h5>Итак, что же это такое?</h5>
              <p>
                Хабраюзер регистрируется на&nbsp;нашем сайте в&nbsp;качестве участника
                акции, заполняет форму со&nbsp;своим адресом и&nbsp;ФИО, куда будет
                присылаться подарок. После окончания регистрации адреса случайным
                образом распределяются между участниками, и&nbsp;наступает время
                отправки подарков.
              </p>
            </div>
          </li>
          <li className="feature feature-anonymity promo-feature">
            <div class="feature-content">
              <h5>Анонимность</h5>
              <p>
                Например, вам пришло сообщение, что вам необходимо отправить подарок
                Иванову Ивану по&nbsp;адресу: РФ, 101000, г.&nbsp;Москва,
                3-я&nbsp;улица строителей, 25/12. Вы понятия не&nbsp;имеете, что за
                хабраюзер скрывается под этими данными. Точно так же ваш адрес попадет
                кому-то другому. Все здорово и&nbsp;анонимно.
              </p>
            </div>
          </li>
          <li className="feature feature-gift promo-feature">
            <div class="feature-content">
              <h5>Что посылать?</h5>
              <p>
                Это, разумеется, на&nbsp;ваше усмотрение. Никаких ограничений тут нет.
                Просто при выборе подарка, прикиньте &mdash; хотелось бы вам получить
                что-то подобное?
              </p>
            </div>
          </li>
        </ul>
        <Button className="promo-button" primary href={loginUrl}>
          Войти через Хабр
        </Button>
      </main>
      <Footer />
    </Fragment>
  ) : null;
};

export default Landing;
