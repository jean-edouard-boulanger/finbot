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

import { exists, mapValues } from '../runtime';
/**
 * Model of a validation error response element.
 * @export
 * @interface ValidationErrorElement
 */
export interface ValidationErrorElement {
    /**
     * 
     * @type {Array<string>}
     * @memberof ValidationErrorElement
     */
    loc: Array<string>;
    /**
     * 
     * @type {string}
     * @memberof ValidationErrorElement
     */
    msg: string;
    /**
     * 
     * @type {string}
     * @memberof ValidationErrorElement
     */
    type: string;
    /**
     * 
     * @type {object}
     * @memberof ValidationErrorElement
     */
    ctx?: object;
}

/**
 * Check if a given object implements the ValidationErrorElement interface.
 */
export function instanceOfValidationErrorElement(value: object): boolean {
    let isInstance = true;
    isInstance = isInstance && "loc" in value;
    isInstance = isInstance && "msg" in value;
    isInstance = isInstance && "type" in value;

    return isInstance;
}

export function ValidationErrorElementFromJSON(json: any): ValidationErrorElement {
    return ValidationErrorElementFromJSONTyped(json, false);
}

export function ValidationErrorElementFromJSONTyped(json: any, ignoreDiscriminator: boolean): ValidationErrorElement {
    if ((json === undefined) || (json === null)) {
        return json;
    }
    return {
        
        'loc': json['loc'],
        'msg': json['msg'],
        'type': json['type'],
        'ctx': !exists(json, 'ctx') ? undefined : json['ctx'],
    };
}

export function ValidationErrorElementToJSON(value?: ValidationErrorElement | null): any {
    if (value === undefined) {
        return undefined;
    }
    if (value === null) {
        return null;
    }
    return {
        
        'loc': value.loc,
        'msg': value.msg,
        'type': value.type,
        'ctx': value.ctx,
    };
}

