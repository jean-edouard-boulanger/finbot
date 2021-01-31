import React, {useContext, useEffect, useState} from "react";

import { TreeGrid, Money, SparkLine, ValuationChange, StackedBarLoader } from "components";
import { Alert } from "react-bootstrap";
import { FaExclamationCircle } from "react-icons/fa";
import { ServicesContext } from "contexts/services/services-context";


function getRowMetadata(data) {
  if(data.role === "user_account") {
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
      <td colspan="8">
        <TreeGrid.Expander {...rest} />
        <strong>{`${props.label}: `}</strong>{props.value}
      </td>
    </tr>
  )
}

const GridRow = (locale, moneyFormatter) => {
  return (props) => {
    const data = props.data;
    const metadata = getRowMetadata(data);

    if(data.role === "metadata") {
      return <GridMetadataRow {...data} {...props} />
    }

    const valuation = data.valuation;
    const change = valuation.change;
    const sparkline = valuation.sparkline;
    const fontWeight = data.role === "user_account" ? "bold" : null;

    return (
      <tr style={{height: metadata.height, fontWeight}}>
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
          {(sparkline !== undefined) && <SparkLine series={sparkline} />}
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
      <th style={{width: "10em"}}>&nbsp;</th>
      <th>1D</th>
      <th>1W</th>
      <th>1M</th>
      <th>1Y</th>
      <th>2Y</th>
    </tr>
  )
}

export const HoldingsReport = (props) => {
  const {
    accountId,
    locale,
    moneyFormatter
  } = props;

  const {finbotClient} = useContext(ServicesContext);
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetch = async () => {
      try {
        setLoading(true);
        const report = await finbotClient.getHoldingsReport();
        setReport(report);
      }
      catch(e) {
        setError(`${e}`);
      }
      setLoading(false);
    }
    fetch();
  }, [finbotClient, accountId])

  if(error !== null) {
    return (
      <Alert variant={"danger"}>
        <Alert.Heading>
          Snap! An error occurred while generating your report
        </Alert.Heading>
        <p>
          {error}
        </p>
      </Alert>
    )
  }

  if(loading || !report) {
    return (
      <StackedBarLoader
        count={4}
        color={"#FBFBFB"}
        spacing={"0.8em"}
        height={"1em"}
        width={"100%"} />
    )
  }

  return (
    <TreeGrid
      rowAs={GridRow(locale, moneyFormatter)}
      headerAs={Header}
      tree={report.valuation_tree}
      sortBy={(data) => data?.valuation?.value} />
  )
}
