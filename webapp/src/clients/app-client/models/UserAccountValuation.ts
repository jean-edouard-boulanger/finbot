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
import type { ValuationChange } from "./ValuationChange";
import {
  ValuationChangeFromJSON,
  ValuationChangeFromJSONTyped,
  ValuationChangeToJSON,
  ValuationChangeToJSONTyped,
} from "./ValuationChange";
import type { UserAccountValuationSparklineEntry } from "./UserAccountValuationSparklineEntry";
import {
  UserAccountValuationSparklineEntryFromJSON,
  UserAccountValuationSparklineEntryFromJSONTyped,
  UserAccountValuationSparklineEntryToJSON,
  UserAccountValuationSparklineEntryToJSONTyped,
} from "./UserAccountValuationSparklineEntry";

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
export function instanceOfUserAccountValuation(
  value: object,
): value is UserAccountValuation {
  if (!("date" in value) || value["date"] === undefined) return false;
  if (!("currency" in value) || value["currency"] === undefined) return false;
  if (!("value" in value) || value["value"] === undefined) return false;
  if (!("totalLiabilities" in value) || value["totalLiabilities"] === undefined)
    return false;
  if (!("change" in value) || value["change"] === undefined) return false;
  if (!("sparkline" in value) || value["sparkline"] === undefined) return false;
  return true;
}

export function UserAccountValuationFromJSON(json: any): UserAccountValuation {
  return UserAccountValuationFromJSONTyped(json, false);
}

export function UserAccountValuationFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): UserAccountValuation {
  if (json == null) {
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

export function UserAccountValuationToJSON(json: any): UserAccountValuation {
  return UserAccountValuationToJSONTyped(json, false);
}

export function UserAccountValuationToJSONTyped(
  value?: UserAccountValuation | null,
  ignoreDiscriminator: boolean = false,
): any {
  if (value == null) {
    return value;
  }

  return {
    date: value["date"].toISOString(),
    currency: value["currency"],
    value: value["value"],
    total_liabilities: value["totalLiabilities"],
    change: ValuationChangeToJSON(value["change"]),
    sparkline: (value["sparkline"] as Array<any>).map(
      UserAccountValuationSparklineEntryToJSON,
    ),
  };
}
