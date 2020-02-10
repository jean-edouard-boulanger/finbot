import React, { useEffect, useContext } from "react";
import { Route, Switch } from "react-router-dom";
import { withRouter } from "react-router";
import { toast } from 'react-toastify';

import AlertContext from "../context/alertContext";
import LinkedAccountContext from "../context/LinkedAccountContext";
import Schema from "./Schema";

const LinkedAccount = props => {

    const alertContext = useContext(AlertContext);
    const { setAlert } = alertContext;
    const linkedAccountContext = useContext(LinkedAccountContext);
    const { _clearErrors, error, accountIsLinked } = linkedAccountContext

    useEffect(() => {
        console.log("error for toast has appeared!")
        if (error) {
            toast.configure({
                delay: 1000,
            });
            toast.error(error, {
                // className: 'foo-bar'
            });
            _clearErrors();
        }
    }, [error])

    useEffect(() => {
        console.log("succesful linking!")
        if (accountIsLinked) {
            toast.configure({
                delay: 1000,
            });
            toast.success("Account was linked successfully!", {
            });
            props.history.push("/")
        }
    }, [accountIsLinked])

    return (
        <Switch>
            <Route
                exact
                path="/linked-account/create"
                render={() => (
                    <Schema
                    />
                )}
            />
            {/* <Route  
                exact
                path="/linked-account/:id"
                render={() => (
                    <LinkedExternalAccount
                    />
                )}
            /> */}
        </Switch>
    );
}



export default withRouter(LinkedAccount);