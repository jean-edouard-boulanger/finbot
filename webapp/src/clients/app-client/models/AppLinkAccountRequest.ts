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
/**
 * 
 * @export
 * @interface AppLinkAccountRequest
 */
export interface AppLinkAccountRequest {
    /**
     * 
     * @type {string}
     * @memberof AppLinkAccountRequest
     */
    providerId: string;
    /**
     * 
     * @type {object}
     * @memberof AppLinkAccountRequest
     */
    credentials: object;
    /**
     * 
     * @type {string}
     * @memberof AppLinkAccountRequest
     */
    accountName: string;
    /**
     * 
     * @type {string}
     * @memberof AppLinkAccountRequest
     */
    accountColour: string;
}

/**
 * Check if a given object implements the AppLinkAccountRequest interface.
 */
export function instanceOfAppLinkAccountRequest(value: object): boolean {
    let isInstance = true;
    isInstance = isInstance && "providerId" in value;
    isInstance = isInstance && "credentials" in value;
    isInstance = isInstance && "accountName" in value;
    isInstance = isInstance && "accountColour" in value;

    return isInstance;
}

export function AppLinkAccountRequestFromJSON(json: any): AppLinkAccountRequest {
    return AppLinkAccountRequestFromJSONTyped(json, false);
}

export function AppLinkAccountRequestFromJSONTyped(json: any, ignoreDiscriminator: boolean): AppLinkAccountRequest {
    if ((json === undefined) || (json === null)) {
        return json;
    }
    return {
        
        'providerId': json['provider_id'],
        'credentials': json['credentials'],
        'accountName': json['account_name'],
        'accountColour': json['account_colour'],
    };
}

export function AppLinkAccountRequestToJSON(value?: AppLinkAccountRequest | null): any {
    if (value === undefined) {
        return undefined;
    }
    if (value === null) {
        return null;
    }
    return {
        
        'provider_id': value.providerId,
        'credentials': value.credentials,
        'account_name': value.accountName,
        'account_colour': value.accountColour,
    };
}

