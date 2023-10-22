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
import type { Value } from "./Value";
import { ValueFromJSON, ValueFromJSONTyped, ValueToJSON } from "./Value";

/**
 *
 * @export
 * @interface SubAccountItemMetadataNode
 */
export interface SubAccountItemMetadataNode {
  /**
   *
   * @type {string}
   * @memberof SubAccountItemMetadataNode
   */
  role?: SubAccountItemMetadataNodeRoleEnum;
  /**
   *
   * @type {string}
   * @memberof SubAccountItemMetadataNode
   */
  label: string;
  /**
   *
   * @type {Value}
   * @memberof SubAccountItemMetadataNode
   */
  value: Value;
}

/**
 * @export
 */
export const SubAccountItemMetadataNodeRoleEnum = {
  Metadata: "metadata",
} as const;
export type SubAccountItemMetadataNodeRoleEnum =
  (typeof SubAccountItemMetadataNodeRoleEnum)[keyof typeof SubAccountItemMetadataNodeRoleEnum];

/**
 * Check if a given object implements the SubAccountItemMetadataNode interface.
 */
export function instanceOfSubAccountItemMetadataNode(value: object): boolean {
  let isInstance = true;
  isInstance = isInstance && "label" in value;
  isInstance = isInstance && "value" in value;

  return isInstance;
}

export function SubAccountItemMetadataNodeFromJSON(
  json: any,
): SubAccountItemMetadataNode {
  return SubAccountItemMetadataNodeFromJSONTyped(json, false);
}

export function SubAccountItemMetadataNodeFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): SubAccountItemMetadataNode {
  if (json === undefined || json === null) {
    return json;
  }
  return {
    role: !exists(json, "role") ? undefined : json["role"],
    label: json["label"],
    value: ValueFromJSON(json["value"]),
  };
}

export function SubAccountItemMetadataNodeToJSON(
  value?: SubAccountItemMetadataNode | null,
): any {
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  return {
    role: value.role,
    label: value.label,
    value: ValueToJSON(value.value),
  };
}
