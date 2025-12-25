import { h, Fragment, FunctionComponent } from "preact";

const Plural: FunctionComponent<{
  n: number;
  one: string;
  few: string;
  many: string;
}> = ({ n, one, few, many }) => (
  <Fragment>{n % 10 == 1 && n % 100 != 11 ? one : (n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 10 || n % 100 >= 20) ? few : many)}</Fragment>
);

export default Plural;
