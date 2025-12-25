import { h, FunctionComponent } from "preact";

const months = [
  "января",
  "февраля",
  "марта",
  "апреля",
  "мая",
  "июня",
  "июля",
  "августа",
  "сентября",
  "октября",
  "ноября",
  "декабря",
];

const DateTime: FunctionComponent<{
  date: string;
}> = ({ date }) => {
  const d = new Date(date);
  return (
    <time>{d.getDate()} {months[d.getMonth()]} {d.getFullYear()} в {d.getHours()}:{String(d.getMinutes()).padStart(2, "0")}</time>
  );
};

export default DateTime;
