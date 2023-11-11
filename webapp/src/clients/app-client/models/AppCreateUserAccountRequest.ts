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
import type { UserAccountCreationSettings } from "./UserAccountCreationSettings";
import {
  UserAccountCreationSettingsFromJSON,
  UserAccountCreationSettingsFromJSONTyped,
  UserAccountCreationSettingsToJSON,
} from "./UserAccountCreationSettings";

/**
 *
 * @export
 * @interface AppCreateUserAccountRequest
 */
export interface AppCreateUserAccountRequest {
  /**
   *
   * @type {string}
   * @memberof AppCreateUserAccountRequest
   */
  email: string;
  /**
   *
   * @type {string}
   * @memberof AppCreateUserAccountRequest
   */
  password: string;
  /**
   *
   * @type {string}
   * @memberof AppCreateUserAccountRequest
   */
  fullName: string;
  /**
   *
   * @type {UserAccountCreationSettings}
   * @memberof AppCreateUserAccountRequest
   */
  settings: UserAccountCreationSettings;
}

/**
 * Check if a given object implements the AppCreateUserAccountRequest interface.
 */
export function instanceOfAppCreateUserAccountRequest(value: object): boolean {
  let isInstance = true;
  isInstance = isInstance && "email" in value;
  isInstance = isInstance && "password" in value;
  isInstance = isInstance && "fullName" in value;
  isInstance = isInstance && "settings" in value;

  return isInstance;
}

export function AppCreateUserAccountRequestFromJSON(
  json: any,
): AppCreateUserAccountRequest {
  return AppCreateUserAccountRequestFromJSONTyped(json, false);
}

export function AppCreateUserAccountRequestFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): AppCreateUserAccountRequest {
  if (json === undefined || json === null) {
    return json;
  }
  return {
    email: json["email"],
    password: json["password"],
    fullName: json["full_name"],
    settings: UserAccountCreationSettingsFromJSON(json["settings"]),
  };
}

export function AppCreateUserAccountRequestToJSON(
  value?: AppCreateUserAccountRequest | null,
): any {
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  return {
    email: value.email,
    password: value.password,
    full_name: value.fullName,
    settings: UserAccountCreationSettingsToJSON(value.settings),
  };
}