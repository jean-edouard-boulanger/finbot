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
  /**
   *
   * @type {boolean}
   * @memberof SystemReport
   */
  isDemo: boolean;
}

/**
 * Check if a given object implements the SystemReport interface.
 */
export function instanceOfSystemReport(value: object): value is SystemReport {
  if (!("finbotVersion" in value) || value["finbotVersion"] === undefined)
    return false;
  if (!("finbotApiVersion" in value) || value["finbotApiVersion"] === undefined)
    return false;
  if (!("runtime" in value) || value["runtime"] === undefined) return false;
  if (!("isDemo" in value) || value["isDemo"] === undefined) return false;
  return true;
}

export function SystemReportFromJSON(json: any): SystemReport {
  return SystemReportFromJSONTyped(json, false);
}

export function SystemReportFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): SystemReport {
  if (json == null) {
    return json;
  }
  return {
    finbotVersion: json["finbot_version"],
    finbotApiVersion: json["finbot_api_version"],
    runtime: json["runtime"],
    isDemo: json["is_demo"],
  };
}

export function SystemReportToJSON(value?: SystemReport | null): any {
  if (value == null) {
    return value;
  }
  return {
    finbot_version: value["finbotVersion"],
    finbot_api_version: value["finbotApiVersion"],
    runtime: value["runtime"],
    is_demo: value["isDemo"],
  };
}
