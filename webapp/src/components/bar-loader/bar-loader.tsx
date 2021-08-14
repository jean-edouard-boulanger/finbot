import React from "react";

import { BarLoader as BarLoaderImpl } from "react-spinners";
import { LoaderHeightWidthProps } from "react-spinners/interfaces";

import { DEFAULT_BACKGROUND_COLOR } from "./constants";

export interface StackedBarLoaderProps {}

export const BarLoader: React.FC<
  StackedBarLoaderProps & LoaderHeightWidthProps
> = (props) => {
  return (
    <div style={{display: "flex"}}>
      <BarLoaderImpl color={DEFAULT_BACKGROUND_COLOR} {...props} />
    </div>
  );
};
