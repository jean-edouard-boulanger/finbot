/* tslint:disable */
/* eslint-disable */
/**
 * Finbot application service
 * API documentation for appwsrv
 *
 *
 *
 * NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).
 * https://openapi-generator.tech
 * Do not edit the class manually.
 */

import { mapValues } from "../runtime";
import type { ValuationFrequency } from "./ValuationFrequency";
import {
  ValuationFrequencyFromJSON,
  ValuationFrequencyFromJSONTyped,
  ValuationFrequencyToJSON,
} from "./ValuationFrequency";

/**
 *
 * @export
 * @interface AppHistoricalValuationParams
 */
export interface AppHistoricalValuationParams {
  /**
   *
   * @type {Date}
   * @memberof AppHistoricalValuationParams
   */
  fromTime?: Date;
  /**
   *
   * @type {Date}
   * @memberof AppHistoricalValuationParams
   */
  toTime?: Date;
  /**
   *
   * @type {ValuationFrequency}
   * @memberof AppHistoricalValuationParams
   */
  frequency?: ValuationFrequency;
}

/**
 * Check if a given object implements the AppHistoricalValuationParams interface.
 */
export function instanceOfAppHistoricalValuationParams(
  value: object,
): value is AppHistoricalValuationParams {
  return true;
}

export function AppHistoricalValuationParamsFromJSON(
  json: any,
): AppHistoricalValuationParams {
  return AppHistoricalValuationParamsFromJSONTyped(json, false);
}

export function AppHistoricalValuationParamsFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): AppHistoricalValuationParams {
  if (json == null) {
    return json;
  }
  return {
    fromTime:
      json["from_time"] == null ? undefined : new Date(json["from_time"]),
    toTime: json["to_time"] == null ? undefined : new Date(json["to_time"]),
    frequency:
      json["frequency"] == null
        ? undefined
        : ValuationFrequencyFromJSON(json["frequency"]),
  };
}

export function AppHistoricalValuationParamsToJSON(
  value?: AppHistoricalValuationParams | null,
): any {
  if (value == null) {
    return value;
  }
  return {
    from_time:
      value["fromTime"] == null ? undefined : value["fromTime"].toISOString(),
    to_time:
      value["toTime"] == null ? undefined : value["toTime"].toISOString(),
    frequency: ValuationFrequencyToJSON(value["frequency"]),
  };
}
