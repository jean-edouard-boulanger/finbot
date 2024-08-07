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
import type { ValuationByAssetType } from "./ValuationByAssetType";
import {
  ValuationByAssetTypeFromJSON,
  ValuationByAssetTypeFromJSONTyped,
  ValuationByAssetTypeToJSON,
} from "./ValuationByAssetType";

/**
 *
 * @export
 * @interface AppGetUserAccountValuationByAssetTypeResponse
 */
export interface AppGetUserAccountValuationByAssetTypeResponse {
  /**
   *
   * @type {ValuationByAssetType}
   * @memberof AppGetUserAccountValuationByAssetTypeResponse
   */
  valuation: ValuationByAssetType;
}

/**
 * Check if a given object implements the AppGetUserAccountValuationByAssetTypeResponse interface.
 */
export function instanceOfAppGetUserAccountValuationByAssetTypeResponse(
  value: object,
): value is AppGetUserAccountValuationByAssetTypeResponse {
  if (!("valuation" in value) || value["valuation"] === undefined) return false;
  return true;
}

export function AppGetUserAccountValuationByAssetTypeResponseFromJSON(
  json: any,
): AppGetUserAccountValuationByAssetTypeResponse {
  return AppGetUserAccountValuationByAssetTypeResponseFromJSONTyped(
    json,
    false,
  );
}

export function AppGetUserAccountValuationByAssetTypeResponseFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): AppGetUserAccountValuationByAssetTypeResponse {
  if (json == null) {
    return json;
  }
  return {
    valuation: ValuationByAssetTypeFromJSON(json["valuation"]),
  };
}

export function AppGetUserAccountValuationByAssetTypeResponseToJSON(
  value?: AppGetUserAccountValuationByAssetTypeResponse | null,
): any {
  if (value == null) {
    return value;
  }
  return {
    valuation: ValuationByAssetTypeToJSON(value["valuation"]),
  };
}
