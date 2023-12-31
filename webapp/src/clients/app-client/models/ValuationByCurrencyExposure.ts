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
import type { GroupValuation } from './GroupValuation';
import {
    GroupValuationFromJSON,
    GroupValuationFromJSONTyped,
    GroupValuationToJSON,
} from './GroupValuation';

/**
 * 
 * @export
 * @interface ValuationByCurrencyExposure
 */
export interface ValuationByCurrencyExposure {
    /**
     * 
     * @type {string}
     * @memberof ValuationByCurrencyExposure
     */
    valuationCcy: string;
    /**
     * 
     * @type {Array<GroupValuation>}
     * @memberof ValuationByCurrencyExposure
     */
    byCurrencyExposure: Array<GroupValuation>;
}

/**
 * Check if a given object implements the ValuationByCurrencyExposure interface.
 */
export function instanceOfValuationByCurrencyExposure(value: object): boolean {
    let isInstance = true;
    isInstance = isInstance && "valuationCcy" in value;
    isInstance = isInstance && "byCurrencyExposure" in value;

    return isInstance;
}

export function ValuationByCurrencyExposureFromJSON(json: any): ValuationByCurrencyExposure {
    return ValuationByCurrencyExposureFromJSONTyped(json, false);
}

export function ValuationByCurrencyExposureFromJSONTyped(json: any, ignoreDiscriminator: boolean): ValuationByCurrencyExposure {
    if ((json === undefined) || (json === null)) {
        return json;
    }
    return {
        
        'valuationCcy': json['valuation_ccy'],
        'byCurrencyExposure': ((json['by_currency_exposure'] as Array<any>).map(GroupValuationFromJSON)),
    };
}

export function ValuationByCurrencyExposureToJSON(value?: ValuationByCurrencyExposure | null): any {
    if (value === undefined) {
        return undefined;
    }
    if (value === null) {
        return null;
    }
    return {
        
        'valuation_ccy': value.valuationCcy,
        'by_currency_exposure': ((value.byCurrencyExposure as Array<any>).map(GroupValuationToJSON)),
    };
}

