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
import type { SubAccountItemNode } from "./SubAccountItemNode";
import {
  SubAccountItemNodeFromJSON,
  SubAccountItemNodeFromJSONTyped,
  SubAccountItemNodeToJSON,
} from "./SubAccountItemNode";
import type { Valuation } from "./Valuation";
import {
  ValuationFromJSON,
  ValuationFromJSONTyped,
  ValuationToJSON,
} from "./Valuation";
import type { SubAccountDescription } from "./SubAccountDescription";
import {
  SubAccountDescriptionFromJSON,
  SubAccountDescriptionFromJSONTyped,
  SubAccountDescriptionToJSON,
} from "./SubAccountDescription";

/**
 *
 * @export
 * @interface SubAccountNode
 */
export interface SubAccountNode {
  /**
   *
   * @type {string}
   * @memberof SubAccountNode
   */
  role?: SubAccountNodeRoleEnum;
  /**
   *
   * @type {SubAccountDescription}
   * @memberof SubAccountNode
   */
  subAccount: SubAccountDescription;
  /**
   *
   * @type {Valuation}
   * @memberof SubAccountNode
   */
  valuation: Valuation;
  /**
   *
   * @type {Array<SubAccountItemNode>}
   * @memberof SubAccountNode
   */
  children: Array<SubAccountItemNode>;
}

/**
 * @export
 */
export const SubAccountNodeRoleEnum = {
  SubAccount: "sub_account",
} as const;
export type SubAccountNodeRoleEnum =
  (typeof SubAccountNodeRoleEnum)[keyof typeof SubAccountNodeRoleEnum];

/**
 * Check if a given object implements the SubAccountNode interface.
 */
export function instanceOfSubAccountNode(
  value: object,
): value is SubAccountNode {
  if (!("subAccount" in value) || value["subAccount"] === undefined)
    return false;
  if (!("valuation" in value) || value["valuation"] === undefined) return false;
  if (!("children" in value) || value["children"] === undefined) return false;
  return true;
}

export function SubAccountNodeFromJSON(json: any): SubAccountNode {
  return SubAccountNodeFromJSONTyped(json, false);
}

export function SubAccountNodeFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): SubAccountNode {
  if (json == null) {
    return json;
  }
  return {
    role: json["role"] == null ? undefined : json["role"],
    subAccount: SubAccountDescriptionFromJSON(json["sub_account"]),
    valuation: ValuationFromJSON(json["valuation"]),
    children: (json["children"] as Array<any>).map(SubAccountItemNodeFromJSON),
  };
}

export function SubAccountNodeToJSON(value?: SubAccountNode | null): any {
  if (value == null) {
    return value;
  }
  return {
    role: value["role"],
    sub_account: SubAccountDescriptionToJSON(value["subAccount"]),
    valuation: ValuationToJSON(value["valuation"]),
    children: (value["children"] as Array<any>).map(SubAccountItemNodeToJSON),
  };
}
