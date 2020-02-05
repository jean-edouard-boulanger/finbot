import React, { useState } from "react";
import FinbotClient from "../FinbotClient/FinbotClient"
import { Route, Switch } from "react-router-dom";
import { withRouter } from "react-router";

import SignUp from "./SignUp";
import Logout from "./Logout";
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

    async function _sign(type, data) {
        let finbot_client = new FinbotClient();
        console.log("in _sign!", type, data)
        const { email, full_name, settings, password } = data.formData;
        setError({
            error: ""
        });
        try {
            const res = await finbot_client.registerAccount({ email, password, full_name, settings });
            console.log("RESPONSE REGISTER", res)
            await localStorage.setItem("identity", "fehjd7483.furucbc883DUDH5.jnidcMf38d");
            props.setUser();
            console.log("after props set user")
            props.history.push("/");
        } catch (error) {
            console.log({ error })
            // setError({error: error.description})
        }
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
            <Route
                exact
                path="/auth/logout"
                render={() => <Logout resetUser={props.resetUser} />}
            />
            {/* <Route component={NotFound} /> */}
        </Switch>
    );
}



export default withRouter(Auth);