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
import type { LinkedAccountValuationEntry } from "./LinkedAccountValuationEntry";
import {
  LinkedAccountValuationEntryFromJSON,
  LinkedAccountValuationEntryFromJSONTyped,
  LinkedAccountValuationEntryToJSON,
} from "./LinkedAccountValuationEntry";

/**
 *
 * @export
 * @interface LinkedAccountsValuation
 */
export interface LinkedAccountsValuation {
  /**
   *
   * @type {string}
   * @memberof LinkedAccountsValuation
   */
  valuationCcy: string;
  /**
   *
   * @type {Array<LinkedAccountValuationEntry>}
   * @memberof LinkedAccountsValuation
   */
  entries: Array<LinkedAccountValuationEntry>;
}

/**
 * Check if a given object implements the LinkedAccountsValuation interface.
 */
export function instanceOfLinkedAccountsValuation(
  value: object,
): value is LinkedAccountsValuation {
  if (!("valuationCcy" in value) || value["valuationCcy"] === undefined)
    return false;
  if (!("entries" in value) || value["entries"] === undefined) return false;
  return true;
}

export function LinkedAccountsValuationFromJSON(
  json: any,
): LinkedAccountsValuation {
  return LinkedAccountsValuationFromJSONTyped(json, false);
}

export function LinkedAccountsValuationFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): LinkedAccountsValuation {
  if (json == null) {
    return json;
  }
  return {
    valuationCcy: json["valuation_ccy"],
    entries: (json["entries"] as Array<any>).map(
      LinkedAccountValuationEntryFromJSON,
    ),
  };
}

export function LinkedAccountsValuationToJSON(
  value?: LinkedAccountsValuation | null,
): any {
  if (value == null) {
    return value;
  }
  return {
    valuation_ccy: value["valuationCcy"],
    entries: (value["entries"] as Array<any>).map(
      LinkedAccountValuationEntryToJSON,
    ),
  };
}
