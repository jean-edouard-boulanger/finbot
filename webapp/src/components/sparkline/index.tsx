import React from "react";

import Chart from "react-apexcharts";

const getSparkLineColor = (series: Array<number>): string => {
  const loss_color = "#e34f44";
  const gain_color = "#94e5a3";
  const last = series[series.length - 1];
  if (last < 0) {
    return loss_color;
  }
  const change = last - series[0];
  return change >= 0 ? gain_color : loss_color;
};

export interface SparkLineProps {
  series: Array<number>
}

export const SparkLine: React.FC<SparkLineProps> = (props) => {
  const series = props.series.filter((value) => value !== null);
  return (
    <Chart
      options={{
        chart: {
          sparkline: {
            enabled: true,
          },
          animations: {
            enabled: false,
          },
        },
        colors: [getSparkLineColor(series)],
        xaxis: {
          show: false,
        },
        yaxis: {
          show: false,
        },
        tooltip: {
          x: {
            show: false,
          },
          y: {
            title: {
              formatter: function () {
                return "";
              },
            },
          },
          marker: {
            show: false,
          },
        },
        fill: {
          opacity: 1,
          type: "solid",
        },
        stroke: {
          width: 1.1,
        },
      }}
      series={[
        {
          name: "value",
          data: props.series.filter((value) => value !== null),
        },
      ]}
      type="line"
      width="70px"
      height="20em"
    />
  );
};
