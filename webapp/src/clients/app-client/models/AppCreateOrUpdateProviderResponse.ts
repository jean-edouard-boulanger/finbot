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
import type { Provider } from "./Provider";
import {
  ProviderFromJSON,
  ProviderFromJSONTyped,
  ProviderToJSON,
} from "./Provider";

/**
 *
 * @export
 * @interface AppCreateOrUpdateProviderResponse
 */
export interface AppCreateOrUpdateProviderResponse {
  /**
   *
   * @type {Provider}
   * @memberof AppCreateOrUpdateProviderResponse
   */
  provider: Provider;
}

/**
 * Check if a given object implements the AppCreateOrUpdateProviderResponse interface.
 */
export function instanceOfAppCreateOrUpdateProviderResponse(
  value: object,
): value is AppCreateOrUpdateProviderResponse {
  if (!("provider" in value) || value["provider"] === undefined) return false;
  return true;
}

export function AppCreateOrUpdateProviderResponseFromJSON(
  json: any,
): AppCreateOrUpdateProviderResponse {
  return AppCreateOrUpdateProviderResponseFromJSONTyped(json, false);
}

export function AppCreateOrUpdateProviderResponseFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): AppCreateOrUpdateProviderResponse {
  if (json == null) {
    return json;
  }
  return {
    provider: ProviderFromJSON(json["provider"]),
  };
}

export function AppCreateOrUpdateProviderResponseToJSON(
  value?: AppCreateOrUpdateProviderResponse | null,
): any {
  if (value == null) {
    return value;
  }
  return {
    provider: ProviderToJSON(value["provider"]),
  };
}
