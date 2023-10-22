/* tslint:disable */
/* eslint-disable */
/**
 * Finbot application service
 * API documentation for appwsrv
 *
 * The version of the OpenAPI document: v0.8.0
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
 * @interface AppGetProvidersResponse
 */
export interface AppGetProvidersResponse {
  /**
   *
   * @type {Array<Provider>}
   * @memberof AppGetProvidersResponse
   */
  providers: Array<Provider>;
}

/**
 * Check if a given object implements the AppGetProvidersResponse interface.
 */
export function instanceOfAppGetProvidersResponse(value: object): boolean {
  let isInstance = true;
  isInstance = isInstance && "providers" in value;

  return isInstance;
}

export function AppGetProvidersResponseFromJSON(
  json: any,
): AppGetProvidersResponse {
  return AppGetProvidersResponseFromJSONTyped(json, false);
}

export function AppGetProvidersResponseFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): AppGetProvidersResponse {
  if (json === undefined || json === null) {
    return json;
  }
  return {
    providers: (json["providers"] as Array<any>).map(ProviderFromJSON),
  };
}

export function AppGetProvidersResponseToJSON(
  value?: AppGetProvidersResponse | null,
): any {
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  return {
    providers: (value.providers as Array<any>).map(ProviderToJSON),
  };
}
