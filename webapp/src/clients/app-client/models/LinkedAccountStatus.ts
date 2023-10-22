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
import type { LinkedAccountStatusErrorEntry } from "./LinkedAccountStatusErrorEntry";
import {
  LinkedAccountStatusErrorEntryFromJSON,
  LinkedAccountStatusErrorEntryFromJSONTyped,
  LinkedAccountStatusErrorEntryToJSON,
} from "./LinkedAccountStatusErrorEntry";

/**
 *
 * @export
 * @interface LinkedAccountStatus
 */
export interface LinkedAccountStatus {
  /**
   *
   * @type {string}
   * @memberof LinkedAccountStatus
   */
  status: LinkedAccountStatusStatusEnum;
  /**
   *
   * @type {Array<LinkedAccountStatusErrorEntry>}
   * @memberof LinkedAccountStatus
   */
  errors?: Array<LinkedAccountStatusErrorEntry>;
  /**
   *
   * @type {number}
   * @memberof LinkedAccountStatus
   */
  lastSnapshotId: number;
  /**
   *
   * @type {Date}
   * @memberof LinkedAccountStatus
   */
  lastSnapshotTime: Date;
}

/**
 * @export
 */
export const LinkedAccountStatusStatusEnum = {
  Stable: "stable",
  Unstable: "unstable",
} as const;
export type LinkedAccountStatusStatusEnum =
  (typeof LinkedAccountStatusStatusEnum)[keyof typeof LinkedAccountStatusStatusEnum];

/**
 * Check if a given object implements the LinkedAccountStatus interface.
 */
export function instanceOfLinkedAccountStatus(value: object): boolean {
  let isInstance = true;
  isInstance = isInstance && "status" in value;
  isInstance = isInstance && "lastSnapshotId" in value;
  isInstance = isInstance && "lastSnapshotTime" in value;

  return isInstance;
}

export function LinkedAccountStatusFromJSON(json: any): LinkedAccountStatus {
  return LinkedAccountStatusFromJSONTyped(json, false);
}

export function LinkedAccountStatusFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean,
): LinkedAccountStatus {
  if (json === undefined || json === null) {
    return json;
  }
  return {
    status: json["status"],
    errors: !exists(json, "errors")
      ? undefined
      : (json["errors"] as Array<any>).map(
          LinkedAccountStatusErrorEntryFromJSON,
        ),
    lastSnapshotId: json["last_snapshot_id"],
    lastSnapshotTime: new Date(json["last_snapshot_time"]),
  };
}

export function LinkedAccountStatusToJSON(
  value?: LinkedAccountStatus | null,
): any {
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  return {
    status: value.status,
    errors:
      value.errors === undefined
        ? undefined
        : (value.errors as Array<any>).map(LinkedAccountStatusErrorEntryToJSON),
    last_snapshot_id: value.lastSnapshotId,
    last_snapshot_time: value.lastSnapshotTime.toISOString(),
  };
}
