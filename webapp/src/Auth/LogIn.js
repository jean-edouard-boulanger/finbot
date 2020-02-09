import React from "react";

import Form from "react-jsonschema-form";
import Button from "react-bootstrap/Button"


const LogIn = props => {

    const schema = {
        "title": "LOG IN",
        "type": "object",
        "required": [
            "password",
            "email"
        ],
        "properties": {
            "email": {
                "type": "string",
                "title": "E-Mail",
                "format": "email"
            },
            "password": {
                "type": "string",
                "title": "Password",
            }
        }
    }

    const uiSchema = {
        "email": {
            "ui:emptyValue": ""
        },
        "password": {
            "ui:widget": "password",
        }
    }

    const _onSubmit = (e) => {
        props._signIn(e);
    }

    return (
        <div className="container mt-5 w-75">
            <Form
                className="border border-dark p-4 rounded text-center"
                schema={schema}
                uiSchema={uiSchema}
                onSubmit={_onSubmit}
                showErrorList={false} >
                <div>
                    <Button className="bg-dark" type="submit">Log In</Button>
                </div>
            </Form>
        </div>
    )
}

export default LogIn;