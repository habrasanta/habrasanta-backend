import { h, FunctionComponent } from "preact";
import clsx from "clsx";

import "./Button.css";

const Button: FunctionComponent<{
  href?: string;
  disabled?: boolean;
  primary?: boolean;
  className?: string;
  onClick?: () => void;
}> = props => h(props.href ? "a" : "button", {
  className: clsx("button", { "button-primary": props.primary }, props.className),
  disabled: props.disabled,
  href: props.href,
  onClick: props.onClick,
}, props.children);

export default Button;
