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
import type { EmailProviderMetadata } from "./EmailProviderMetadata";
import {
  EmailProviderMetadataFromJSON,
  EmailProviderMetadataFromJSONTyped,
  EmailProviderMetadataToJSON,
} from "./EmailProviderMetadata";

/**
 *
 * @export
 * @interface AppGetEmailDeliveryProvidersResponse
 */
export interface AppGetEmailDeliveryProvidersResponse {
  /**
   *
   * @type {Array<EmailProviderMetadata>}
   * @memberof AppGetEmailDeliveryProvidersResponse
   */
  providers: Array<EmailProviderMetadata>;
}

/**
 * Check if a given object implements the AppGetEmailDeliveryProvidersResponse interface.
 */
export function instanceOfAppGetEmailDeliveryProvidersResponse(
  value: object,
): value is AppGetEmailDeliveryProvidersResponse {
  if (!("providers" in value) || value["providers"] === undefined) return false;
  return true;
}

export function AppGetEmailDeliveryProvidersResponseFromJSON(
  json: any,
): AppGetEmailDeliveryProvidersResponse {
  return AppGetEmailDeliveryProvidersResponseFromJSONTyped(json, false);
}

export function AppGetEmailDeliveryProvidersResponseFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): AppGetEmailDeliveryProvidersResponse {
  if (json == null) {
    return json;
  }
  return {
    providers: (json["providers"] as Array<any>).map(
      EmailProviderMetadataFromJSON,
    ),
  };
}

export function AppGetEmailDeliveryProvidersResponseToJSON(
  value?: AppGetEmailDeliveryProvidersResponse | null,
): any {
  if (value == null) {
    return value;
  }
  return {
    providers: (value["providers"] as Array<any>).map(
      EmailProviderMetadataToJSON,
    ),
  };
}
