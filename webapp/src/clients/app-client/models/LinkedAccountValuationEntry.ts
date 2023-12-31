/* tslint:disable */
/* eslint-disable */
/**
 * Finbot application service
 * API documentation for appwsrv
 *
 * The version of the OpenAPI document: v0.0.3
 *
 *
 * NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).
 * https://openapi-generator.tech
 * Do not edit the class manually.
 */

import { exists, mapValues } from "../runtime";
import type { LinkedAccountValuation } from "./LinkedAccountValuation";
import {
  LinkedAccountValuationFromJSON,
  LinkedAccountValuationFromJSONTyped,
  LinkedAccountValuationToJSON,
} from "./LinkedAccountValuation";
import type { LinkedAccountValuationLinkedAccountDescription } from "./LinkedAccountValuationLinkedAccountDescription";
import {
  LinkedAccountValuationLinkedAccountDescriptionFromJSON,
  LinkedAccountValuationLinkedAccountDescriptionFromJSONTyped,
  LinkedAccountValuationLinkedAccountDescriptionToJSON,
} from "./LinkedAccountValuationLinkedAccountDescription";

/**
 *
 * @export
 * @interface LinkedAccountValuationEntry
 */
export interface LinkedAccountValuationEntry {
  /**
   *
   * @type {LinkedAccountValuationLinkedAccountDescription}
   * @memberof LinkedAccountValuationEntry
   */
  linkedAccount: LinkedAccountValuationLinkedAccountDescription;
  /**
   *
   * @type {LinkedAccountValuation}
   * @memberof LinkedAccountValuationEntry
   */
  valuation: LinkedAccountValuation;
}

/**
 * Check if a given object implements the LinkedAccountValuationEntry interface.
 */
export function instanceOfLinkedAccountValuationEntry(value: object): boolean {
  let isInstance = true;
  isInstance = isInstance && "linkedAccount" in value;
  isInstance = isInstance && "valuation" in value;

  return isInstance;
}

export function LinkedAccountValuationEntryFromJSON(
  json: any,
): LinkedAccountValuationEntry {
  return LinkedAccountValuationEntryFromJSONTyped(json, false);
}

export function LinkedAccountValuationEntryFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): LinkedAccountValuationEntry {
  if (json === undefined || json === null) {
    return json;
  }
  return {
    linkedAccount: LinkedAccountValuationLinkedAccountDescriptionFromJSON(
      json["linked_account"],
    ),
    valuation: LinkedAccountValuationFromJSON(json["valuation"]),
  };
}

export function LinkedAccountValuationEntryToJSON(
  value?: LinkedAccountValuationEntry | null,
): any {
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  return {
    linked_account: LinkedAccountValuationLinkedAccountDescriptionToJSON(
      value.linkedAccount,
    ),
    valuation: LinkedAccountValuationToJSON(value.valuation),
  };
}
