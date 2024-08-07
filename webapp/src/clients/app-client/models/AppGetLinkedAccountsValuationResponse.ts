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
import type { LinkedAccountsValuation } from "./LinkedAccountsValuation";
import {
  LinkedAccountsValuationFromJSON,
  LinkedAccountsValuationFromJSONTyped,
  LinkedAccountsValuationToJSON,
} from "./LinkedAccountsValuation";

/**
 *
 * @export
 * @interface AppGetLinkedAccountsValuationResponse
 */
export interface AppGetLinkedAccountsValuationResponse {
  /**
   *
   * @type {LinkedAccountsValuation}
   * @memberof AppGetLinkedAccountsValuationResponse
   */
  valuation: LinkedAccountsValuation;
}

/**
 * Check if a given object implements the AppGetLinkedAccountsValuationResponse interface.
 */
export function instanceOfAppGetLinkedAccountsValuationResponse(
  value: object,
): value is AppGetLinkedAccountsValuationResponse {
  if (!("valuation" in value) || value["valuation"] === undefined) return false;
  return true;
}

export function AppGetLinkedAccountsValuationResponseFromJSON(
  json: any,
): AppGetLinkedAccountsValuationResponse {
  return AppGetLinkedAccountsValuationResponseFromJSONTyped(json, false);
}

export function AppGetLinkedAccountsValuationResponseFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): AppGetLinkedAccountsValuationResponse {
  if (json == null) {
    return json;
  }
  return {
    valuation: LinkedAccountsValuationFromJSON(json["valuation"]),
  };
}

export function AppGetLinkedAccountsValuationResponseToJSON(
  value?: AppGetLinkedAccountsValuationResponse | null,
): any {
  if (value == null) {
    return value;
  }
  return {
    valuation: LinkedAccountsValuationToJSON(value["valuation"]),
  };
}
