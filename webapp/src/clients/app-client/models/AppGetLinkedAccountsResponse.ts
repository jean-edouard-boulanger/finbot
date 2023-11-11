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
import type { LinkedAccount } from "./LinkedAccount";
import {
  LinkedAccountFromJSON,
  LinkedAccountFromJSONTyped,
  LinkedAccountToJSON,
} from "./LinkedAccount";

/**
 *
 * @export
 * @interface AppGetLinkedAccountsResponse
 */
export interface AppGetLinkedAccountsResponse {
  /**
   *
   * @type {Array<LinkedAccount>}
   * @memberof AppGetLinkedAccountsResponse
   */
  linkedAccounts: Array<LinkedAccount>;
}

/**
 * Check if a given object implements the AppGetLinkedAccountsResponse interface.
 */
export function instanceOfAppGetLinkedAccountsResponse(value: object): boolean {
  let isInstance = true;
  isInstance = isInstance && "linkedAccounts" in value;

  return isInstance;
}

export function AppGetLinkedAccountsResponseFromJSON(
  json: any,
): AppGetLinkedAccountsResponse {
  return AppGetLinkedAccountsResponseFromJSONTyped(json, false);
}

export function AppGetLinkedAccountsResponseFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): AppGetLinkedAccountsResponse {
  if (json === undefined || json === null) {
    return json;
  }
  return {
    linkedAccounts: (json["linked_accounts"] as Array<any>).map(
      LinkedAccountFromJSON,
    ),
  };
}

export function AppGetLinkedAccountsResponseToJSON(
  value?: AppGetLinkedAccountsResponse | null,
): any {
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  return {
    linked_accounts: (value.linkedAccounts as Array<any>).map(
      LinkedAccountToJSON,
    ),
  };
}