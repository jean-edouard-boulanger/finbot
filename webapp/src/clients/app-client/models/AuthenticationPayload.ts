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
 * @interface AuthenticationPayload
 */
export interface AuthenticationPayload {
  /**
   *
   * @type {string}
   * @memberof AuthenticationPayload
   */
  accessToken: string;
  /**
   *
   * @type {string}
   * @memberof AuthenticationPayload
   */
  refreshToken: string;
}

/**
 * Check if a given object implements the AuthenticationPayload interface.
 */
export function instanceOfAuthenticationPayload(value: object): boolean {
  let isInstance = true;
  isInstance = isInstance && "accessToken" in value;
  isInstance = isInstance && "refreshToken" in value;

  return isInstance;
}

export function AuthenticationPayloadFromJSON(
  json: any,
): AuthenticationPayload {
  return AuthenticationPayloadFromJSONTyped(json, false);
}

export function AuthenticationPayloadFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): AuthenticationPayload {
  if (json === undefined || json === null) {
    return json;
  }
  return {
    accessToken: json["access_token"],
    refreshToken: json["refresh_token"],
  };
}

export function AuthenticationPayloadToJSON(
  value?: AuthenticationPayload | null,
): any {
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  return {
    access_token: value.accessToken,
    refresh_token: value.refreshToken,
  };
}