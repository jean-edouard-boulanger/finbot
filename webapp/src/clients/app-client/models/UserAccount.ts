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
 * @interface UserAccount
 */
export interface UserAccount {
  /**
   *
   * @type {number}
   * @memberof UserAccount
   */
  id: number;
  /**
   *
   * @type {string}
   * @memberof UserAccount
   */
  email: string;
  /**
   *
   * @type {string}
   * @memberof UserAccount
   */
  fullName: string;
  /**
   *
   * @type {string}
   * @memberof UserAccount
   */
  mobilePhoneNumber?: string;
  /**
   *
   * @type {Date}
   * @memberof UserAccount
   */
  createdAt: Date;
  /**
   *
   * @type {Date}
   * @memberof UserAccount
   */
  updatedAt?: Date;
}

/**
 * Check if a given object implements the UserAccount interface.
 */
export function instanceOfUserAccount(value: object): boolean {
  let isInstance = true;
  isInstance = isInstance && "id" in value;
  isInstance = isInstance && "email" in value;
  isInstance = isInstance && "fullName" in value;
  isInstance = isInstance && "createdAt" in value;

  return isInstance;
}

export function UserAccountFromJSON(json: any): UserAccount {
  return UserAccountFromJSONTyped(json, false);
}

export function UserAccountFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): UserAccount {
  if (json === undefined || json === null) {
    return json;
  }
  return {
    id: json["id"],
    email: json["email"],
    fullName: json["full_name"],
    mobilePhoneNumber: !exists(json, "mobile_phone_number")
      ? undefined
      : json["mobile_phone_number"],
    createdAt: new Date(json["created_at"]),
    updatedAt: !exists(json, "updated_at")
      ? undefined
      : new Date(json["updated_at"]),
  };
}

export function UserAccountToJSON(value?: UserAccount | null): any {
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  return {
    id: value.id,
    email: value.email,
    full_name: value.fullName,
    mobile_phone_number: value.mobilePhoneNumber,
    created_at: value.createdAt.toISOString(),
    updated_at:
      value.updatedAt === undefined ? undefined : value.updatedAt.toISOString(),
  };
}
