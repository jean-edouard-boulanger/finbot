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
import type { HistoricalValuation } from './HistoricalValuation';
import {
    HistoricalValuationFromJSON,
    HistoricalValuationFromJSONTyped,
    HistoricalValuationToJSON,
} from './HistoricalValuation';

/**
 * 
 * @export
 * @interface AppGetUserAccountValuationHistoryByAssetClassResponse
 */
export interface AppGetUserAccountValuationHistoryByAssetClassResponse {
    /**
     * 
     * @type {HistoricalValuation}
     * @memberof AppGetUserAccountValuationHistoryByAssetClassResponse
     */
    historicalValuation: HistoricalValuation;
}

/**
 * Check if a given object implements the AppGetUserAccountValuationHistoryByAssetClassResponse interface.
 */
export function instanceOfAppGetUserAccountValuationHistoryByAssetClassResponse(value: object): boolean {
    let isInstance = true;
    isInstance = isInstance && "historicalValuation" in value;

    return isInstance;
}

export function AppGetUserAccountValuationHistoryByAssetClassResponseFromJSON(json: any): AppGetUserAccountValuationHistoryByAssetClassResponse {
    return AppGetUserAccountValuationHistoryByAssetClassResponseFromJSONTyped(json, false);
}

export function AppGetUserAccountValuationHistoryByAssetClassResponseFromJSONTyped(json: any, ignoreDiscriminator: boolean): AppGetUserAccountValuationHistoryByAssetClassResponse {
    if ((json === undefined) || (json === null)) {
        return json;
    }
    return {
        
        'historicalValuation': HistoricalValuationFromJSON(json['historical_valuation']),
    };
}

export function AppGetUserAccountValuationHistoryByAssetClassResponseToJSON(value?: AppGetUserAccountValuationHistoryByAssetClassResponse | null): any {
    if (value === undefined) {
        return undefined;
    }
    if (value === null) {
        return null;
    }
    return {
        
        'historical_valuation': HistoricalValuationToJSON(value.historicalValuation),
    };
}

