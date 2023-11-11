/* tslint:disable */
/* eslint-disable */
/**
 * Finbot application service
 * API documentation for appwsrv
 *
 * The version of the OpenAPI document: v0.0.2
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
 * @interface AppEmailDeliverySettings
 */
export interface AppEmailDeliverySettings {
  /**
   *
   * @type {string}
   * @memberof AppEmailDeliverySettings
   */
  subjectPrefix: string;
  /**
   *
   * @type {string}
   * @memberof AppEmailDeliverySettings
   */
  senderName: string;
  /**
   *
   * @type {string}
   * @memberof AppEmailDeliverySettings
   */
  providerId: string;
  /**
   *
   * @type {object}
   * @memberof AppEmailDeliverySettings
   */
  providerSettings: object;
}

/**
 * Check if a given object implements the AppEmailDeliverySettings interface.
 */
export function instanceOfAppEmailDeliverySettings(value: object): boolean {
  let isInstance = true;
  isInstance = isInstance && "subjectPrefix" in value;
  isInstance = isInstance && "senderName" in value;
  isInstance = isInstance && "providerId" in value;
  isInstance = isInstance && "providerSettings" in value;

  return isInstance;
}

export function AppEmailDeliverySettingsFromJSON(
  json: any,
): AppEmailDeliverySettings {
  return AppEmailDeliverySettingsFromJSONTyped(json, false);
}

export function AppEmailDeliverySettingsFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): AppEmailDeliverySettings {
  if (json === undefined || json === null) {
    return json;
  }
  return {
    subjectPrefix: json["subject_prefix"],
    senderName: json["sender_name"],
    providerId: json["provider_id"],
    providerSettings: json["provider_settings"],
  };
}

export function AppEmailDeliverySettingsToJSON(
  value?: AppEmailDeliverySettings | null,
): any {
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  return {
    subject_prefix: value.subjectPrefix,
    sender_name: value.senderName,
    provider_id: value.providerId,
    provider_settings: value.providerSettings,
  };
}