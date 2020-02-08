import React, { useState } from 'react';
import FinbotClient from "../FinbotClient/FinbotClient";
import ProvidersContext from "../context/LinkedAccountContext";

const LinkedAccountState = props => {

    const finbot_client = new FinbotClient();
    const [selectedProvider, setProvider] = useState(null);
    const [schema, setSchema] = useState(null)
    const [providersList, setProviders] = useState([])

    function _retrieveSchema(provSelected) {
        const relSchema = providersList.filter(prov => prov.id === provSelected)[0].credentials_schema || null;
        setSchema(relSchema)
    }

    async function _awaitProviders() {
        const providers = await finbot_client.getProviders();
        setProviders([...providers])
    }

    function _selectProvider(providerID) {
        console.log("TARGET", providerID);
        setProvider(providerID);
        _retrieveSchema(providerID);
    }

    async function _validateCredentials(input) {
        console.log("in validate", input)
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
                schema: schema,
                selectedProvider: selectedProvider,
                providersList: providersList,
                _selectProvider: _selectProvider,
                _awaitProviders: _awaitProviders,
                _retrieveSchema: _retrieveSchema,
                _validateCredentials
            }}>
            {props.children}
        </ProvidersContext.Provider>
    )
}

export default LinkedAccountState;