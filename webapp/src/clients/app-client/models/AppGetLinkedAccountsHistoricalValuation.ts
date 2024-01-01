/* tslint:disable */
/* eslint-disable */
/**
 * Finbot application service
 * API documentation for appwsrv
 *
 * The version of the OpenAPI document: v0.0.4
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
 * @interface AppGetLinkedAccountsHistoricalValuation
 */
export interface AppGetLinkedAccountsHistoricalValuation {
  /**
   *
   * @type {HistoricalValuation}
   * @memberof AppGetLinkedAccountsHistoricalValuation
   */
  historicalValuation: HistoricalValuation;
}

/**
 * Check if a given object implements the AppGetLinkedAccountsHistoricalValuation interface.
 */
export function instanceOfAppGetLinkedAccountsHistoricalValuation(
  value: object,
): boolean {
  let isInstance = true;
  isInstance = isInstance && "historicalValuation" in value;

  return isInstance;
}

export function AppGetLinkedAccountsHistoricalValuationFromJSON(
  json: any,
): AppGetLinkedAccountsHistoricalValuation {
  return AppGetLinkedAccountsHistoricalValuationFromJSONTyped(json, false);
}

export function AppGetLinkedAccountsHistoricalValuationFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): AppGetLinkedAccountsHistoricalValuation {
  if (json === undefined || json === null) {
    return json;
  }
  return {
    historicalValuation: HistoricalValuationFromJSON(
      json["historical_valuation"],
    ),
  };
}

export function AppGetLinkedAccountsHistoricalValuationToJSON(
  value?: AppGetLinkedAccountsHistoricalValuation | null,
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
