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
import type { ValuationByAssetClass } from "./ValuationByAssetClass";
import {
  ValuationByAssetClassFromJSON,
  ValuationByAssetClassFromJSONTyped,
  ValuationByAssetClassToJSON,
} from "./ValuationByAssetClass";

/**
 *
 * @export
 * @interface AppGetUserAccountValuationByAssetClassResponse
 */
export interface AppGetUserAccountValuationByAssetClassResponse {
  /**
   *
   * @type {ValuationByAssetClass}
   * @memberof AppGetUserAccountValuationByAssetClassResponse
   */
  valuation: ValuationByAssetClass;
}

/**
 * Check if a given object implements the AppGetUserAccountValuationByAssetClassResponse interface.
 */
export function instanceOfAppGetUserAccountValuationByAssetClassResponse(
  value: object,
): value is AppGetUserAccountValuationByAssetClassResponse {
  if (!("valuation" in value) || value["valuation"] === undefined) return false;
  return true;
}

export function AppGetUserAccountValuationByAssetClassResponseFromJSON(
  json: any,
): AppGetUserAccountValuationByAssetClassResponse {
  return AppGetUserAccountValuationByAssetClassResponseFromJSONTyped(
    json,
    false,
  );
}

export function AppGetUserAccountValuationByAssetClassResponseFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): AppGetUserAccountValuationByAssetClassResponse {
  if (json == null) {
    return json;
  }
  return {
    valuation: ValuationByAssetClassFromJSON(json["valuation"]),
  };
}

export function AppGetUserAccountValuationByAssetClassResponseToJSON(
  value?: AppGetUserAccountValuationByAssetClassResponse | null,
): any {
  if (value == null) {
    return value;
  }
  return {
    valuation: ValuationByAssetClassToJSON(value["valuation"]),
  };
}
