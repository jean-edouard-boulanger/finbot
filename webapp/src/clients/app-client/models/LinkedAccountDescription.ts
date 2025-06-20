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
export function instanceOfLinkedAccountDescription(
  value: object,
): value is LinkedAccountDescription {
  if (!("id" in value) || value["id"] === undefined) return false;
  if (!("providerId" in value) || value["providerId"] === undefined)
    return false;
  if (!("description" in value) || value["description"] === undefined)
    return false;
  return true;
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
  if (json == null) {
    return json;
  }
  return {
    id: json["id"],
    providerId: json["provider_id"],
    description: json["description"],
  };
}

export function LinkedAccountDescriptionToJSON(
  json: any,
): LinkedAccountDescription {
  return LinkedAccountDescriptionToJSONTyped(json, false);
}

export function LinkedAccountDescriptionToJSONTyped(
  value?: LinkedAccountDescription | null,
  ignoreDiscriminator: boolean = false,
): any {
  if (value == null) {
    return value;
  }

  return {
    id: value["id"],
    provider_id: value["providerId"],
    description: value["description"],
  };
}
