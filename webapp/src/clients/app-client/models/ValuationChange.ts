/* tslint:disable */
/* eslint-disable */
/**
 * Finbot application service
 * API documentation for appwsrv
 *
 * The version of the OpenAPI document: v0.8.1
 *
 *
 * NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).
 * https://openapi-generator.tech
 * Do not edit the class manually.
 */

import { exists, mapValues } from "../runtime";
/**
 *
 * @export
 * @interface ValuationChange
 */
export interface ValuationChange {
  /**
   *
   * @type {number}
   * @memberof ValuationChange
   */
  change1hour?: number;
  /**
   *
   * @type {number}
   * @memberof ValuationChange
   */
  change1day?: number;
  /**
   *
   * @type {number}
   * @memberof ValuationChange
   */
  change1week?: number;
  /**
   *
   * @type {number}
   * @memberof ValuationChange
   */
  change1month?: number;
  /**
   *
   * @type {number}
   * @memberof ValuationChange
   */
  change6months?: number;
  /**
   *
   * @type {number}
   * @memberof ValuationChange
   */
  change1year?: number;
  /**
   *
   * @type {number}
   * @memberof ValuationChange
   */
  change2years?: number;
}

/**
 * Check if a given object implements the ValuationChange interface.
 */
export function instanceOfValuationChange(value: object): boolean {
  let isInstance = true;

  return isInstance;
}

export function ValuationChangeFromJSON(json: any): ValuationChange {
  return ValuationChangeFromJSONTyped(json, false);
}

export function ValuationChangeFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): ValuationChange {
  if (json === undefined || json === null) {
    return json;
  }
  return {
    change1hour: !exists(json, "change_1hour")
      ? undefined
      : json["change_1hour"],
    change1day: !exists(json, "change_1day") ? undefined : json["change_1day"],
    change1week: !exists(json, "change_1week")
      ? undefined
      : json["change_1week"],
    change1month: !exists(json, "change_1month")
      ? undefined
      : json["change_1month"],
    change6months: !exists(json, "change_6months")
      ? undefined
      : json["change_6months"],
    change1year: !exists(json, "change_1year")
      ? undefined
      : json["change_1year"],
    change2years: !exists(json, "change_2years")
      ? undefined
      : json["change_2years"],
  };
}

export function ValuationChangeToJSON(value?: ValuationChange | null): any {
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  return {
    change_1hour: value.change1hour,
    change_1day: value.change1day,
    change_1week: value.change1week,
    change_1month: value.change1month,
    change_6months: value.change6months,
    change_1year: value.change1year,
    change_2years: value.change2years,
  };
}
