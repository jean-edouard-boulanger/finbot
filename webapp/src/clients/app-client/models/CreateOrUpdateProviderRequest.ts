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
 * @interface CreateOrUpdateProviderRequest
 */
export interface CreateOrUpdateProviderRequest {
  /**
   *
   * @type {string}
   * @memberof CreateOrUpdateProviderRequest
   */
  id: string;
  /**
   *
   * @type {string}
   * @memberof CreateOrUpdateProviderRequest
   */
  description: string;
  /**
   *
   * @type {string}
   * @memberof CreateOrUpdateProviderRequest
   */
  websiteUrl: string;
  /**
   *
   * @type {{ [key: string]: any; }}
   * @memberof CreateOrUpdateProviderRequest
   */
  credentialsSchema: { [key: string]: any };
}

/**
 * Check if a given object implements the CreateOrUpdateProviderRequest interface.
 */
export function instanceOfCreateOrUpdateProviderRequest(
  value: object,
): value is CreateOrUpdateProviderRequest {
  if (!("id" in value) || value["id"] === undefined) return false;
  if (!("description" in value) || value["description"] === undefined)
    return false;
  if (!("websiteUrl" in value) || value["websiteUrl"] === undefined)
    return false;
  if (
    !("credentialsSchema" in value) ||
    value["credentialsSchema"] === undefined
  )
    return false;
  return true;
}

export function CreateOrUpdateProviderRequestFromJSON(
  json: any,
): CreateOrUpdateProviderRequest {
  return CreateOrUpdateProviderRequestFromJSONTyped(json, false);
}

export function CreateOrUpdateProviderRequestFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): CreateOrUpdateProviderRequest {
  if (json == null) {
    return json;
  }
  return {
    id: json["id"],
    description: json["description"],
    websiteUrl: json["website_url"],
    credentialsSchema: json["credentials_schema"],
  };
}

export function CreateOrUpdateProviderRequestToJSON(
  json: any,
): CreateOrUpdateProviderRequest {
  return CreateOrUpdateProviderRequestToJSONTyped(json, false);
}

export function CreateOrUpdateProviderRequestToJSONTyped(
  value?: CreateOrUpdateProviderRequest | null,
  ignoreDiscriminator: boolean = false,
): any {
  if (value == null) {
    return value;
  }

  return {
    id: value["id"],
    description: value["description"],
    website_url: value["websiteUrl"],
    credentials_schema: value["credentialsSchema"],
  };
}
