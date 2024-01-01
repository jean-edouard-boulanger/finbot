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
): boolean {
  let isInstance = true;
  isInstance = isInstance && "providers" in value;

  return isInstance;
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
  if (json === undefined || json === null) {
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
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  return {
    providers: (value.providers as Array<any>).map(EmailProviderMetadataToJSON),
  };
}
