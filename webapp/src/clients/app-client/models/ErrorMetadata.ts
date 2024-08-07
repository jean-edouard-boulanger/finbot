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
/**
 *
 * @export
 * @interface ErrorMetadata
 */
export interface ErrorMetadata {
  /**
   *
   * @type {string}
   * @memberof ErrorMetadata
   */
  userMessage: string;
  /**
   *
   * @type {string}
   * @memberof ErrorMetadata
   */
  debugMessage?: string;
  /**
   *
   * @type {string}
   * @memberof ErrorMetadata
   */
  errorCode?: string;
  /**
   *
   * @type {string}
   * @memberof ErrorMetadata
   */
  exceptionType?: string;
  /**
   *
   * @type {string}
   * @memberof ErrorMetadata
   */
  trace?: string;
}

/**
 * Check if a given object implements the ErrorMetadata interface.
 */
export function instanceOfErrorMetadata(value: object): value is ErrorMetadata {
  if (!("userMessage" in value) || value["userMessage"] === undefined)
    return false;
  return true;
}

export function ErrorMetadataFromJSON(json: any): ErrorMetadata {
  return ErrorMetadataFromJSONTyped(json, false);
}

export function ErrorMetadataFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): ErrorMetadata {
  if (json == null) {
    return json;
  }
  return {
    userMessage: json["user_message"],
    debugMessage:
      json["debug_message"] == null ? undefined : json["debug_message"],
    errorCode: json["error_code"] == null ? undefined : json["error_code"],
    exceptionType:
      json["exception_type"] == null ? undefined : json["exception_type"],
    trace: json["trace"] == null ? undefined : json["trace"],
  };
}

export function ErrorMetadataToJSON(value?: ErrorMetadata | null): any {
  if (value == null) {
    return value;
  }
  return {
    user_message: value["userMessage"],
    debug_message: value["debugMessage"],
    error_code: value["errorCode"],
    exception_type: value["exceptionType"],
    trace: value["trace"],
  };
}
