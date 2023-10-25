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
import type { HistoricalValuation } from "./HistoricalValuation";
import {
  HistoricalValuationFromJSON,
  HistoricalValuationFromJSONTyped,
  HistoricalValuationToJSON,
} from "./HistoricalValuation";

/**
 *
 * @export
 * @interface AppGetUserAccountValuationHistoryResponse
 */
export interface AppGetUserAccountValuationHistoryResponse {
  /**
   *
   * @type {HistoricalValuation}
   * @memberof AppGetUserAccountValuationHistoryResponse
   */
  historicalValuation: HistoricalValuation;
}

/**
 * Check if a given object implements the AppGetUserAccountValuationHistoryResponse interface.
 */
export function instanceOfAppGetUserAccountValuationHistoryResponse(
  value: object,
): boolean {
  let isInstance = true;
  isInstance = isInstance && "historicalValuation" in value;

  return isInstance;
}

export function AppGetUserAccountValuationHistoryResponseFromJSON(
  json: any,
): AppGetUserAccountValuationHistoryResponse {
  return AppGetUserAccountValuationHistoryResponseFromJSONTyped(json, false);
}

export function AppGetUserAccountValuationHistoryResponseFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): AppGetUserAccountValuationHistoryResponse {
  if (json === undefined || json === null) {
    return json;
  }
  return {
    historicalValuation: HistoricalValuationFromJSON(
      json["historical_valuation"],
    ),
  };
}

export function AppGetUserAccountValuationHistoryResponseToJSON(
  value?: AppGetUserAccountValuationHistoryResponse | null,
): any {
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  return {
    historical_valuation: HistoricalValuationToJSON(value.historicalValuation),
  };
}
