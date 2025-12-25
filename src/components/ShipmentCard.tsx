import { h, FunctionComponent } from "preact";
import { useState } from "preact/hooks";

import { Country } from "../models";

import PostageStamp from "./PostageStamp";
import Button from "./Button";

const ShipmentCard: FunctionComponent<{
  year: number;
  fullName: string;
  postcode: string;
  address: string;
  country: string;
  isOverdue: boolean;
  countries: Country[];
  onSubmit: () => void;
}> = props => {
  const [checked, setChecked] = useState(false);

  return (
    <div className="card-front card-decorated shipping">
      <label for="fullname">Кому</label>
      <input
        id="fullname"
        type="text"
        disabled
        value={props.fullName}
      />
      <PostageStamp year={props.year} />
      <label for="postcode">Куда</label>
      <input
        id="postcode"
        type="text"
        disabled
        value={props.postcode}
      />
      <textarea
        id="address"
        disabled
        value={props.address}
      />
      <select
        id="country"
        value={props.country}
        disabled
      >
        <option disabled value="select">Не указана</option>
        {props.countries.map(country => (
          <option key={country.code} value={country.code} selected={country.code === props.country}>
            {country.name}
          </option>
        ))}
      </select>
      {props.isOverdue ? (
        <div className="card-closed">
          Вы так и не отправили подарок вовремя :-(
        </div>
      ) : (
        <div className="shipping-confirmation">
          <Button className="shipping-button" disabled={!checked} onClick={props.onSubmit}>
            Далее
          </Button>
          <input type="checkbox" checked={checked} />
          <label onClick={() => setChecked(prevState => !prevState)}>Я отправил подарок</label>
        </div>
      )}
    </div>
  );
};

export default ShipmentCard;
