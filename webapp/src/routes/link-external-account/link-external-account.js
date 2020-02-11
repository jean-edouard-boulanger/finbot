import React, { useContext } from "react";

import Form from "react-jsonschema-form";
import Button from "react-bootstrap/Button";
import ProvidersContext from "../../context/LinkedAccountContext";
import SpinnerButton from "./SpinnerButton";

const LinkExternalAccount = () => {

    const providersContext = useContext(ProvidersContext);
    const { schema, _validateCredentials, _getCurrentProvider, loading } = providersContext

    return (

        schema ?

            loading.current ?

                <SpinnerButton message={loading.message} />

                :

                <>
                    <div className="container w-75">
                        <h4 className="text-center">{_getCurrentProvider().description}</h4>
                        <Form
                            className="border border-dark p-4 rounded text-center opaque-background"
                            schema={schema.json_schema || {}}
                            uiSchema={schema.ui_schema || {}}
                            onSubmit={_validateCredentials}
                            showErrorList={false} >
                            <div>
                                <Button className="bg-dark" type="submit">Authenticate</Button>
                            </div>
                        </Form>
                    </div>
                </>

            :

            null
    )
}

export default LinkExternalAccount;