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
export function instanceOfValuationChange(
  value: object,
): value is ValuationChange {
  return true;
}

export function ValuationChangeFromJSON(json: any): ValuationChange {
  return ValuationChangeFromJSONTyped(json, false);
}

export function ValuationChangeFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): ValuationChange {
  if (json == null) {
    return json;
  }
  return {
    change1hour:
      json["change_1hour"] == null ? undefined : json["change_1hour"],
    change1day: json["change_1day"] == null ? undefined : json["change_1day"],
    change1week:
      json["change_1week"] == null ? undefined : json["change_1week"],
    change1month:
      json["change_1month"] == null ? undefined : json["change_1month"],
    change6months:
      json["change_6months"] == null ? undefined : json["change_6months"],
    change1year:
      json["change_1year"] == null ? undefined : json["change_1year"],
    change2years:
      json["change_2years"] == null ? undefined : json["change_2years"],
  };
}

export function ValuationChangeToJSON(value?: ValuationChange | null): any {
  if (value == null) {
    return value;
  }
  return {
    change_1hour: value["change1hour"],
    change_1day: value["change1day"],
    change_1week: value["change1week"],
    change_1month: value["change1month"],
    change_6months: value["change6months"],
    change_1year: value["change1year"],
    change_2years: value["change2years"],
  };
}
