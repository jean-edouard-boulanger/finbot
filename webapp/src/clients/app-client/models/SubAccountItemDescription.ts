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
import type { SubAccountItemNodeIcon } from "./SubAccountItemNodeIcon";
import {
  SubAccountItemNodeIconFromJSON,
  SubAccountItemNodeIconFromJSONTyped,
  SubAccountItemNodeIconToJSON,
} from "./SubAccountItemNodeIcon";

/**
 *
 * @export
 * @interface SubAccountItemDescription
 */
export interface SubAccountItemDescription {
  /**
   *
   * @type {string}
   * @memberof SubAccountItemDescription
   */
  name: string;
  /**
   *
   * @type {string}
   * @memberof SubAccountItemDescription
   */
  type: string;
  /**
   *
   * @type {string}
   * @memberof SubAccountItemDescription
   */
  subType: string;
  /**
   *
   * @type {string}
   * @memberof SubAccountItemDescription
   */
  assetClass?: string;
  /**
   *
   * @type {string}
   * @memberof SubAccountItemDescription
   */
  assetType?: string;
  /**
   *
   * @type {SubAccountItemNodeIcon}
   * @memberof SubAccountItemDescription
   */
  icon?: SubAccountItemNodeIcon;
}

/**
 * Check if a given object implements the SubAccountItemDescription interface.
 */
export function instanceOfSubAccountItemDescription(value: object): boolean {
  let isInstance = true;
  isInstance = isInstance && "name" in value;
  isInstance = isInstance && "type" in value;
  isInstance = isInstance && "subType" in value;

  return isInstance;
}

export function SubAccountItemDescriptionFromJSON(
  json: any,
): SubAccountItemDescription {
  return SubAccountItemDescriptionFromJSONTyped(json, false);
}

export function SubAccountItemDescriptionFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): SubAccountItemDescription {
  if (json === undefined || json === null) {
    return json;
  }
  return {
    name: json["name"],
    type: json["type"],
    subType: json["sub_type"],
    assetClass: !exists(json, "asset_class") ? undefined : json["asset_class"],
    assetType: !exists(json, "asset_type") ? undefined : json["asset_type"],
    icon: !exists(json, "icon")
      ? undefined
      : SubAccountItemNodeIconFromJSON(json["icon"]),
  };
}

export function SubAccountItemDescriptionToJSON(
  value?: SubAccountItemDescription | null,
): any {
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  return {
    name: value.name,
    type: value.type,
    sub_type: value.subType,
    asset_class: value.assetClass,
    asset_type: value.assetType,
    icon: SubAccountItemNodeIconToJSON(value.icon),
  };
}
