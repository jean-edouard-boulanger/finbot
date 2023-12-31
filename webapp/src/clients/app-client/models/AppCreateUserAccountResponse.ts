/* tslint:disable */
/* eslint-disable */
/**
 * Finbot application service
 * API documentation for appwsrv
 *
 * The version of the OpenAPI document: v0.0.3
 * 
 *
 * NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).
 * https://openapi-generator.tech
 * Do not edit the class manually.
 */

import { exists, mapValues } from '../runtime';
import type { UserAccount } from './UserAccount';
import {
    UserAccountFromJSON,
    UserAccountFromJSONTyped,
    UserAccountToJSON,
} from './UserAccount';

/**
 * 
 * @export
 * @interface AppCreateUserAccountResponse
 */
export interface AppCreateUserAccountResponse {
    /**
     * 
     * @type {UserAccount}
     * @memberof AppCreateUserAccountResponse
     */
    userAccount: UserAccount;
}

/**
 * Check if a given object implements the AppCreateUserAccountResponse interface.
 */
export function instanceOfAppCreateUserAccountResponse(value: object): boolean {
    let isInstance = true;
    isInstance = isInstance && "userAccount" in value;

    return isInstance;
}

export function AppCreateUserAccountResponseFromJSON(json: any): AppCreateUserAccountResponse {
    return AppCreateUserAccountResponseFromJSONTyped(json, false);
}

export function AppCreateUserAccountResponseFromJSONTyped(json: any, ignoreDiscriminator: boolean): AppCreateUserAccountResponse {
    if ((json === undefined) || (json === null)) {
        return json;
    }
    return {
        
        'userAccount': UserAccountFromJSON(json['user_account']),
    };
}

export function AppCreateUserAccountResponseToJSON(value?: AppCreateUserAccountResponse | null): any {
    if (value === undefined) {
        return undefined;
    }
    if (value === null) {
        return null;
    }
    return {
        
        'user_account': UserAccountToJSON(value.userAccount),
    };
}

