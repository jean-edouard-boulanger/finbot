import React from "react";
import PropTypes from "prop-types";
import Form from "react-jsonschema-form";
import Button from "react-bootstrap/Button";

const LoginForm = props => {

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
            "ui:emptyValue": "",
            "ui:autofocus": true,
        },
        "password": {
            "ui:widget": "password",
        }
    }

    const _onSubmit = (e) => {
        props._signIn(e);
    }

    return (
        <div style={{ height: "100%", display: "flex", justifyContent: "center", alignItems: "center", padding: "115px 25px 455px" }}>
            <Form
                className="border border-secondary p-4 text-center opaque-background sign-form"
                schema={schema}
                uiSchema={uiSchema}
                onSubmit={_onSubmit}
                showErrorList={false} >
                <div>
                    <Button className="bg-dark col-md-6" type="submit">Log In</Button>
                </div>
            </Form>
        </div>
    )
}

// div container mt-3 w-75

LoginForm.propTypes = {
    _signIn: PropTypes.func,
};

export default LoginForm;
