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
import type { ValuationChange } from "./ValuationChange";
import {
  ValuationChangeFromJSON,
  ValuationChangeFromJSONTyped,
  ValuationChangeToJSON,
} from "./ValuationChange";

/**
 *
 * @export
 * @interface LinkedAccountValuation
 */
export interface LinkedAccountValuation {
  /**
   *
   * @type {Date}
   * @memberof LinkedAccountValuation
   */
  date: Date;
  /**
   *
   * @type {string}
   * @memberof LinkedAccountValuation
   */
  currency: string;
  /**
   *
   * @type {number}
   * @memberof LinkedAccountValuation
   */
  value: number;
  /**
   *
   * @type {ValuationChange}
   * @memberof LinkedAccountValuation
   */
  change: ValuationChange;
}

/**
 * Check if a given object implements the LinkedAccountValuation interface.
 */
export function instanceOfLinkedAccountValuation(value: object): boolean {
  let isInstance = true;
  isInstance = isInstance && "date" in value;
  isInstance = isInstance && "currency" in value;
  isInstance = isInstance && "value" in value;
  isInstance = isInstance && "change" in value;

  return isInstance;
}

export function LinkedAccountValuationFromJSON(
  json: any,
): LinkedAccountValuation {
  return LinkedAccountValuationFromJSONTyped(json, false);
}

export function LinkedAccountValuationFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): LinkedAccountValuation {
  if (json === undefined || json === null) {
    return json;
  }
  return {
    date: new Date(json["date"]),
    currency: json["currency"],
    value: json["value"],
    change: ValuationChangeFromJSON(json["change"]),
  };
}

export function LinkedAccountValuationToJSON(
  value?: LinkedAccountValuation | null,
): any {
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  return {
    date: value.date.toISOString(),
    currency: value.currency,
    value: value.value,
    change: ValuationChangeToJSON(value.change),
  };
}
