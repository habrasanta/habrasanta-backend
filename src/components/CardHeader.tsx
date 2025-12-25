import { h, FunctionComponent } from "preact";

import ChatButton from "./ChatButton";

const CardHeader: FunctionComponent<{
  showChatButton: boolean;
  unreadMessageCount: number;
  onChatButton: () => void;
}> = props => (
  <header className="card-heading">
    {props.showChatButton && (
      <ChatButton unreadCount={props.unreadMessageCount} onClick={props.onChatButton} />
    )}
    <h3 className="card-title">{props.children}</h3>
  </header>
);

export default CardHeader;
