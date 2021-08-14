import React, { useContext, useEffect, useState } from "react";

import { ServicesContext } from "contexts";
import {
  HoldingsReport,
  HoldingsReportMetadataNode,
  HoldingsReportNode,
} from "clients/finbot-client/types";

import {
  TreeGrid,
  Money,
  SparkLine,
  ValuationChange,
  StackedBarLoader,
} from "components";
import { TreeGridRowProps } from "components/tree-grid";
import { MoneyFormatterType } from "components/money";
import { Alert } from "react-bootstrap";

function getRowMetadata(node: HoldingsReportNode) {
  if (node.role === "user_account") {
    return {
      label: "Holdings",
      height: "4em",
    };
  } else if (node.role === "linked_account") {
    return {
      label: node.linked_account.description,
      height: "4em",
    };
  } else if (node.role === "sub_account") {
    return {
      label: node.sub_account.description,
      height: "4em",
    };
  } else if (node.role === "item") {
    return {
      label: node.item.name,
      height: "4em",
    };
  }
}

function getNodeValuation(node: HoldingsReportNode): number | undefined {
  if (node.role !== "metadata") {
    return node.valuation.value;
  }
}

const GridMetadataRow = (
  props: TreeGridRowProps<HoldingsReportMetadataNode>
) => {
  const { data, ...rest } = props;
  return (
    <tr>
      <td colSpan={8}>
        <TreeGrid.Expander {...rest} />
        <strong>{`${data.label}: `}</strong>
        {data.value}
      </td>
    </tr>
  );
};

const GridRow = (locale: string, moneyFormatter: MoneyFormatterType) => {
  return (props: TreeGridRowProps<HoldingsReportNode>) => {
    const node = props.data;
    const metadata = getRowMetadata(node);

    if (node.role === "metadata") {
      const metadataNode: HoldingsReportMetadataNode = node;
      const newProps = { ...props, data: metadataNode };
      return <GridMetadataRow {...newProps} />;
    }

    const valuation = node.valuation;
    const change = valuation.change;
    const sparkline = valuation.sparkline;
    const fontWeight = node.role === "user_account" ? "bold" : undefined;

    return (
      <tr style={{ height: metadata!.height, fontWeight }}>
        <td>
          <TreeGrid.Expander {...props} />
          {metadata!.label}
        </td>
        <td>
          <Money
            amount={valuation.value}
            locale={locale}
            ccy={valuation.currency}
            moneyFormatter={moneyFormatter}
          />
        </td>
        <td>{sparkline !== undefined && <SparkLine series={sparkline} />}</td>
        <td>
          {change ? <ValuationChange amount={change.change_1day} /> : "-"}
        </td>
        <td>
          {change ? <ValuationChange amount={change.change_1week} /> : "-"}
        </td>
        <td>
          {change ? <ValuationChange amount={change.change_1month} /> : "-"}
        </td>
        <td>
          {change ? <ValuationChange amount={change.change_1year} /> : "-"}
        </td>
        <td>
          {change ? <ValuationChange amount={change.change_2years} /> : "-"}
        </td>
      </tr>
    );
  };
};

const Header = () => {
  return (
    <tr>
      <th style={{ width: "40em" }}>&nbsp;</th>
      <th>Value</th>
      <th style={{ width: "10em" }}>&nbsp;</th>
      <th>1D</th>
      <th>1W</th>
      <th>1M</th>
      <th>1Y</th>
      <th>2Y</th>
    </tr>
  );
};

export interface HoldingsReportPanelProps {
  userAccountId: number;
  locale: string;
  moneyFormatter: MoneyFormatterType;
}

export const HoldingsReportPanel: React.FC<HoldingsReportPanelProps> = (
  props
) => {
  const { userAccountId, locale, moneyFormatter } = props;

  const { finbotClient } = useContext(ServicesContext);
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<HoldingsReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetch = async () => {
      try {
        setLoading(true);
        const report = await finbotClient!.getHoldingsReport();
        setReport(report);
      } catch (e) {
        setError(`${e}`);
      }
      setLoading(false);
    };
    fetch();
  }, [finbotClient, userAccountId]);

  if (error !== null) {
    return (
      <Alert variant={"danger"}>
        <Alert.Heading>
          Snap! An error occurred while generating your report
        </Alert.Heading>
        <p>{error}</p>
      </Alert>
    );
  }

  if (loading || !report) {
    return (
      <StackedBarLoader
        count={4}
        color={"#FBFBFB"}
        spacing={"0.8em"}
        height={"1em"}
        width={"100%"}
      />
    );
  }

  return (
    <TreeGrid
      rowAs={GridRow(locale, moneyFormatter)}
      headerAs={Header}
      tree={report!.valuation_tree as HoldingsReportNode}
      sortBy={(node) => getNodeValuation(node) ?? Number.MIN_VALUE}
    />
  );
};
