import { h, FunctionComponent } from "preact";

const BannedCard: FunctionComponent<{
  username: string;
}> = props => (
  <div className="card-front card-banned">
    <p>
      Привет, {props.username}. В&nbsp;прошлом году твой получатель
      не&nbsp;нажал кнопку подтверждения получения подарка. Скорее
      всего, он просто забыл об&nbsp;этом, но нам хотелось&nbsp;бы это
      выяснить. Напиши, пожалуйста, в&nbsp;ЛС
      хабрапользователю <a target="_blank" href="https://habr.com/users/negasus/">@negasus</a> о&nbsp;том,
      что ты сейчас прочитал, и&nbsp;мы попробуем вместе
      разобраться. После этого ты сможешь заполнить свои данные
      и&nbsp;участвовать в&nbsp;ХабраАДМ.
    </p>
    <p>
      Извини, что так все сложно, но&nbsp;нам хочется, чтобы все было
      хорошо и&nbsp;правильно.
    </p>
    <p>
      С&nbsp;наступающим!
    </p>
  </div>
);

export default BannedCard;
