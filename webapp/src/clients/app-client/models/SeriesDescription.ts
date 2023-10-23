/* tslint:disable */
/* eslint-disable */
/**
 * Finbot application service
 * API documentation for appwsrv
 *
 * The version of the OpenAPI document: v0.8.1
 *
 *
 * NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).
 * https://openapi-generator.tech
 * Do not edit the class manually.
 */

import { exists, mapValues } from "../runtime";
import type { DataInner } from "./DataInner";
import {
  DataInnerFromJSON,
  DataInnerFromJSONTyped,
  DataInnerToJSON,
} from "./DataInner";

/**
 *
 * @export
 * @interface SeriesDescription
 */
export interface SeriesDescription {
  /**
   *
   * @type {string}
   * @memberof SeriesDescription
   */
  name: string;
  /**
   *
   * @type {Array<DataInner>}
   * @memberof SeriesDescription
   */
  data: Array<DataInner>;
  /**
   *
   * @type {string}
   * @memberof SeriesDescription
   */
  colour: string;
}

/**
 * Check if a given object implements the SeriesDescription interface.
 */
export function instanceOfSeriesDescription(value: object): boolean {
  let isInstance = true;
  isInstance = isInstance && "name" in value;
  isInstance = isInstance && "data" in value;
  isInstance = isInstance && "colour" in value;

  return isInstance;
}

export function SeriesDescriptionFromJSON(json: any): SeriesDescription {
  return SeriesDescriptionFromJSONTyped(json, false);
}

export function SeriesDescriptionFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): SeriesDescription {
  if (json === undefined || json === null) {
    return json;
  }
  return {
    name: json["name"],
    data: (json["data"] as Array<any>).map(DataInnerFromJSON),
    colour: json["colour"],
  };
}

export function SeriesDescriptionToJSON(value?: SeriesDescription | null): any {
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  return {
    name: value.name,
    data: (value.data as Array<any>).map(DataInnerToJSON),
    colour: value.colour,
  };
}
