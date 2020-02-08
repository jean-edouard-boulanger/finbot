import React, { useContext } from "react";

import Form from "react-jsonschema-form";
import Button from "react-bootstrap/Button";
import ProvidersContext from "../context/LinkedAccountContext";

const Schema = () => {

    const providersContext = useContext(ProvidersContext);
    const { schema, _validateCredentials } = providersContext

    const log = (type) => console.log.bind(console, type);

    return (

        schema ?
            <>
                <div className="container mt-5 w-75">
                    <Form
                        className="border border-dark p-4 rounded text-center"
                        schema={schema}
                        onError={log("errors")}
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

export default Schema;