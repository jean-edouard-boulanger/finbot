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
 * @interface AppLinkAccountCommitParams
 */
export interface AppLinkAccountCommitParams {
    /**
     * 
     * @type {boolean}
     * @memberof AppLinkAccountCommitParams
     */
    validate?: boolean;
    /**
     * 
     * @type {boolean}
     * @memberof AppLinkAccountCommitParams
     */
    persist?: boolean;
}

/**
 * Check if a given object implements the AppLinkAccountCommitParams interface.
 */
export function instanceOfAppLinkAccountCommitParams(value: object): boolean {
    let isInstance = true;

    return isInstance;
}

export function AppLinkAccountCommitParamsFromJSON(json: any): AppLinkAccountCommitParams {
    return AppLinkAccountCommitParamsFromJSONTyped(json, false);
}

export function AppLinkAccountCommitParamsFromJSONTyped(json: any, ignoreDiscriminator: boolean): AppLinkAccountCommitParams {
    if ((json === undefined) || (json === null)) {
        return json;
    }
    return {
        
        'validate': !exists(json, 'validate') ? undefined : json['validate'],
        'persist': !exists(json, 'persist') ? undefined : json['persist'],
    };
}

export function AppLinkAccountCommitParamsToJSON(value?: AppLinkAccountCommitParams | null): any {
    if (value === undefined) {
        return undefined;
    }
    if (value === null) {
        return null;
    }
    return {
        
        'validate': value.validate,
        'persist': value.persist,
    };
}

