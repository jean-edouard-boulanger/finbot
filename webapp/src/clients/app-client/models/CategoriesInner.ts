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
/**
 *
 * @export
 * @interface CategoriesInner
 */
export interface CategoriesInner {}

/**
 * Check if a given object implements the CategoriesInner interface.
 */
export function instanceOfCategoriesInner(
  value: object,
): value is CategoriesInner {
  return true;
}

export function CategoriesInnerFromJSON(json: any): CategoriesInner {
  return CategoriesInnerFromJSONTyped(json, false);
}

export function CategoriesInnerFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): CategoriesInner {
  return json;
}

export function CategoriesInnerToJSON(json: any): CategoriesInner {
  return CategoriesInnerToJSONTyped(json, false);
}

export function CategoriesInnerToJSONTyped(
  value?: CategoriesInner | null,
  ignoreDiscriminator: boolean = false,
): any {
  return value;
}
