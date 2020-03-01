import {
    SET_SCHEMA,
    SET_SELECTED_PROVIDER,
    INITIALIZE_PROVIDERS,
    VALIDATION_LINKING_FAIL,
    LINKING_ACCOUNT_SUCCESS,
    SET_LOADING,
    VALIDATION_SUCCESS,
    CLEAR_TOAST,
} from './types';

export default (state, action) => {
    switch (action.type) {
        case SET_SCHEMA:
            return {
                ...state,
                schema: action.payload,
                loading: { current: false, message: null }
            }
        case SET_SELECTED_PROVIDER:
            return {
                ...state,
                selectedProvider: action.payload.selected,
                loading: { current: true, message: action.payload.message }
            }
        case INITIALIZE_PROVIDERS:
            return {
                ...state,
                providersList: [...action.payload]
            }
        case VALIDATION_LINKING_FAIL:
            return {
                ...state,
                error: action.payload,
                loading: { current: false, message: null }
            }
        case LINKING_ACCOUNT_SUCCESS:
            return {
                ...state,
                error: null,
                loading: { current: false, message: null },
                accountIsLinked: true
            }
        case SET_LOADING:
        case VALIDATION_SUCCESS:
            return {
                ...state,
                loading: { current: true, message: action.payload }
            }
        case CLEAR_TOAST:
            return {
                ...state,
                error: null,
                accountIsLinked: false
            };
        default:
            return state;
    }
};
