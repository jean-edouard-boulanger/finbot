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
 * @interface LinkedAccountValuationLinkedAccountDescription
 */
export interface LinkedAccountValuationLinkedAccountDescription {
  /**
   *
   * @type {number}
   * @memberof LinkedAccountValuationLinkedAccountDescription
   */
  id: number;
  /**
   *
   * @type {string}
   * @memberof LinkedAccountValuationLinkedAccountDescription
   */
  providerId: string;
  /**
   *
   * @type {string}
   * @memberof LinkedAccountValuationLinkedAccountDescription
   */
  description: string;
  /**
   *
   * @type {string}
   * @memberof LinkedAccountValuationLinkedAccountDescription
   */
  accountColour: string;
}

/**
 * Check if a given object implements the LinkedAccountValuationLinkedAccountDescription interface.
 */
export function instanceOfLinkedAccountValuationLinkedAccountDescription(
  value: object,
): boolean {
  let isInstance = true;
  isInstance = isInstance && "id" in value;
  isInstance = isInstance && "providerId" in value;
  isInstance = isInstance && "description" in value;
  isInstance = isInstance && "accountColour" in value;

  return isInstance;
}

export function LinkedAccountValuationLinkedAccountDescriptionFromJSON(
  json: any,
): LinkedAccountValuationLinkedAccountDescription {
  return LinkedAccountValuationLinkedAccountDescriptionFromJSONTyped(
    json,
    false,
  );
}

export function LinkedAccountValuationLinkedAccountDescriptionFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): LinkedAccountValuationLinkedAccountDescription {
  if (json === undefined || json === null) {
    return json;
  }
  return {
    id: json["id"],
    providerId: json["provider_id"],
    description: json["description"],
    accountColour: json["account_colour"],
  };
}

export function LinkedAccountValuationLinkedAccountDescriptionToJSON(
  value?: LinkedAccountValuationLinkedAccountDescription | null,
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
    account_colour: value.accountColour,
  };
}
