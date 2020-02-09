import React from "react";
import Form from "react-jsonschema-form";
import Button from "react-bootstrap/Button"


const LoginForm = () => {

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

    const log = (type) => console.log.bind(console, type);

    return (
        <div className="container mt-5 w-75">
            <Form
                className="border border-secondary p-4 text-center"
                schema={schema}
                uiSchema={uiSchema}
                onError={log("errors")}
                showErrorList={false} >
                <div>
                    <Button className="bg-dark" type="submit">Log In</Button>
                </div>
            </Form>
        </div>
    )
}


export default LoginForm;
