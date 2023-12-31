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


import * as runtime from '../runtime';
import type {
  AppGetEarningsReportResponse,
  AppGetHoldingsReportResponse,
  ValidationErrorElement,
} from '../models/index';
import {
    AppGetEarningsReportResponseFromJSON,
    AppGetEarningsReportResponseToJSON,
    AppGetHoldingsReportResponseFromJSON,
    AppGetHoldingsReportResponseToJSON,
    ValidationErrorElementFromJSON,
    ValidationErrorElementToJSON,
} from '../models/index';

/**
 * UserAccountsReportsApi - interface
 * 
 * @export
 * @interface UserAccountsReportsApiInterface
 */
export interface UserAccountsReportsApiInterface {
    /**
     * 
     * @summary Get earnings report
     * @param {*} [options] Override http request option.
     * @throws {RequiredError}
     * @memberof UserAccountsReportsApiInterface
     */
    getUserAccountEarningsReportRaw(initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<AppGetEarningsReportResponse>>;

    /**
     * 
     * Get earnings report
     */
    getUserAccountEarningsReport(initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<AppGetEarningsReportResponse>;

    /**
     * 
     * @summary Get holdings report
     * @param {*} [options] Override http request option.
     * @throws {RequiredError}
     * @memberof UserAccountsReportsApiInterface
     */
    getUserAccountHoldingsReportRaw(initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<AppGetHoldingsReportResponse>>;

    /**
     * 
     * Get holdings report
     */
    getUserAccountHoldingsReport(initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<AppGetHoldingsReportResponse>;

}

/**
 * 
 */
export class UserAccountsReportsApi extends runtime.BaseAPI implements UserAccountsReportsApiInterface {

    /**
     * 
     * Get earnings report
     */
    async getUserAccountEarningsReportRaw(initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<AppGetEarningsReportResponse>> {
        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        if (this.configuration && this.configuration.accessToken) {
            const token = this.configuration.accessToken;
            const tokenString = await token("bearerAuth", []);

            if (tokenString) {
                headerParameters["Authorization"] = `Bearer ${tokenString}`;
            }
        }
        const response = await this.request({
            path: `/api/v1/reports/earnings/`,
            method: 'GET',
            headers: headerParameters,
            query: queryParameters,
        }, initOverrides);

        return new runtime.JSONApiResponse(response, (jsonValue) => AppGetEarningsReportResponseFromJSON(jsonValue));
    }

    /**
     * 
     * Get earnings report
     */
    async getUserAccountEarningsReport(initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<AppGetEarningsReportResponse> {
        const response = await this.getUserAccountEarningsReportRaw(initOverrides);
        return await response.value();
    }

    /**
     * 
     * Get holdings report
     */
    async getUserAccountHoldingsReportRaw(initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<AppGetHoldingsReportResponse>> {
        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        if (this.configuration && this.configuration.accessToken) {
            const token = this.configuration.accessToken;
            const tokenString = await token("bearerAuth", []);

            if (tokenString) {
                headerParameters["Authorization"] = `Bearer ${tokenString}`;
            }
        }
        const response = await this.request({
            path: `/api/v1/reports/holdings/`,
            method: 'GET',
            headers: headerParameters,
            query: queryParameters,
        }, initOverrides);

        return new runtime.JSONApiResponse(response, (jsonValue) => AppGetHoldingsReportResponseFromJSON(jsonValue));
    }

    /**
     * 
     * Get holdings report
     */
    async getUserAccountHoldingsReport(initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<AppGetHoldingsReportResponse> {
        const response = await this.getUserAccountHoldingsReportRaw(initOverrides);
        return await response.value();
    }

}
