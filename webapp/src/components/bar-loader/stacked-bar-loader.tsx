import React from "react";

import { BarLoader } from "./bar-loader";
import { LoaderHeightWidthProps } from "react-spinners/helpers/props";

const DEFAULT_COUNT = 3;
const DEFAULT_SPACING = "0.5em";

export interface StackedBarLoaderProps {
  count?: number;
  spacing?: string | number;
}

export const StackedBarLoader: React.FC<
  StackedBarLoaderProps & LoaderHeightWidthProps
> = (props) => {
  const { count = DEFAULT_COUNT, spacing = DEFAULT_SPACING, ...rest } = props;
  const range = Array.from(Array(count).keys());
  return (
    <div>
      {range.map((_, index) => {
        return (
          <div key={`loader-${index}`} style={{ marginBottom: spacing }}>
            <BarLoader {...rest} />
          </div>
        );
      })}
    </div>
  );
};
