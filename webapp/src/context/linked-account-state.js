import React, { useReducer } from 'react';
import FinbotClient from "../clients/finbot-client";
import ProvidersContext from "./linked-account-context";
import linkedAccountReducer from "./LinkedAccountReducer";
import {
    SET_SCHEMA,
    SET_SELECTED_PROVIDER,
    INITIALIZE_PROVIDERS,
    VALIDATION_LINKING_FAIL,
    LINKING_ACCOUNT_SUCCESS,
    SET_LOADING,
    VALIDATION_SUCCESS,
    CLEAR_ERRORS,
} from "./types"


const LinkedAccountState = props => {

    const finbot_client = new FinbotClient();

    const initialState = {
        selectedProvider: null,
        schema: null,
        providersList: [],
        error: null,
        loading: { current: false, message: null },
        accountIsLinked: false
    };

    const [state, dispatch] = useReducer(linkedAccountReducer, initialState);


    function _getCurrentProvider() {
        return state.providersList.filter(prov => prov.id === state.selectedProvider)[0]
    }

    function _retrieveSchema(provSelected) {
        const relSchema = state.providersList.filter(prov => prov.id === provSelected)[0].credentials_schema || null;
        dispatch({
            type: SET_SCHEMA,
            payload: relSchema
        });
    }

    async function _awaitProviders() {
        const providers = await finbot_client.getProviders();
        dispatch({
            type: INITIALIZE_PROVIDERS,
            payload: providers
        })
    }

    function _selectProvider(providerID) {
        console.log("in selctprovider")
        dispatch({
            type: SET_SELECTED_PROVIDER,
            payload: providerID
        })
        _retrieveSchema(providerID);

    }

    function _clearErrors() { dispatch({ type: CLEAR_ERRORS }) };

    async function _validateCredentials(input) {
        console.log("in valid creden", input)
        const params = {
            credentials: input.formData || {},
            provider_id: state.selectedProvider,
            account_name: state.providersList.filter(provider => provider.id === state.selectedProvider)[0].description
        }
        dispatch({ type: SET_LOADING, payload: "Validating credentials" })
        try {
            const response = await finbot_client.validateExternalAccountCredentials(params)
            console.log("VALIDATE?", params, response)
            dispatch({ type: VALIDATION_SUCCESS, payload: "Linking Account" })
            const secResponse = await finbot_client.linkAccount(params);
            console.log("SECRES LINK ACOCUNZ", secResponse);
            dispatch({ type: LINKING_ACCOUNT_SUCCESS })
        } catch (err) {
            dispatch({ type: VALIDATION_LINKING_FAIL, payload: err })
            console.log("VALIDFAIL", err);
        }
    }

    return (
        <ProvidersContext.Provider
            value={{
                schema: state.schema,
                selectedProvider: state.selectedProvider,
                providersList: state.providersList,
                error: state.error,
                loading: state.loading,
                accountIsLinked: state.accountIsLinked,
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