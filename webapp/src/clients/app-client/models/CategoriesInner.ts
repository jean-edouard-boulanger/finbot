/* tslint:disable */
/* eslint-disable */
/**
 * Finbot application service
 * API documentation for appwsrv
 *
 * The version of the OpenAPI document: v0.0.3
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
 * @interface CategoriesInner
 */
export interface CategoriesInner {}

/**
 * Check if a given object implements the CategoriesInner interface.
 */
export function instanceOfCategoriesInner(value: object): boolean {
  let isInstance = true;

  return isInstance;
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

export function CategoriesInnerToJSON(value?: CategoriesInner | null): any {
  return value;
}
