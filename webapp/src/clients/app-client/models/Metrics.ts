/* tslint:disable */
/* eslint-disable */
/**
 * Finbot application service
 * API documentation for appwsrv
 *
 * The version of the OpenAPI document: v0.0.2
 *
 *
 * NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).
 * https://openapi-generator.tech
 * Do not edit the class manually.
 */

import { exists, mapValues } from "../runtime";
/**
 *
 * @export
 * @interface Metrics
 */
export interface Metrics {
  /**
   *
   * @type {Date}
   * @memberof Metrics
   */
  firstDate: Date;
  /**
   *
   * @type {number}
   * @memberof Metrics
   */
  firstValue: number;
  /**
   *
   * @type {Date}
   * @memberof Metrics
   */
  lastDate: Date;
  /**
   *
   * @type {number}
   * @memberof Metrics
   */
  lastValue: number;
  /**
   *
   * @type {number}
   * @memberof Metrics
   */
  minValue: number;
  /**
   *
   * @type {number}
   * @memberof Metrics
   */
  maxValue: number;
  /**
   *
   * @type {number}
   * @memberof Metrics
   */
  absChange: number;
  /**
   *
   * @type {number}
   * @memberof Metrics
   */
  relChange: number;
}

/**
 * Check if a given object implements the Metrics interface.
 */
export function instanceOfMetrics(value: object): boolean {
  let isInstance = true;
  isInstance = isInstance && "firstDate" in value;
  isInstance = isInstance && "firstValue" in value;
  isInstance = isInstance && "lastDate" in value;
  isInstance = isInstance && "lastValue" in value;
  isInstance = isInstance && "minValue" in value;
  isInstance = isInstance && "maxValue" in value;
  isInstance = isInstance && "absChange" in value;
  isInstance = isInstance && "relChange" in value;

  return isInstance;
}

export function MetricsFromJSON(json: any): Metrics {
  return MetricsFromJSONTyped(json, false);
}

export function MetricsFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): Metrics {
  if (json === undefined || json === null) {
    return json;
  }
  return {
    firstDate: new Date(json["first_date"]),
    firstValue: json["first_value"],
    lastDate: new Date(json["last_date"]),
    lastValue: json["last_value"],
    minValue: json["min_value"],
    maxValue: json["max_value"],
    absChange: json["abs_change"],
    relChange: json["rel_change"],
  };
}

export function MetricsToJSON(value?: Metrics | null): any {
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  return {
    first_date: value.firstDate.toISOString(),
    first_value: value.firstValue,
    last_date: value.lastDate.toISOString(),
    last_value: value.lastValue,
    min_value: value.minValue,
    max_value: value.maxValue,
    abs_change: value.absChange,
    rel_change: value.relChange,
  };
}
