import Chart from "react-apexcharts";
import React from "react";


const getSparkLineColor = (series) => {
  const loss_color = "#e34f44";
  const gain_color = "#94e5a3";
  const last = series[series.length - 1];
  if(last < 0) {
    return loss_color;
  }
  const change = last - series[0];
  return (change >= 0) ? gain_color : loss_color;
}

export const SparkLine = (props) => {
  const series = props.series.filter((value) => value !== null);
  return (
    <Chart
      options={{
        chart: {
          sparkline: {
            enabled: true
          },
          animations: {
            enabled: false
          }
        },
        colors: [getSparkLineColor(series)],
        xaxis: {},
        yaxis: {},
        tooltip: {
          fixed: {
            enabled: false
          },
          x: {
            show: false
          },
          y: {
            title: {
              formatter: function () {
                return '';
              }
            }
          },
          marker: {
            show: false
          }
        },
        fill: {
          opacity: 1,
          type: "solid"
        },
        stroke: {
          width: 1.1,
        }
      }}
      series={[
        {
          name: "value",
          data: props.series.filter((value) => value !== null)
        }
      ]}
      type="line"
      width="70px"
      height="20em"
    />
  )
}
