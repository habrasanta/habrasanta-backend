import { h, FunctionComponent } from "preact";
import clsx from "clsx";
import { useEffect, useMemo, useState } from "preact/hooks";

import { AddressForm, AddressFormError, Country, Participation } from "../models";

import PostageStamp from "./PostageStamp";
import Button from "./Button";
import Milestone from "./Milestone";

import "./EnrollmentCard.css";

const EnrollmentCard: FunctionComponent<{
  year: number;
  signupsEnd: string;
  canParticipate: boolean;
  isParticipatable: boolean;
  participation?: Participation;
  addressFormError: AddressFormError;
  countries: Country[];
  onEnroll: (form: AddressForm) => void;
  onUnenroll: () => void;
}> = props => {
  const [addressForm, setAddressForm] = useState<AddressForm>({
    fullname: "",
    postcode: "",
    address: "",
    country: "",
  });

  useEffect(() => {
    if (props.participation) {
      setAddressForm({
        fullname: props.participation.fullname,
        postcode: props.participation.postcode,
        address: props.participation.address,
        country: props.participation.country || '',
      });
    }
  }, [props.participation]);

  const onAddressForm = (e: Event) => {
    const input = e.target as HTMLInputElement;
    setAddressForm(form => ({
      ...form,
      [input.id]: input.value,
    }));
  };

  const formDisabled = useMemo(() => {
    return !!Object.values(addressForm).some(v => !v);
  }, [addressForm]);

  return (
    <div className={clsx("card-front", "card-address", { "card-decorated": props.participation })}>
      <form noValidate>
        <label for="fullname">Кому</label>
        <input
          id="fullname"
          className={clsx({ "error": props.addressFormError.fullname })}
          type="text"
          name="fullName"
          value={addressForm.fullname}
          onInput={onAddressForm}
          placeholder="Полное имя"
          disabled={!!props.participation}
        />
        <PostageStamp year={props.year} />
        <label for="postcode">Куда</label>
        <input
          id="postcode"
          className={clsx({ "error": props.addressFormError.postcode })}
          type="text"
          name="postCode"
          value={addressForm.postcode}
          onInput={onAddressForm}
          placeholder="Индекс"
          disabled={!!props.participation}
        />
        <textarea
          id="address"
          className={clsx({ "error": props.addressFormError.address })}
          name="address"
          value={addressForm.address}
          onInput={onAddressForm}
          placeholder="Адрес"
          disabled={!!props.participation}
        />
        <select
          id="country"
          value={addressForm.country}
          onChange={onAddressForm}
          disabled={!!props.participation}
        >
          <option disabled value=''>Страна</option>
          {props.countries.map(country => (
            <option key={country.code} value={country.code}>
              {country.name}
            </option>
          ))}
        </select>
      </form>
      {props.participation ? (
        <Button className="card-button" primary onClick={props.onUnenroll} disabled={!props.isParticipatable}>
          Я передумал участвовать
        </Button>
      ) : props.isParticipatable ? props.canParticipate ? (
        <Button disabled={formDisabled} className="card-button" primary onClick={() => props.onEnroll(addressForm)}>
          Зарегистрировать участника
        </Button>
      ) : (
        <div className="card-closed card-banned">
          Нужен <a href="https://habr.com/ru/docs/help/registration/#standard" target="_blank">полноправный аккаунт</a> с кармой от +7
        </div>
      ) : (
        <div className="card-closed">
          Регистрация закрыта <Milestone date={props.signupsEnd} />.
        </div>
      )}
    </div>
  );
};

export default EnrollmentCard;
