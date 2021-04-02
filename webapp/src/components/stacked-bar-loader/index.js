import React from "react";

import { BarLoader } from "react-spinners";


const DEFAULT_COUNT = 3;
const DEFAULT_SPACING = "0.5em";

export const StackedBarLoader = (props) => {
  const {
    count = DEFAULT_COUNT,
    spacing = DEFAULT_SPACING,
    ...rest
  } = props;
  const range = Array.from(Array(count).keys())
  return (
    <div>
      {
        (range.map((_, index) => {
          return (
            <div key={`loader-${index}`} style={{marginBottom: spacing}} >
              <BarLoader {...rest} />
            </div>
          )
        }))
      }
    </div>
  )
}
