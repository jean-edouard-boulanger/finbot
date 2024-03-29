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
import type { UserAccount } from "./UserAccount";
import {
  UserAccountFromJSON,
  UserAccountFromJSONTyped,
  UserAccountToJSON,
} from "./UserAccount";

/**
 *
 * @export
 * @interface AppGetUserAccountResponse
 */
export interface AppGetUserAccountResponse {
  /**
   *
   * @type {UserAccount}
   * @memberof AppGetUserAccountResponse
   */
  userAccount: UserAccount;
}

/**
 * Check if a given object implements the AppGetUserAccountResponse interface.
 */
export function instanceOfAppGetUserAccountResponse(value: object): boolean {
  let isInstance = true;
  isInstance = isInstance && "userAccount" in value;

  return isInstance;
}

export function AppGetUserAccountResponseFromJSON(
  json: any,
): AppGetUserAccountResponse {
  return AppGetUserAccountResponseFromJSONTyped(json, false);
}

export function AppGetUserAccountResponseFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): AppGetUserAccountResponse {
  if (json === undefined || json === null) {
    return json;
  }
  return {
    userAccount: UserAccountFromJSON(json["user_account"]),
  };
}

export function AppGetUserAccountResponseToJSON(
  value?: AppGetUserAccountResponse | null,
): any {
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  return {
    user_account: UserAccountToJSON(value.userAccount),
  };
}
