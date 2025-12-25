import { h, FunctionComponent } from "preact";

const PostageStamp: FunctionComponent<{
  year: number;
}> = props => (
  <div className="card-stamp">{props.year}</div>
);

export default PostageStamp;
