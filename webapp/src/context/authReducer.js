import {
    REGISTER_SUCCESS,
    REGISTER_FAIL,
    AUTH_ERROR,
    LOGIN_SUCCESS,
    LOGIN_FAIL,
    LOGOUT,
    CLEAR_ERRORS
} from './types';

export default (state, action) => {
    switch (action.type) {
        case REGISTER_SUCCESS:
            return {
                ...state,
                loading: false,
                accountID: action.payload.id
            }
        case LOGIN_SUCCESS:
            localStorage.setItem('identity', action.payload.auth.access_token);
            return {
                ...state,
                isAuthenticated: true,
                loading: false,
                token: action.payload.auth.access_token,
                accountID: action.payload.account.id
            };
        case REGISTER_FAIL:
        case AUTH_ERROR:
        case LOGIN_FAIL:
            localStorage.removeItem('identity');
            return {
                ...state,
                token: null,
                isAuthenticated: false,
                loading: false,
                error: action.payload,
                accountID: null
            };
        case LOGOUT:
            localStorage.removeItem('identity');
            return {
                ...state,
                token: null,
                isAuthenticated: false,
                loading: false,
                accountID: null
            };
        case CLEAR_ERRORS:
            return {
                ...state,
                error: null
            };
        default:
            return state;
    }
};
