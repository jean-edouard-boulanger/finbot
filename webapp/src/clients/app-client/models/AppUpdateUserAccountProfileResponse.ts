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
import type { UserAccountProfile } from "./UserAccountProfile";
import {
  UserAccountProfileFromJSON,
  UserAccountProfileFromJSONTyped,
  UserAccountProfileToJSON,
} from "./UserAccountProfile";

/**
 *
 * @export
 * @interface AppUpdateUserAccountProfileResponse
 */
export interface AppUpdateUserAccountProfileResponse {
  /**
   *
   * @type {UserAccountProfile}
   * @memberof AppUpdateUserAccountProfileResponse
   */
  profile: UserAccountProfile;
}

/**
 * Check if a given object implements the AppUpdateUserAccountProfileResponse interface.
 */
export function instanceOfAppUpdateUserAccountProfileResponse(
  value: object,
): boolean {
  let isInstance = true;
  isInstance = isInstance && "profile" in value;

  return isInstance;
}

export function AppUpdateUserAccountProfileResponseFromJSON(
  json: any,
): AppUpdateUserAccountProfileResponse {
  return AppUpdateUserAccountProfileResponseFromJSONTyped(json, false);
}

export function AppUpdateUserAccountProfileResponseFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): AppUpdateUserAccountProfileResponse {
  if (json === undefined || json === null) {
    return json;
  }
  return {
    profile: UserAccountProfileFromJSON(json["profile"]),
  };
}

export function AppUpdateUserAccountProfileResponseToJSON(
  value?: AppUpdateUserAccountProfileResponse | null,
): any {
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  return {
    profile: UserAccountProfileToJSON(value.profile),
  };
}
