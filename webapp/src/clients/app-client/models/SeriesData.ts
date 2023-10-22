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
import type { SeriesDescription } from "./SeriesDescription";
import {
  SeriesDescriptionFromJSON,
  SeriesDescriptionFromJSONTyped,
  SeriesDescriptionToJSON,
} from "./SeriesDescription";
import type { XAxisDescription } from "./XAxisDescription";
import {
  XAxisDescriptionFromJSON,
  XAxisDescriptionFromJSONTyped,
  XAxisDescriptionToJSON,
} from "./XAxisDescription";

/**
 *
 * @export
 * @interface SeriesData
 */
export interface SeriesData {
  /**
   *
   * @type {XAxisDescription}
   * @memberof SeriesData
   */
  xAxis: XAxisDescription;
  /**
   *
   * @type {Array<SeriesDescription>}
   * @memberof SeriesData
   */
  series: Array<SeriesDescription>;
}

/**
 * Check if a given object implements the SeriesData interface.
 */
export function instanceOfSeriesData(value: object): boolean {
  let isInstance = true;
  isInstance = isInstance && "xAxis" in value;
  isInstance = isInstance && "series" in value;

  return isInstance;
}

export function SeriesDataFromJSON(json: any): SeriesData {
  return SeriesDataFromJSONTyped(json, false);
}

export function SeriesDataFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): SeriesData {
  if (json === undefined || json === null) {
    return json;
  }
  return {
    xAxis: XAxisDescriptionFromJSON(json["x_axis"]),
    series: (json["series"] as Array<any>).map(SeriesDescriptionFromJSON),
  };
}

export function SeriesDataToJSON(value?: SeriesData | null): any {
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  return {
    x_axis: XAxisDescriptionToJSON(value.xAxis),
    series: (value.series as Array<any>).map(SeriesDescriptionToJSON),
  };
}
