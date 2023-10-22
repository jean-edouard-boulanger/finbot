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
 * @interface SubAccountDescription
 */
export interface SubAccountDescription {
  /**
   *
   * @type {string}
   * @memberof SubAccountDescription
   */
  id: string;
  /**
   *
   * @type {string}
   * @memberof SubAccountDescription
   */
  currency: string;
  /**
   *
   * @type {string}
   * @memberof SubAccountDescription
   */
  description: string;
  /**
   *
   * @type {string}
   * @memberof SubAccountDescription
   */
  type: string;
}

/**
 * Check if a given object implements the SubAccountDescription interface.
 */
export function instanceOfSubAccountDescription(value: object): boolean {
  let isInstance = true;
  isInstance = isInstance && "id" in value;
  isInstance = isInstance && "currency" in value;
  isInstance = isInstance && "description" in value;
  isInstance = isInstance && "type" in value;

  return isInstance;
}

export function SubAccountDescriptionFromJSON(
  json: any,
): SubAccountDescription {
  return SubAccountDescriptionFromJSONTyped(json, false);
}

export function SubAccountDescriptionFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): SubAccountDescription {
  if (json === undefined || json === null) {
    return json;
  }
  return {
    id: json["id"],
    currency: json["currency"],
    description: json["description"],
    type: json["type"],
  };
}

export function SubAccountDescriptionToJSON(
  value?: SubAccountDescription | null,
): any {
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  return {
    id: value.id,
    currency: value.currency,
    description: value.description,
    type: value.type,
  };
}
