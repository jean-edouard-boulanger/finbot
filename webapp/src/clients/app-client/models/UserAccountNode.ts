/* tslint:disable */
/* eslint-disable */
/**
 * Finbot application service
 * API documentation for appwsrv
 *
 * The version of the OpenAPI document: v0.8.1
 *
 *
 * NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).
 * https://openapi-generator.tech
 * Do not edit the class manually.
 */

import { exists, mapValues } from "../runtime";
import type { LinkedAccountNode } from "./LinkedAccountNode";
import {
  LinkedAccountNodeFromJSON,
  LinkedAccountNodeFromJSONTyped,
  LinkedAccountNodeToJSON,
} from "./LinkedAccountNode";
import type { ValuationWithSparkline } from "./ValuationWithSparkline";
import {
  ValuationWithSparklineFromJSON,
  ValuationWithSparklineFromJSONTyped,
  ValuationWithSparklineToJSON,
} from "./ValuationWithSparkline";

/**
 *
 * @export
 * @interface UserAccountNode
 */
export interface UserAccountNode {
  /**
   *
   * @type {string}
   * @memberof UserAccountNode
   */
  role?: UserAccountNodeRoleEnum;
  /**
   *
   * @type {ValuationWithSparkline}
   * @memberof UserAccountNode
   */
  valuation: ValuationWithSparkline;
  /**
   *
   * @type {Array<LinkedAccountNode>}
   * @memberof UserAccountNode
   */
  children: Array<LinkedAccountNode>;
}

/**
 * @export
 */
export const UserAccountNodeRoleEnum = {
  UserAccount: "user_account",
} as const;
export type UserAccountNodeRoleEnum =
  (typeof UserAccountNodeRoleEnum)[keyof typeof UserAccountNodeRoleEnum];

/**
 * Check if a given object implements the UserAccountNode interface.
 */
export function instanceOfUserAccountNode(value: object): boolean {
  let isInstance = true;
  isInstance = isInstance && "valuation" in value;
  isInstance = isInstance && "children" in value;

  return isInstance;
}

export function UserAccountNodeFromJSON(json: any): UserAccountNode {
  return UserAccountNodeFromJSONTyped(json, false);
}

export function UserAccountNodeFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): UserAccountNode {
  if (json === undefined || json === null) {
    return json;
  }
  return {
    role: !exists(json, "role") ? undefined : json["role"],
    valuation: ValuationWithSparklineFromJSON(json["valuation"]),
    children: (json["children"] as Array<any>).map(LinkedAccountNodeFromJSON),
  };
}

export function UserAccountNodeToJSON(value?: UserAccountNode | null): any {
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  return {
    role: value.role,
    valuation: ValuationWithSparklineToJSON(value.valuation),
    children: (value.children as Array<any>).map(LinkedAccountNodeToJSON),
  };
}
