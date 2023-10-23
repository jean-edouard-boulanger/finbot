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
import type { UserAccountValuationSparklineEntry } from "./UserAccountValuationSparklineEntry";
import {
  UserAccountValuationSparklineEntryFromJSON,
  UserAccountValuationSparklineEntryFromJSONTyped,
  UserAccountValuationSparklineEntryToJSON,
} from "./UserAccountValuationSparklineEntry";
import type { ValuationChange } from "./ValuationChange";
import {
  ValuationChangeFromJSON,
  ValuationChangeFromJSONTyped,
  ValuationChangeToJSON,
} from "./ValuationChange";

/**
 *
 * @export
 * @interface UserAccountValuation
 */
export interface UserAccountValuation {
  /**
   *
   * @type {Date}
   * @memberof UserAccountValuation
   */
  date: Date;
  /**
   *
   * @type {string}
   * @memberof UserAccountValuation
   */
  currency: string;
  /**
   *
   * @type {number}
   * @memberof UserAccountValuation
   */
  value: number;
  /**
   *
   * @type {number}
   * @memberof UserAccountValuation
   */
  totalLiabilities: number;
  /**
   *
   * @type {ValuationChange}
   * @memberof UserAccountValuation
   */
  change: ValuationChange;
  /**
   *
   * @type {Array<UserAccountValuationSparklineEntry>}
   * @memberof UserAccountValuation
   */
  sparkline: Array<UserAccountValuationSparklineEntry>;
}

/**
 * Check if a given object implements the UserAccountValuation interface.
 */
export function instanceOfUserAccountValuation(value: object): boolean {
  let isInstance = true;
  isInstance = isInstance && "date" in value;
  isInstance = isInstance && "currency" in value;
  isInstance = isInstance && "value" in value;
  isInstance = isInstance && "totalLiabilities" in value;
  isInstance = isInstance && "change" in value;
  isInstance = isInstance && "sparkline" in value;

  return isInstance;
}

export function UserAccountValuationFromJSON(json: any): UserAccountValuation {
  return UserAccountValuationFromJSONTyped(json, false);
}

export function UserAccountValuationFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): UserAccountValuation {
  if (json === undefined || json === null) {
    return json;
  }
  return {
    date: new Date(json["date"]),
    currency: json["currency"],
    value: json["value"],
    totalLiabilities: json["total_liabilities"],
    change: ValuationChangeFromJSON(json["change"]),
    sparkline: (json["sparkline"] as Array<any>).map(
      UserAccountValuationSparklineEntryFromJSON,
    ),
  };
}

export function UserAccountValuationToJSON(
  value?: UserAccountValuation | null,
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
    total_liabilities: value.totalLiabilities,
    change: ValuationChangeToJSON(value.change),
    sparkline: (value.sparkline as Array<any>).map(
      UserAccountValuationSparklineEntryToJSON,
    ),
  };
}
