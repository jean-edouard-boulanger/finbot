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
import type { AggregationDescription } from './AggregationDescription';
import {
    AggregationDescriptionFromJSON,
    AggregationDescriptionFromJSONTyped,
    AggregationDescriptionToJSON,
} from './AggregationDescription';
import type { Metrics } from './Metrics';
import {
    MetricsFromJSON,
    MetricsFromJSONTyped,
    MetricsToJSON,
} from './Metrics';

/**
 * 
 * @export
 * @interface ReportEntry
 */
export interface ReportEntry {
    /**
     * 
     * @type {AggregationDescription}
     * @memberof ReportEntry
     */
    aggregation: AggregationDescription;
    /**
     * 
     * @type {Metrics}
     * @memberof ReportEntry
     */
    metrics: Metrics;
}

/**
 * Check if a given object implements the ReportEntry interface.
 */
export function instanceOfReportEntry(value: object): boolean {
    let isInstance = true;
    isInstance = isInstance && "aggregation" in value;
    isInstance = isInstance && "metrics" in value;

    return isInstance;
}

export function ReportEntryFromJSON(json: any): ReportEntry {
    return ReportEntryFromJSONTyped(json, false);
}

export function ReportEntryFromJSONTyped(json: any, ignoreDiscriminator: boolean): ReportEntry {
    if ((json === undefined) || (json === null)) {
        return json;
    }
    return {
        
        'aggregation': AggregationDescriptionFromJSON(json['aggregation']),
        'metrics': MetricsFromJSON(json['metrics']),
    };
}

export function ReportEntryToJSON(value?: ReportEntry | null): any {
    if (value === undefined) {
        return undefined;
    }
    if (value === null) {
        return null;
    }
    return {
        
        'aggregation': AggregationDescriptionToJSON(value.aggregation),
        'metrics': MetricsToJSON(value.metrics),
    };
}

