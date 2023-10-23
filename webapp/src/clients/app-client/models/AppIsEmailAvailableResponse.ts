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
 * @interface AppIsEmailAvailableResponse
 */
export interface AppIsEmailAvailableResponse {
  /**
   *
   * @type {boolean}
   * @memberof AppIsEmailAvailableResponse
   */
  available: boolean;
}

/**
 * Check if a given object implements the AppIsEmailAvailableResponse interface.
 */
export function instanceOfAppIsEmailAvailableResponse(value: object): boolean {
  let isInstance = true;
  isInstance = isInstance && "available" in value;

  return isInstance;
}

export function AppIsEmailAvailableResponseFromJSON(
  json: any,
): AppIsEmailAvailableResponse {
  return AppIsEmailAvailableResponseFromJSONTyped(json, false);
}

export function AppIsEmailAvailableResponseFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): AppIsEmailAvailableResponse {
  if (json === undefined || json === null) {
    return json;
  }
  return {
    available: json["available"],
  };
}

export function AppIsEmailAvailableResponseToJSON(
  value?: AppIsEmailAvailableResponse | null,
): any {
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  return {
    available: value.available,
  };
}
