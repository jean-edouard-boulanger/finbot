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

import { exists, mapValues } from "../runtime";
import type { UserAccountValuation } from "./UserAccountValuation";
import {
  UserAccountValuationFromJSON,
  UserAccountValuationFromJSONTyped,
  UserAccountValuationToJSON,
} from "./UserAccountValuation";

/**
 *
 * @export
 * @interface AppGetUserAccountValuationResponse
 */
export interface AppGetUserAccountValuationResponse {
  /**
   *
   * @type {UserAccountValuation}
   * @memberof AppGetUserAccountValuationResponse
   */
  valuation: UserAccountValuation;
}

/**
 * Check if a given object implements the AppGetUserAccountValuationResponse interface.
 */
export function instanceOfAppGetUserAccountValuationResponse(
  value: object,
): boolean {
  let isInstance = true;
  isInstance = isInstance && "valuation" in value;

  return isInstance;
}

export function AppGetUserAccountValuationResponseFromJSON(
  json: any,
): AppGetUserAccountValuationResponse {
  return AppGetUserAccountValuationResponseFromJSONTyped(json, false);
}

export function AppGetUserAccountValuationResponseFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): AppGetUserAccountValuationResponse {
  if (json === undefined || json === null) {
    return json;
  }
  return {
    valuation: UserAccountValuationFromJSON(json["valuation"]),
  };
}

export function AppGetUserAccountValuationResponseToJSON(
  value?: AppGetUserAccountValuationResponse | null,
): any {
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  return {
    valuation: UserAccountValuationToJSON(value.valuation),
  };
}
