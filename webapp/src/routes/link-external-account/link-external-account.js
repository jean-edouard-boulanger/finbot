import React, { useContext } from "react";
import Form from "react-jsonschema-form";
import Button from "react-bootstrap/Button";

import ProvidersContext from "context/linked-account-context";


const LinkExternalAccount = () => {

    const providersContext = useContext(ProvidersContext);
    const { schema, _validateCredentials, _getCurrentProvider } = providersContext

    const log = (type) => console.log.bind(console, type);
    console.log(schema);

    return (
        schema ?
            <>
                <div className="container mt-5 w-75">
                    <h4 className="text-center">{_getCurrentProvider().description}</h4>
                    <Form
                        className="border border-secondary p-4 text-center"
                        schema={schema.json_schema || {}}
                        uiSchema={schema.ui_schema || {}}
                        onError={log("errors")}
                        onSubmit={_validateCredentials}
                        showErrorList={false} >
                        <div>
                            <Button className="bg-dark" type="submit">Link external account</Button>
                        </div>
                    </Form>
                </div>
            </>
            : null
    )
}

export { LinkExternalAccount };
