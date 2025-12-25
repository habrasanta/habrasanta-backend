import { FunctionComponent } from "preact";
import { route } from "preact-router";
import { useEffect } from "preact/hooks";

import { Season } from "../models";
import { useUser } from "../contexts/UserContext";

const Home: FunctionComponent = () => {
  const user = useUser();

  useEffect(() => {
    fetch("/api/v1/seasons/latest")
      .then(res => res.ok ? res.json() : Promise.reject(res))
      .then((data: Season) => route("/" + data.id + (user.is_authenticated ? "/profile/" : "/"), true))
      .catch(res => res.json().then(err => alert(err.detail)));
  }, []);

  return null;
};

export default Home;