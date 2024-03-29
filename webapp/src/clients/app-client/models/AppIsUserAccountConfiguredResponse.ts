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
 * @interface AppIsUserAccountConfiguredResponse
 */
export interface AppIsUserAccountConfiguredResponse {
  /**
   *
   * @type {boolean}
   * @memberof AppIsUserAccountConfiguredResponse
   */
  configured: boolean;
}

/**
 * Check if a given object implements the AppIsUserAccountConfiguredResponse interface.
 */
export function instanceOfAppIsUserAccountConfiguredResponse(
  value: object,
): boolean {
  let isInstance = true;
  isInstance = isInstance && "configured" in value;

  return isInstance;
}

export function AppIsUserAccountConfiguredResponseFromJSON(
  json: any,
): AppIsUserAccountConfiguredResponse {
  return AppIsUserAccountConfiguredResponseFromJSONTyped(json, false);
}

export function AppIsUserAccountConfiguredResponseFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): AppIsUserAccountConfiguredResponse {
  if (json === undefined || json === null) {
    return json;
  }
  return {
    configured: json["configured"],
  };
}

export function AppIsUserAccountConfiguredResponseToJSON(
  value?: AppIsUserAccountConfiguredResponse | null,
): any {
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  return {
    configured: value.configured,
  };
}
