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
): value is AppIsUserAccountConfiguredResponse {
  if (!("configured" in value) || value["configured"] === undefined)
    return false;
  return true;
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
  if (json == null) {
    return json;
  }
  return {
    configured: json["configured"],
  };
}

export function AppIsUserAccountConfiguredResponseToJSON(
  value?: AppIsUserAccountConfiguredResponse | null,
): any {
  if (value == null) {
    return value;
  }
  return {
    configured: value["configured"],
  };
}
