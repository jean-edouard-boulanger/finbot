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
 * @interface AppGetAccountsFormattingRulesResponse
 */
export interface AppGetAccountsFormattingRulesResponse {
  /**
   *
   * @type {Array<string>}
   * @memberof AppGetAccountsFormattingRulesResponse
   */
  colourPalette: Array<string>;
}

/**
 * Check if a given object implements the AppGetAccountsFormattingRulesResponse interface.
 */
export function instanceOfAppGetAccountsFormattingRulesResponse(
  value: object,
): boolean {
  let isInstance = true;
  isInstance = isInstance && "colourPalette" in value;

  return isInstance;
}

export function AppGetAccountsFormattingRulesResponseFromJSON(
  json: any,
): AppGetAccountsFormattingRulesResponse {
  return AppGetAccountsFormattingRulesResponseFromJSONTyped(json, false);
}

export function AppGetAccountsFormattingRulesResponseFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): AppGetAccountsFormattingRulesResponse {
  if (json === undefined || json === null) {
    return json;
  }
  return {
    colourPalette: json["colour_palette"],
  };
}

export function AppGetAccountsFormattingRulesResponseToJSON(
  value?: AppGetAccountsFormattingRulesResponse | null,
): any {
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  return {
    colour_palette: value.colourPalette,
  };
}
