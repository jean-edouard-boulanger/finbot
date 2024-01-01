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
import type { Provider } from "./Provider";
import {
  ProviderFromJSON,
  ProviderFromJSONTyped,
  ProviderToJSON,
} from "./Provider";

/**
 *
 * @export
 * @interface AppGetProviderResponse
 */
export interface AppGetProviderResponse {
  /**
   *
   * @type {Provider}
   * @memberof AppGetProviderResponse
   */
  provider: Provider;
}

/**
 * Check if a given object implements the AppGetProviderResponse interface.
 */
export function instanceOfAppGetProviderResponse(value: object): boolean {
  let isInstance = true;
  isInstance = isInstance && "provider" in value;

  return isInstance;
}

export function AppGetProviderResponseFromJSON(
  json: any,
): AppGetProviderResponse {
  return AppGetProviderResponseFromJSONTyped(json, false);
}

export function AppGetProviderResponseFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): AppGetProviderResponse {
  if (json === undefined || json === null) {
    return json;
  }
  return {
    provider: ProviderFromJSON(json["provider"]),
  };
}

export function AppGetProviderResponseToJSON(
  value?: AppGetProviderResponse | null,
): any {
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  return {
    provider: ProviderToJSON(value.provider),
  };
}
