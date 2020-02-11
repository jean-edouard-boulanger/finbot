import React, { useEffect, useContext } from "react";
import { Route, Switch } from "react-router-dom";
import { withRouter } from "react-router";
import { toast } from 'react-toastify';

import LinkedAccountContext from "../../context/LinkedAccountContext";
import Schema from "./link-external-account";

const LinkedAccount = props => {

    const linkedAccountContext = useContext(LinkedAccountContext);
    const { _clearErrors, error, accountIsLinked } = linkedAccountContext

    useEffect(() => {
        if (error) {
            toast.error(error, {
                // className: 'foo-bar'
            });
            _clearErrors();
        }
    }, [error])

    useEffect(() => {
        if (accountIsLinked) {
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