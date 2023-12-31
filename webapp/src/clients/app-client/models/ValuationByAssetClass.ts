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

import { exists, mapValues } from "../runtime";
import type { GroupValuation } from "./GroupValuation";
import {
  GroupValuationFromJSON,
  GroupValuationFromJSONTyped,
  GroupValuationToJSON,
} from "./GroupValuation";

/**
 *
 * @export
 * @interface ValuationByAssetClass
 */
export interface ValuationByAssetClass {
  /**
   *
   * @type {string}
   * @memberof ValuationByAssetClass
   */
  valuationCcy: string;
  /**
   *
   * @type {Array<GroupValuation>}
   * @memberof ValuationByAssetClass
   */
  byAssetClass: Array<GroupValuation>;
}

/**
 * Check if a given object implements the ValuationByAssetClass interface.
 */
export function instanceOfValuationByAssetClass(value: object): boolean {
  let isInstance = true;
  isInstance = isInstance && "valuationCcy" in value;
  isInstance = isInstance && "byAssetClass" in value;

  return isInstance;
}

export function ValuationByAssetClassFromJSON(
  json: any,
): ValuationByAssetClass {
  return ValuationByAssetClassFromJSONTyped(json, false);
}

export function ValuationByAssetClassFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): ValuationByAssetClass {
  if (json === undefined || json === null) {
    return json;
  }
  return {
    valuationCcy: json["valuation_ccy"],
    byAssetClass: (json["by_asset_class"] as Array<any>).map(
      GroupValuationFromJSON,
    ),
  };
}

export function ValuationByAssetClassToJSON(
  value?: ValuationByAssetClass | null,
): any {
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  return {
    valuation_ccy: value.valuationCcy,
    by_asset_class: (value.byAssetClass as Array<any>).map(
      GroupValuationToJSON,
    ),
  };
}
