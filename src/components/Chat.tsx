import { h, FunctionComponent, createRef } from "preact";
import { useEffect, useState } from "preact/hooks";
import clsx from "clsx";

import { Mail } from "../models";

import DateTime from "./DateTime";

import "./Chat.css";

const Chat: FunctionComponent<{
  mails: Mail[];
  isClosed: boolean;
  closedAt: string;
  onSubmit: (text: string) => void;
}> = props => {
  const [text, setText] = useState("");
  const scrollEnd = createRef();

  useEffect(() => {
    scrollEnd.current?.scrollIntoView();
  }, [props.mails]);

  return (
    <div className="card-back chat">
      <div className="chat-view" scroll-glue>
        {props.mails.map(msg => (
          <div key={msg.id} className={clsx("chat-message", { "is-author": msg.is_author })}>
            <p>{msg.text}</p>
            {(!msg.is_author || !msg.read_date) ? (
              <span>Отправлено <DateTime date={msg.send_date} /></span>
            ) : (
              <span>Прочитано <DateTime date={msg.read_date} /></span>
            )}
          </div>
        ))}
        <div ref={scrollEnd}/>
      </div>
      {props.isClosed ? (
        <div className="card-closed">
          Чатик закрыт <DateTime date={props.closedAt} />.
        </div>
      ) : (
        <form onSubmit={(e: Event) => {
          e.preventDefault();
          if (text.length > 0) {
            props.onSubmit(text);
            setText("");
          }
        }}
          className="chat-form"
        >
          <input
            className="chat-input"
            type="text"
            autocomplete="off"
            placeholder="Ваше сообщение..."
            value={text}
            onInput={(e: Event) => setText((e.target as HTMLInputElement).value)}
          />
          <button type="submit" className="chat-submit" />
        </form>
      )}
    </div>
  );
};

export default Chat;
