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

import { exists, mapValues } from "../runtime";
/**
 *
 * @export
 * @interface EmailProviderMetadata
 */
export interface EmailProviderMetadata {
  /**
   *
   * @type {string}
   * @memberof EmailProviderMetadata
   */
  providerId: string;
  /**
   *
   * @type {string}
   * @memberof EmailProviderMetadata
   */
  description: string;
  /**
   *
   * @type {object}
   * @memberof EmailProviderMetadata
   */
  settingsSchema: object;
}

/**
 * Check if a given object implements the EmailProviderMetadata interface.
 */
export function instanceOfEmailProviderMetadata(value: object): boolean {
  let isInstance = true;
  isInstance = isInstance && "providerId" in value;
  isInstance = isInstance && "description" in value;
  isInstance = isInstance && "settingsSchema" in value;

  return isInstance;
}

export function EmailProviderMetadataFromJSON(
  json: any,
): EmailProviderMetadata {
  return EmailProviderMetadataFromJSONTyped(json, false);
}

export function EmailProviderMetadataFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): EmailProviderMetadata {
  if (json === undefined || json === null) {
    return json;
  }
  return {
    providerId: json["provider_id"],
    description: json["description"],
    settingsSchema: json["settings_schema"],
  };
}

export function EmailProviderMetadataToJSON(
  value?: EmailProviderMetadata | null,
): any {
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  return {
    provider_id: value.providerId,
    description: value.description,
    settings_schema: value.settingsSchema,
  };
}
