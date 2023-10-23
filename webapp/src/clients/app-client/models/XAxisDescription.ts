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
export function instanceOfXAxisDescription(value: object): boolean {
  let isInstance = true;
  isInstance = isInstance && "type" in value;
  isInstance = isInstance && "categories" in value;

  return isInstance;
}

export function XAxisDescriptionFromJSON(json: any): XAxisDescription {
  return XAxisDescriptionFromJSONTyped(json, false);
}

export function XAxisDescriptionFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): XAxisDescription {
  if (json === undefined || json === null) {
    return json;
  }
  return {
    type: json["type"],
    categories: (json["categories"] as Array<any>).map(CategoriesInnerFromJSON),
  };
}

export function XAxisDescriptionToJSON(value?: XAxisDescription | null): any {
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  return {
    type: value.type,
    categories: (value.categories as Array<any>).map(CategoriesInnerToJSON),
  };
}
