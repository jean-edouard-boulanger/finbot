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


/**
 * An enumeration.
 * @export
 */
export const ValuationFrequency = {
    Daily: 'Daily',
    Weekly: 'Weekly',
    Monthly: 'Monthly',
    Quarterly: 'Quarterly',
    Yearly: 'Yearly'
} as const;
export type ValuationFrequency = typeof ValuationFrequency[keyof typeof ValuationFrequency];


export function ValuationFrequencyFromJSON(json: any): ValuationFrequency {
    return ValuationFrequencyFromJSONTyped(json, false);
}

export function ValuationFrequencyFromJSONTyped(json: any, ignoreDiscriminator: boolean): ValuationFrequency {
    return json as ValuationFrequency;
}

export function ValuationFrequencyToJSON(value?: ValuationFrequency | null): any {
    return value as any;
}

