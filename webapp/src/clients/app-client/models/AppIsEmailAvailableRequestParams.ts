/* tslint:disable */
/* eslint-disable */
/**
 * Finbot application service
 * API documentation for appwsrv
 *
 * The version of the OpenAPI document: v0.0.2
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
 * @interface AppIsEmailAvailableRequestParams
 */
export interface AppIsEmailAvailableRequestParams {
  /**
   *
   * @type {string}
   * @memberof AppIsEmailAvailableRequestParams
   */
  email: string;
}

/**
 * Check if a given object implements the AppIsEmailAvailableRequestParams interface.
 */
export function instanceOfAppIsEmailAvailableRequestParams(
  value: object,
): boolean {
  let isInstance = true;
  isInstance = isInstance && "email" in value;

  return isInstance;
}

export function AppIsEmailAvailableRequestParamsFromJSON(
  json: any,
): AppIsEmailAvailableRequestParams {
  return AppIsEmailAvailableRequestParamsFromJSONTyped(json, false);
}

export function AppIsEmailAvailableRequestParamsFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): AppIsEmailAvailableRequestParams {
  if (json === undefined || json === null) {
    return json;
  }
  return {
    email: json["email"],
  };
}

export function AppIsEmailAvailableRequestParamsToJSON(
  value?: AppIsEmailAvailableRequestParams | null,
): any {
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  return {
    email: value.email,
  };
}