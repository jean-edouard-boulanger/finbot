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
 * @interface AppLoginRequest
 */
export interface AppLoginRequest {
  /**
   *
   * @type {string}
   * @memberof AppLoginRequest
   */
  email: string;
  /**
   *
   * @type {string}
   * @memberof AppLoginRequest
   */
  password: string;
}

/**
 * Check if a given object implements the AppLoginRequest interface.
 */
export function instanceOfAppLoginRequest(value: object): boolean {
  let isInstance = true;
  isInstance = isInstance && "email" in value;
  isInstance = isInstance && "password" in value;

  return isInstance;
}

export function AppLoginRequestFromJSON(json: any): AppLoginRequest {
  return AppLoginRequestFromJSONTyped(json, false);
}

export function AppLoginRequestFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): AppLoginRequest {
  if (json === undefined || json === null) {
    return json;
  }
  return {
    email: json["email"],
    password: json["password"],
  };
}

export function AppLoginRequestToJSON(value?: AppLoginRequest | null): any {
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  return {
    email: value.email,
    password: value.password,
  };
}
