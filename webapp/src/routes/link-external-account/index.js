import React, { useEffect, useContext } from "react";
import { Route, Switch } from "react-router-dom";
import { withRouter } from "react-router";
import { toast } from 'react-toastify';

import LinkedAccountContext from "../../context/linked-account-context";
import LinkExternalAccount from "./link-external-account";

const LinkedAccounts = props => {

    const linkedAccountContext = useContext(LinkedAccountContext);
    const { _clearToast, error, accountIsLinked } = linkedAccountContext

    useEffect(() => {
        if (error) {
            toast.error(error, {
                // className: 'foo-bar'
            });
            _clearToast();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [error])

    useEffect(() => {
        if (accountIsLinked) {
            toast.success("Account was linked successfully!", {
            });
            _clearToast();
            props.history.push("/")
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [accountIsLinked])

    return (
        <Switch>
            <Route
                exact
                path="/linked-account/create"
                render={() => (
                    <LinkExternalAccount
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



export default withRouter(LinkedAccounts);
// export default LinkExternalAccount;
