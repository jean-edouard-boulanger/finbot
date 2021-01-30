import React from "react";

import { TreeGrid, Money, ValuationChange } from 'components';
import { FaExclamationCircle } from 'react-icons/fa';
import Chart from "react-apexcharts";
import {Card} from "react-bootstrap";


function getRowMetadata(totalValuation, data) {
  if(data.role === "_root") {
    return {
      label: "Holdings",
      height: "4em"
    }
  }
  else if(data.role === "linked_account") {
    return {
      label: data.linked_account.description,
      height: "4em",
    }
  }
  else if(data.role === "sub_account") {
    return {
      label: data.sub_account.description,
      height: "4em"
    }
  }
  else if(data.role === "item") {
    return {
      label: data.item.name,
      height: "4em"
    }
  }
}

const GridMetadataRow = (props) => {
  const {label, value, ...rest} = props;
  return (
    <tr>
      <td>
        <TreeGrid.Expander {...rest} />
        <strong>{`${props.label}: `}</strong>{props.value}
      </td>
      <td>&nbsp;</td>
      <td>&nbsp;</td>
      <td>&nbsp;</td>
      <td>&nbsp;</td>
      <td>&nbsp;</td>
      <td>&nbsp;</td>
    </tr>
  )
}

const getSparkLineColor = (diff) => {
  if(diff === 0) {
    return "#cccccc";
  }
  else if(diff > 0) {
    return "#6cbc7b";
  }
  else {
    return "#ca5c54";
  }
}

const SparkLine = (props) => {
  const series = props.series.filter((value) => value !== null);
  const change = series[series.length - 1] - series[0];
  console.log(change);
  return (
    <Chart
      options={{
        chart: {
          sparkline: {
            enabled: true
          }
        },
        colors: [getSparkLineColor(change)],
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
          opacity: 0.5,
          type: "solid"
        },
        stroke: {
          width: 1.5,
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

const GridRow = (locale, moneyFormatter, totalValuation) => {
  return (props) => {
    const data = props.data;
    const metadata = getRowMetadata(totalValuation, data);

    if(data.role === "metadata") {
      return <GridMetadataRow {...data} {...props} />
    }

    const valuation = data.valuation;
    const change = valuation.change;
    const sparkline = valuation.sparkline;

    return (
      <tr style={{height: metadata.height}}>
        <td>
          <TreeGrid.Expander {...props} />{metadata.label}{" "}
          {
            (metadata.warning !== undefined) &&
                <FaExclamationCircle />
          }
        </td>
        <td>
          <Money
            amount={valuation.value}
            locale={locale}
            ccy={valuation.currency}
            moneyFormatter={moneyFormatter} />
        </td>
        <td>
          {(sparkline !== undefined) && <SparkLine series={sparkline.map((item) => item.value)} />}
        </td>
        <td>{change ? <ValuationChange amount={change.change_1day}/> : "-"}</td>
        <td>{change ? <ValuationChange amount={change.change_1week}/> : "-"}</td>
        <td>{change ? <ValuationChange amount={change.change_1month}/> : "-"}</td>
        <td>{change ? <ValuationChange amount={change.change_1year}/> : "-"}</td>
        <td>{change ? <ValuationChange amount={change.change_2years}/> : "-"}</td>
      </tr>
    )
  }
}

const Header = () => {
  return (
    <tr>
      <th style={{width: "40em"}}>&nbsp;</th>
      <th>Value</th>
      <th>&nbsp;</th>
      <th>1D</th>
      <th>1W</th>
      <th>1M</th>
      <th>1Y</th>
      <th>2Y</th>
    </tr>
  )
}

const ValuationTree = (props) => {
  const {
    linkedAccounts,
    locale,
    moneyFormatter,
    valuation,
  } = props;

  const tree = {
    role: "_root",
    children: linkedAccounts,
    valuation
  };

  console.log(linkedAccounts);

  return (
    <TreeGrid
      rowAs={GridRow(locale, moneyFormatter, valuation)}
      headerAs={Header}
      tree={tree}
      sortBy={(data) => (data.valuation ?? {}).value}  />
  );
}

export default ValuationTree;
export { ValuationTree };
