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
import type { Metrics } from "./Metrics";
import {
  MetricsFromJSON,
  MetricsFromJSONTyped,
  MetricsToJSON,
} from "./Metrics";
import type { ReportEntry } from "./ReportEntry";
import {
  ReportEntryFromJSON,
  ReportEntryFromJSONTyped,
  ReportEntryToJSON,
} from "./ReportEntry";

/**
 *
 * @export
 * @interface EarningsReport
 */
export interface EarningsReport {
  /**
   *
   * @type {string}
   * @memberof EarningsReport
   */
  currency: string;
  /**
   *
   * @type {Array<ReportEntry>}
   * @memberof EarningsReport
   */
  entries: Array<ReportEntry>;
  /**
   *
   * @type {Metrics}
   * @memberof EarningsReport
   */
  rollup: Metrics;
}

/**
 * Check if a given object implements the EarningsReport interface.
 */
export function instanceOfEarningsReport(value: object): boolean {
  let isInstance = true;
  isInstance = isInstance && "currency" in value;
  isInstance = isInstance && "entries" in value;
  isInstance = isInstance && "rollup" in value;

  return isInstance;
}

export function EarningsReportFromJSON(json: any): EarningsReport {
  return EarningsReportFromJSONTyped(json, false);
}

export function EarningsReportFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): EarningsReport {
  if (json === undefined || json === null) {
    return json;
  }
  return {
    currency: json["currency"],
    entries: (json["entries"] as Array<any>).map(ReportEntryFromJSON),
    rollup: MetricsFromJSON(json["rollup"]),
  };
}

export function EarningsReportToJSON(value?: EarningsReport | null): any {
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  return {
    currency: value.currency,
    entries: (value.entries as Array<any>).map(ReportEntryToJSON),
    rollup: MetricsToJSON(value.rollup),
  };
}
