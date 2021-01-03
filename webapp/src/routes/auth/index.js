import React, { useEffect, useContext } from "react";
import { Route, Switch } from "react-router-dom";
import { withRouter } from "react-router";
import { toast } from 'react-toastify';

import AuthContext from "../../context/auth/auth-context";
import SignUp from "./signup-form";
import Logout from "./logout";
import LogIn from "./login-form";
// import NotFound from "../NotFound";

const Auth = props => {

    const authContext = useContext(AuthContext);
    const { _register, _login, _logout, _clearErrors, accountID, isAuthenticated, error } = authContext;

    useEffect(() => {
        console.log("accID Changed")
        if (accountID && !isAuthenticated) {
            console.log("use effect someone registered");
            props.history.push("/auth/log-in");
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps,
    }, [accountID])

    useEffect(() => {
        if (isAuthenticated) {
            console.log("use effect someone loggedin succeffsully");
            props.history.push("/");
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps,
    }, [isAuthenticated])

    useEffect(() => {
        if (error) {
            toast.error(error, {
            });
            _clearErrors();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps,
    }, [error])

    function _signIn(data) {
        console.log("in _sign in!", data);
        _login(data.formData)
    }

    function _signUp(data) {
        console.log("in sign up comp");
        _register(data.formData);
    }

    function _exit() {
        _logout();
    }

    return (
        <div>
            <Switch>
                <Route
                    exact
                    path="/auth/sign-up"
                    render={() => (
                        <SignUp
                            error={error}
                            _signUp={_signUp}
                        />
                    )}
                />
                <Route
                    exact
                    path="/auth/log-in"
                    render={() => (
                        <LogIn
                            error={error}
                            _signIn={_signIn}
                        />
                    )}
                />
                <Route
                    exact
                    path="/auth/logout"
                    render={() => (<Logout _exit={_exit} />)}
                />
                {/* <Route component={NotFound} /> */}
            </Switch>
        </div>
    );
}



export default withRouter(Auth);