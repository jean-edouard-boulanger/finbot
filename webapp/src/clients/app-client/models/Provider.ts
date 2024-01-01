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
 * @interface Provider
 */
export interface Provider {
  /**
   *
   * @type {string}
   * @memberof Provider
   */
  id: string;
  /**
   *
   * @type {string}
   * @memberof Provider
   */
  description: string;
  /**
   *
   * @type {string}
   * @memberof Provider
   */
  websiteUrl: string;
  /**
   *
   * @type {object}
   * @memberof Provider
   */
  credentialsSchema: object;
  /**
   *
   * @type {Date}
   * @memberof Provider
   */
  createdAt: Date;
  /**
   *
   * @type {Date}
   * @memberof Provider
   */
  updatedAt?: Date;
}

/**
 * Check if a given object implements the Provider interface.
 */
export function instanceOfProvider(value: object): boolean {
  let isInstance = true;
  isInstance = isInstance && "id" in value;
  isInstance = isInstance && "description" in value;
  isInstance = isInstance && "websiteUrl" in value;
  isInstance = isInstance && "credentialsSchema" in value;
  isInstance = isInstance && "createdAt" in value;

  return isInstance;
}

export function ProviderFromJSON(json: any): Provider {
  return ProviderFromJSONTyped(json, false);
}

export function ProviderFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): Provider {
  if (json === undefined || json === null) {
    return json;
  }
  return {
    id: json["id"],
    description: json["description"],
    websiteUrl: json["website_url"],
    credentialsSchema: json["credentials_schema"],
    createdAt: new Date(json["created_at"]),
    updatedAt: !exists(json, "updated_at")
      ? undefined
      : new Date(json["updated_at"]),
  };
}

export function ProviderToJSON(value?: Provider | null): any {
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  return {
    id: value.id,
    description: value.description,
    website_url: value.websiteUrl,
    credentials_schema: value.credentialsSchema,
    created_at: value.createdAt.toISOString(),
    updated_at:
      value.updatedAt === undefined ? undefined : value.updatedAt.toISOString(),
  };
}
