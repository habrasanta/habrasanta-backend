import { h, FunctionComponent } from "preact";

const ChatButton: FunctionComponent<{
  unreadCount: number;
  onClick: () => void;
}> = props => (
  <button className="card-flipper" title="Показать/спрятать чатик" onClick={props.onClick}>
  {props.unreadCount > 0 && (
    <div className="chat-counter">
      {props.unreadCount}
    </div>
  )}
  </button>
);

export default ChatButton;
