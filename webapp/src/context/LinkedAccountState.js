import React, { useState } from 'react';
import FinbotClient from "../FinbotClient/FinbotClient";
import ProvidersContext from "../context/LinkedAccountContext";

const LinkedAccountState = props => {

    const finbot_client = new FinbotClient();
    const [selectedProvider, setProvider] = useState(null);
    const [schema, setSchema] = useState(null);
    const [providersList, setProviders] = useState([]);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);
    const [accountIsLinked, setAccountIsLinked] = useState(false);

    function _getCurrentProvider() {
        return providersList.filter(prov => prov.id === selectedProvider)[0]
    }

    function _retrieveSchema(provSelected) {
        const relSchema = providersList.filter(prov => prov.id === provSelected)[0].credentials_schema || null;
        setSchema(relSchema)
    }

    async function _awaitProviders() {
        const providers = await finbot_client.getProviders();
        setProviders([...providers])
    }

    function _selectProvider(providerID) {
        setProvider(providerID);
        _retrieveSchema(providerID);
    }

    function _clearErrors() { setError(null) };

    async function _validateCredentials(input) {
        console.log("in valid creden", input)
        const params = {
            credentials: input.formData || {},
            provider_id: selectedProvider,
            account_name: providersList.filter(provider => provider.id === selectedProvider)[0].description
        }
        setLoading(true)
        try {
            const response = await finbot_client.validateCredentials(params)
            console.log("VALIDATE?", params, response)
            const secResponse = await finbot_client.linkAccount(params);
            console.log("SECRES LINK ACOCUNZ", secResponse);
            setLoading(false);
            setAccountIsLinked(true);
        } catch (err) {
            setError(err);
            setLoading(false)
            console.log("VALIDFAIL", err)
        }
    }

    return (
        <ProvidersContext.Provider
            value={{
                schema,
                selectedProvider,
                providersList,
                error,
                loading,
                accountIsLinked,
                _selectProvider,
                _awaitProviders,
                _retrieveSchema,
                _getCurrentProvider,
                _validateCredentials,
                _clearErrors
            }}>
            {props.children}
        </ProvidersContext.Provider>
    )
}

export default LinkedAccountState;