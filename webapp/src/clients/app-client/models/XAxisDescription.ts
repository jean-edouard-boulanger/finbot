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
import type { CategoriesInner } from "./CategoriesInner";
import {
  CategoriesInnerFromJSON,
  CategoriesInnerFromJSONTyped,
  CategoriesInnerToJSON,
} from "./CategoriesInner";

/**
 *
 * @export
 * @interface XAxisDescription
 */
export interface XAxisDescription {
  /**
   *
   * @type {string}
   * @memberof XAxisDescription
   */
  type: string;
  /**
   *
   * @type {Array<CategoriesInner>}
   * @memberof XAxisDescription
   */
  categories: Array<CategoriesInner>;
}

/**
 * Check if a given object implements the XAxisDescription interface.
 */
export function instanceOfXAxisDescription(
  value: object,
): value is XAxisDescription {
  if (!("type" in value) || value["type"] === undefined) return false;
  if (!("categories" in value) || value["categories"] === undefined)
    return false;
  return true;
}

export function XAxisDescriptionFromJSON(json: any): XAxisDescription {
  return XAxisDescriptionFromJSONTyped(json, false);
}

export function XAxisDescriptionFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): XAxisDescription {
  if (json == null) {
    return json;
  }
  return {
    type: json["type"],
    categories: (json["categories"] as Array<any>).map(CategoriesInnerFromJSON),
  };
}

export function XAxisDescriptionToJSON(value?: XAxisDescription | null): any {
  if (value == null) {
    return value;
  }
  return {
    type: value["type"],
    categories: (value["categories"] as Array<any>).map(CategoriesInnerToJSON),
  };
}
