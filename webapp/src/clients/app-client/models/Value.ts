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
 * @interface Value
 */
export interface Value {}

/**
 * Check if a given object implements the Value interface.
 */
export function instanceOfValue(value: object): boolean {
  let isInstance = true;

  return isInstance;
}

export function ValueFromJSON(json: any): Value {
  return ValueFromJSONTyped(json, false);
}

export function ValueFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): Value {
  return json;
}

export function ValueToJSON(value?: Value | null): any {
  return value;
}
