import React, { useContext } from "react";
import styled from 'styled-components';

import Form from "react-jsonschema-form";
import Button from "react-bootstrap/Button";
import ProvidersContext from "../../context/linked-account-context";
import SpinnerButton from "./spinner-button"

const StyledContainer = styled.div`
height: 100%;
display: flex;
justify-content: center;
alignItems: center;
padding: 85px 25px 455px;
`

const LinkExternalAccount = () => {

    const providersContext = useContext(ProvidersContext);
    const { schema, _validateCredentials, loading } = providersContext;

    return (

        schema ?

            <>
                <StyledContainer>
                    <Form
                        className="border border-secondary p-4 text-center opaque-background sign-form"
                        schema={schema.json_schema || {}}
                        uiSchema={schema.ui_schema || {}}
                        onSubmit={_validateCredentials}
                        showErrorList={false} >
                        <div>
                            {loading.current ? <SpinnerButton message={loading.message} /> : <Button className="bg-dark" type="submit">Link Account</Button>}
                        </div>
                    </Form>
                </StyledContainer>
            </>

            :

            null
    )
}

export default LinkExternalAccount;