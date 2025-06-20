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
import type { GroupValuation } from "./GroupValuation";
import {
  GroupValuationFromJSON,
  GroupValuationFromJSONTyped,
  GroupValuationToJSON,
  GroupValuationToJSONTyped,
} from "./GroupValuation";

/**
 *
 * @export
 * @interface ValuationByCurrencyExposure
 */
export interface ValuationByCurrencyExposure {
  /**
   *
   * @type {string}
   * @memberof ValuationByCurrencyExposure
   */
  valuationCcy: string;
  /**
   *
   * @type {Array<GroupValuation>}
   * @memberof ValuationByCurrencyExposure
   */
  byCurrencyExposure: Array<GroupValuation>;
}

/**
 * Check if a given object implements the ValuationByCurrencyExposure interface.
 */
export function instanceOfValuationByCurrencyExposure(
  value: object,
): value is ValuationByCurrencyExposure {
  if (!("valuationCcy" in value) || value["valuationCcy"] === undefined)
    return false;
  if (
    !("byCurrencyExposure" in value) ||
    value["byCurrencyExposure"] === undefined
  )
    return false;
  return true;
}

export function ValuationByCurrencyExposureFromJSON(
  json: any,
): ValuationByCurrencyExposure {
  return ValuationByCurrencyExposureFromJSONTyped(json, false);
}

export function ValuationByCurrencyExposureFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): ValuationByCurrencyExposure {
  if (json == null) {
    return json;
  }
  return {
    valuationCcy: json["valuation_ccy"],
    byCurrencyExposure: (json["by_currency_exposure"] as Array<any>).map(
      GroupValuationFromJSON,
    ),
  };
}

export function ValuationByCurrencyExposureToJSON(
  json: any,
): ValuationByCurrencyExposure {
  return ValuationByCurrencyExposureToJSONTyped(json, false);
}

export function ValuationByCurrencyExposureToJSONTyped(
  value?: ValuationByCurrencyExposure | null,
  ignoreDiscriminator: boolean = false,
): any {
  if (value == null) {
    return value;
  }

  return {
    valuation_ccy: value["valuationCcy"],
    by_currency_exposure: (value["byCurrencyExposure"] as Array<any>).map(
      GroupValuationToJSON,
    ),
  };
}
