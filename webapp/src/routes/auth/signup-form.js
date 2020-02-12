import React from "react";
import PropTypes from "prop-types";
import Form from "react-jsonschema-form";
import Button from "react-bootstrap/Button";


const SignupForm = props => {

    const schema = {
        "title": "SIGN UP",
        "type": "object",
        "required": [
            "full_name",
            "password",
            "settings",
            "email"
        ],
        "properties": {
            "full_name": {
                "type": "string",
                "title": "Name",
                minLength: 4
            },
            "email": {
                "type": "string",
                "title": "E-Mail",
                "format": "email"
            },
            "settings": {
                "type": "string",
                "title": "Settings",
                "enum": [
                    "EUR",
                    "GBP",
                    "AUD",
                    "USD",
                    "CAD",
                    "JPY",
                    "CNY",
                    "INR",
                    "CHF"
                ]
            },
            "password": {
                "type": "string",
                "title": "Password",
                "minLength": 7
            }
        }
    }

    const uiSchema = {
        "full_name": {
            "ui:autofocus": true,
            "ui:emptyValue": "",
            "ui:placeholder": "John Doe"
        },
        "email": {
            "ui:emptyValue": ""
        },
        "password": {
            "ui:widget": "password",
            "ui:help": "Hint: Make it strong!"
        },
        "settings": {
            "ui:placeholder": "Choose one",
            "ui:description": "Choose currency"
        }
    }

    const _onSubmit = (e) => {
        console.log("submitted")
        props._signUp(e);
    }

    return (
        <div className="container mt-5 w-75">
            <Form
                className="border border-secondary p-4 text-center opaque-background"
                schema={schema}
                uiSchema={uiSchema}
                onSubmit={_onSubmit}
                showErrorList={false} >
                <div>
                    <Button className="bg-dark" type="submit">Submit</Button>
                    <Button className="bg-dark" type="button">Log In</Button>
                </div>
            </Form>
        </div>
    )
}

SignupForm.propTypes = {
    _signUp: PropTypes.func,
};

export default SignupForm;