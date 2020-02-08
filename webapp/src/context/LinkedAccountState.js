import React, { useState } from 'react';
import FinbotClient from "../FinbotClient/FinbotClient";
import ProvidersContext from "../context/LinkedAccountContext";

const LinkedAccountState = props => {

    const finbot_client = new FinbotClient();
    const [selectedProvider, setProvider] = useState(null);
    const [schema, setSchema] = useState(null)
    const [providersList, setProviders] = useState([])

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

    async function _validateCredentials(input) {
        const params = {
            credentials: input.formData,
            provider_id: selectedProvider,
            account_name: providersList.filter(provider => provider.id === selectedProvider)[0].description
        }
        try {
            const response = await finbot_client.validateCredentials(params)
            console.log("VALIDATE?", params, response)
        } catch (err) {
            console.log("VALIDFAIL", err)
        }
    }

    return (
        <ProvidersContext.Provider
            value={{
                schema,
                selectedProvider,
                providersList,
                _selectProvider,
                _awaitProviders,
                _retrieveSchema,
                _getCurrentProvider,
                _validateCredentials
            }}>
            {props.children}
        </ProvidersContext.Provider>
    )
}

export default LinkedAccountState;