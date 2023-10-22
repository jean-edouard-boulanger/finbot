/* tslint:disable */
/* eslint-disable */
/**
 * Finbot application service
 * API documentation for appwsrv
 *
 * The version of the OpenAPI document: v0.8.0
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
 * @interface AppUpdateLinkedAccountCredentialsRequest
 */
export interface AppUpdateLinkedAccountCredentialsRequest {
  /**
   *
   * @type {object}
   * @memberof AppUpdateLinkedAccountCredentialsRequest
   */
  credentials: object;
}

/**
 * Check if a given object implements the AppUpdateLinkedAccountCredentialsRequest interface.
 */
export function instanceOfAppUpdateLinkedAccountCredentialsRequest(
  value: object,
): boolean {
  let isInstance = true;
  isInstance = isInstance && "credentials" in value;

  return isInstance;
}

export function AppUpdateLinkedAccountCredentialsRequestFromJSON(
  json: any,
): AppUpdateLinkedAccountCredentialsRequest {
  return AppUpdateLinkedAccountCredentialsRequestFromJSONTyped(json, false);
}

export function AppUpdateLinkedAccountCredentialsRequestFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): AppUpdateLinkedAccountCredentialsRequest {
  if (json === undefined || json === null) {
    return json;
  }
  return {
    credentials: json["credentials"],
  };
}

export function AppUpdateLinkedAccountCredentialsRequestToJSON(
  value?: AppUpdateLinkedAccountCredentialsRequest | null,
): any {
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  return {
    credentials: value.credentials,
  };
}
