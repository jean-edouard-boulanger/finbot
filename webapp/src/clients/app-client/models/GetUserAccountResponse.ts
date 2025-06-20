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
import type { UserAccount } from "./UserAccount";
import {
  UserAccountFromJSON,
  UserAccountFromJSONTyped,
  UserAccountToJSON,
  UserAccountToJSONTyped,
} from "./UserAccount";

/**
 *
 * @export
 * @interface GetUserAccountResponse
 */
export interface GetUserAccountResponse {
  /**
   *
   * @type {UserAccount}
   * @memberof GetUserAccountResponse
   */
  userAccount: UserAccount;
}

/**
 * Check if a given object implements the GetUserAccountResponse interface.
 */
export function instanceOfGetUserAccountResponse(
  value: object,
): value is GetUserAccountResponse {
  if (!("userAccount" in value) || value["userAccount"] === undefined)
    return false;
  return true;
}

export function GetUserAccountResponseFromJSON(
  json: any,
): GetUserAccountResponse {
  return GetUserAccountResponseFromJSONTyped(json, false);
}

export function GetUserAccountResponseFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): GetUserAccountResponse {
  if (json == null) {
    return json;
  }
  return {
    userAccount: UserAccountFromJSON(json["user_account"]),
  };
}

export function GetUserAccountResponseToJSON(
  json: any,
): GetUserAccountResponse {
  return GetUserAccountResponseToJSONTyped(json, false);
}

export function GetUserAccountResponseToJSONTyped(
  value?: GetUserAccountResponse | null,
  ignoreDiscriminator: boolean = false,
): any {
  if (value == null) {
    return value;
  }

  return {
    user_account: UserAccountToJSON(value["userAccount"]),
  };
}
