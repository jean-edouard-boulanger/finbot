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
import type { ValuationByCurrencyExposure } from './ValuationByCurrencyExposure';
import {
    ValuationByCurrencyExposureFromJSON,
    ValuationByCurrencyExposureFromJSONTyped,
    ValuationByCurrencyExposureToJSON,
} from './ValuationByCurrencyExposure';

/**
 * 
 * @export
 * @interface AppGetUserAccountValuationByCurrencyExposureResponse
 */
export interface AppGetUserAccountValuationByCurrencyExposureResponse {
    /**
     * 
     * @type {ValuationByCurrencyExposure}
     * @memberof AppGetUserAccountValuationByCurrencyExposureResponse
     */
    valuation: ValuationByCurrencyExposure;
}

/**
 * Check if a given object implements the AppGetUserAccountValuationByCurrencyExposureResponse interface.
 */
export function instanceOfAppGetUserAccountValuationByCurrencyExposureResponse(value: object): boolean {
    let isInstance = true;
    isInstance = isInstance && "valuation" in value;

    return isInstance;
}

export function AppGetUserAccountValuationByCurrencyExposureResponseFromJSON(json: any): AppGetUserAccountValuationByCurrencyExposureResponse {
    return AppGetUserAccountValuationByCurrencyExposureResponseFromJSONTyped(json, false);
}

export function AppGetUserAccountValuationByCurrencyExposureResponseFromJSONTyped(json: any, ignoreDiscriminator: boolean): AppGetUserAccountValuationByCurrencyExposureResponse {
    if ((json === undefined) || (json === null)) {
        return json;
    }
    return {
        
        'valuation': ValuationByCurrencyExposureFromJSON(json['valuation']),
    };
}

export function AppGetUserAccountValuationByCurrencyExposureResponseToJSON(value?: AppGetUserAccountValuationByCurrencyExposureResponse | null): any {
    if (value === undefined) {
        return undefined;
    }
    if (value === null) {
        return null;
    }
    return {
        
        'valuation': ValuationByCurrencyExposureToJSON(value.valuation),
    };
}

