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
export function instanceOfAppIsEmailAvailableResponse(
  value: object,
): value is AppIsEmailAvailableResponse {
  if (!("available" in value) || value["available"] === undefined) return false;
  return true;
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
  if (json == null) {
    return json;
  }
  return {
    available: json["available"],
  };
}

export function AppIsEmailAvailableResponseToJSON(
  value?: AppIsEmailAvailableResponse | null,
): any {
  if (value == null) {
    return value;
  }
  return {
    available: value["available"],
  };
}
