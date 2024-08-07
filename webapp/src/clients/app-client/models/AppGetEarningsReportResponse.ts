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
import type { EarningsReport } from "./EarningsReport";
import {
  EarningsReportFromJSON,
  EarningsReportFromJSONTyped,
  EarningsReportToJSON,
} from "./EarningsReport";

/**
 *
 * @export
 * @interface AppGetEarningsReportResponse
 */
export interface AppGetEarningsReportResponse {
  /**
   *
   * @type {EarningsReport}
   * @memberof AppGetEarningsReportResponse
   */
  report: EarningsReport;
}

/**
 * Check if a given object implements the AppGetEarningsReportResponse interface.
 */
export function instanceOfAppGetEarningsReportResponse(
  value: object,
): value is AppGetEarningsReportResponse {
  if (!("report" in value) || value["report"] === undefined) return false;
  return true;
}

export function AppGetEarningsReportResponseFromJSON(
  json: any,
): AppGetEarningsReportResponse {
  return AppGetEarningsReportResponseFromJSONTyped(json, false);
}

export function AppGetEarningsReportResponseFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): AppGetEarningsReportResponse {
  if (json == null) {
    return json;
  }
  return {
    report: EarningsReportFromJSON(json["report"]),
  };
}

export function AppGetEarningsReportResponseToJSON(
  value?: AppGetEarningsReportResponse | null,
): any {
  if (value == null) {
    return value;
  }
  return {
    report: EarningsReportToJSON(value["report"]),
  };
}
