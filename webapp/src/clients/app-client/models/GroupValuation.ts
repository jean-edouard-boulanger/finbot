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
 * @interface GroupValuation
 */
export interface GroupValuation {
  /**
   *
   * @type {string}
   * @memberof GroupValuation
   */
  name: string;
  /**
   *
   * @type {string}
   * @memberof GroupValuation
   */
  colour: string;
  /**
   *
   * @type {number}
   * @memberof GroupValuation
   */
  value: number;
}

/**
 * Check if a given object implements the GroupValuation interface.
 */
export function instanceOfGroupValuation(value: object): boolean {
  let isInstance = true;
  isInstance = isInstance && "name" in value;
  isInstance = isInstance && "colour" in value;
  isInstance = isInstance && "value" in value;

  return isInstance;
}

export function GroupValuationFromJSON(json: any): GroupValuation {
  return GroupValuationFromJSONTyped(json, false);
}

export function GroupValuationFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): GroupValuation {
  if (json === undefined || json === null) {
    return json;
  }
  return {
    name: json["name"],
    colour: json["colour"],
    value: json["value"],
  };
}

export function GroupValuationToJSON(value?: GroupValuation | null): any {
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  return {
    name: value.name,
    colour: value.colour,
    value: value.value,
  };
}
