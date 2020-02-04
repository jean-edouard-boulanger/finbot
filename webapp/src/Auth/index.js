import React, { useState } from "react";
import FinbotClient from "../FinbotClient/FinbotClient"
import { Route, Switch } from "react-router-dom";
import { withRouter } from "react-router";

import SignUp from "./SignUp";
// import Logout from "./Logout";
import LogIn from "./LogIn";
// import NotFound from "../NotFound";

const Auth = props => {

    const [credentials, setCredentials] = useState({
        email: "",
        password: "",
        settings: "",
        full_name: "",
    })

    const [error, setError] = useState({
        error: ""
    })

    const { email, password } = credentials;

    function _sign(type, data) {
        setError({
            error: ""
        });
        // try {
        //     // const account_data = await finbot_client.getAccount({ account_id: this.account_id });
        //     // localStorage.setItem("identity", data.token);
        //     // props.setUser();
        //     // props.history.push("/");
        // } catch (error) {
        //     // setError({error: error.description})
        // }
    }

    return (
        <Switch>
            <Route
                exact
                path="/auth/sign-up"
                render={() => (
                    <SignUp
                        email={email}
                        password={password}
                        error={error}
                        _sign={_sign}
                    />
                )}
            />
            <Route
                exact
                path="/auth/log-in"
                render={() => (
                    <LogIn
                        email={email}
                        password={password}
                        error={error}
                        _sign={_sign}
                    />
                )}
            />
            {/* <Route
          exact
          path="/auth/logout"
          render={() => <Logout resetUser={props.resetUser} />}
        /> */}
            {/* <Route component={NotFound} /> */}
        </Switch>
    );
}



export default withRouter(Auth);