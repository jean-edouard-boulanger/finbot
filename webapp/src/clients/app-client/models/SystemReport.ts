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
/**
 *
 * @export
 * @interface SystemReport
 */
export interface SystemReport {
  /**
   *
   * @type {string}
   * @memberof SystemReport
   */
  finbotVersion: string;
  /**
   *
   * @type {string}
   * @memberof SystemReport
   */
  finbotApiVersion: string;
  /**
   *
   * @type {string}
   * @memberof SystemReport
   */
  runtime: string;
}

/**
 * Check if a given object implements the SystemReport interface.
 */
export function instanceOfSystemReport(value: object): boolean {
  let isInstance = true;
  isInstance = isInstance && "finbotVersion" in value;
  isInstance = isInstance && "finbotApiVersion" in value;
  isInstance = isInstance && "runtime" in value;

  return isInstance;
}

export function SystemReportFromJSON(json: any): SystemReport {
  return SystemReportFromJSONTyped(json, false);
}

export function SystemReportFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): SystemReport {
  if (json === undefined || json === null) {
    return json;
  }
  return {
    finbotVersion: json["finbot_version"],
    finbotApiVersion: json["finbot_api_version"],
    runtime: json["runtime"],
  };
}

export function SystemReportToJSON(value?: SystemReport | null): any {
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  return {
    finbot_version: value.finbotVersion,
    finbot_api_version: value.finbotApiVersion,
    runtime: value.runtime,
  };
}
