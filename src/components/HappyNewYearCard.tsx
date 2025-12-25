import { h, FunctionComponent } from "preact";

const HappyNewYearCard: FunctionComponent<{
  galleryUrl?: string;
}> = props => (
  <div className="card-front card-happy">
    <h3>С Новым Годом!</h3>
    {props.galleryUrl && (
      <p>
        Расскажите всем о своём подарке в <a target="_blank" href={props.galleryUrl}>посте хвастовства</a>
      </p>
    )}
  </div>
);

export default HappyNewYearCard;
