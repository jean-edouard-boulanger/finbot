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
 * @interface AppUpdateUserAccountProfileRequest
 */
export interface AppUpdateUserAccountProfileRequest {
  /**
   *
   * @type {string}
   * @memberof AppUpdateUserAccountProfileRequest
   */
  email: string;
  /**
   *
   * @type {string}
   * @memberof AppUpdateUserAccountProfileRequest
   */
  fullName: string;
  /**
   *
   * @type {string}
   * @memberof AppUpdateUserAccountProfileRequest
   */
  mobilePhoneNumber?: string;
}

/**
 * Check if a given object implements the AppUpdateUserAccountProfileRequest interface.
 */
export function instanceOfAppUpdateUserAccountProfileRequest(
  value: object,
): boolean {
  let isInstance = true;
  isInstance = isInstance && "email" in value;
  isInstance = isInstance && "fullName" in value;

  return isInstance;
}

export function AppUpdateUserAccountProfileRequestFromJSON(
  json: any,
): AppUpdateUserAccountProfileRequest {
  return AppUpdateUserAccountProfileRequestFromJSONTyped(json, false);
}

export function AppUpdateUserAccountProfileRequestFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): AppUpdateUserAccountProfileRequest {
  if (json === undefined || json === null) {
    return json;
  }
  return {
    email: json["email"],
    fullName: json["full_name"],
    mobilePhoneNumber: !exists(json, "mobile_phone_number")
      ? undefined
      : json["mobile_phone_number"],
  };
}

export function AppUpdateUserAccountProfileRequestToJSON(
  value?: AppUpdateUserAccountProfileRequest | null,
): any {
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  return {
    email: value.email,
    full_name: value.fullName,
    mobile_phone_number: value.mobilePhoneNumber,
  };
}
