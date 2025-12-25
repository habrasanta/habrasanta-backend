import { h, FunctionComponent } from "preact";
import clsx from "clsx";

import bug from "../images/bug.png";

import "./Logo.css";

const Logo: FunctionComponent<{
  year: number;
  debug: boolean;
  className?: string;
}> = props => (
  <div className={clsx("logo", props.className)}>
    <h1>АДМ {props.year}</h1>
    <h2>на Хабре</h2>
    {props.debug && (
      <img className="bug" src={bug} />
    )}
  </div>
);

export default Logo;
