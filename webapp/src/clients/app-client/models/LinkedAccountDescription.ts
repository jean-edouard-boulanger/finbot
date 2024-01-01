/* tslint:disable */
/* eslint-disable */
/**
 * Finbot application service
 * API documentation for appwsrv
 *
 * The version of the OpenAPI document: v0.0.4
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
 * @interface LinkedAccountDescription
 */
export interface LinkedAccountDescription {
  /**
   *
   * @type {number}
   * @memberof LinkedAccountDescription
   */
  id: number;
  /**
   *
   * @type {string}
   * @memberof LinkedAccountDescription
   */
  providerId: string;
  /**
   *
   * @type {string}
   * @memberof LinkedAccountDescription
   */
  description: string;
}

/**
 * Check if a given object implements the LinkedAccountDescription interface.
 */
export function instanceOfLinkedAccountDescription(value: object): boolean {
  let isInstance = true;
  isInstance = isInstance && "id" in value;
  isInstance = isInstance && "providerId" in value;
  isInstance = isInstance && "description" in value;

  return isInstance;
}

export function LinkedAccountDescriptionFromJSON(
  json: any,
): LinkedAccountDescription {
  return LinkedAccountDescriptionFromJSONTyped(json, false);
}

export function LinkedAccountDescriptionFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): LinkedAccountDescription {
  if (json === undefined || json === null) {
    return json;
  }
  return {
    id: json["id"],
    providerId: json["provider_id"],
    description: json["description"],
  };
}

export function LinkedAccountDescriptionToJSON(
  value?: LinkedAccountDescription | null,
): any {
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  return {
    id: value.id,
    provider_id: value.providerId,
    description: value.description,
  };
}
