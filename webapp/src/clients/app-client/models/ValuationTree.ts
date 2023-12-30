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
import type { UserAccountNode } from "./UserAccountNode";
import {
  UserAccountNodeFromJSON,
  UserAccountNodeFromJSONTyped,
  UserAccountNodeToJSON,
} from "./UserAccountNode";

/**
 *
 * @export
 * @interface ValuationTree
 */
export interface ValuationTree {
  /**
   *
   * @type {UserAccountNode}
   * @memberof ValuationTree
   */
  valuationTree: UserAccountNode;
}

/**
 * Check if a given object implements the ValuationTree interface.
 */
export function instanceOfValuationTree(value: object): boolean {
  let isInstance = true;
  isInstance = isInstance && "valuationTree" in value;

  return isInstance;
}

export function ValuationTreeFromJSON(json: any): ValuationTree {
  return ValuationTreeFromJSONTyped(json, false);
}

export function ValuationTreeFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): ValuationTree {
  if (json === undefined || json === null) {
    return json;
  }
  return {
    valuationTree: UserAccountNodeFromJSON(json["valuation_tree"]),
  };
}

export function ValuationTreeToJSON(value?: ValuationTree | null): any {
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  return {
    valuation_tree: UserAccountNodeToJSON(value.valuationTree),
  };
}
