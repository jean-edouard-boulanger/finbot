import React, { useEffect, useState } from "react";

import {
  useApi,
  UserAccountsReportsApi,
  ValuationTree,
  UserAccountNode,
  LinkedAccountNode,
  SubAccountNode,
  SubAccountItemNode,
  SubAccountItemMetadataNode,
  SubAccountItemNodeIcon,
  Valuation,
} from "clients";

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

type HoldingsReportNode =
  | UserAccountNode
  | LinkedAccountNode
  | SubAccountNode
  | SubAccountItemNode
  | SubAccountItemMetadataNode;

function getRowMetadata(node: HoldingsReportNode) {
  if (node.role === "user_account") {
    return {
      label: "Holdings",
      height: "4em",
    };
  } else if (node.role === "linked_account") {
    return {
      label: node.linkedAccount.description,
      height: "4em",
    };
  } else if (node.role === "sub_account") {
    return {
      label: node.subAccount.description,
      height: "3.5em",
    };
  } else if (node.role === "item") {
    return {
      label: node.item.name,
      height: "3em",
    };
  }
}

function getNodeValuation(node: HoldingsReportNode): Valuation | undefined {
  if ("valuation" in node) {
    return node.valuation;
  }
}

const GridMetadataRow = (
  props: TreeGridRowProps<SubAccountItemMetadataNode>,
) => {
  const { data, ...rest } = props;
  return (
    <tr>
      <td colSpan={8}>
        <>
          <TreeGrid.Expander {...rest} />
          <strong>{`${data.label}: `}</strong>
          {data.value}
        </>
      </td>
    </tr>
  );
};

interface ItemIconProps {
  icon: SubAccountItemNodeIcon;
}

const ItemIcon = (props: ItemIconProps) => {
  return (
    <span
      style={{
        display: "inline-block",
        width: "2.35em",
        textAlign: "center",
        color: "white",
        backgroundColor: props.icon.backgroundColour,
        paddingTop: "0.2em",
        paddingBottom: "0.2em",
        marginRight: "0.5em",
      }}
    >
      <strong>{props.icon.label}</strong>
    </span>
  );
};

const GridRow = (locale: string, moneyFormatter: MoneyFormatterType) => {
  return (props: TreeGridRowProps<HoldingsReportNode>) => {
    const node = props.data;
    const metadata = getRowMetadata(node);

    if (node.role === "metadata") {
      const newProps = { ...props, data: node };
      return <GridMetadataRow {...newProps} />;
    }

    const valuation = getNodeValuation(node)!;
    const change = valuation.change;
    const sparkline =
      "sparkline" in valuation ? valuation.sparkline : undefined;
    const fontWeight = node.role === "user_account" ? "bold" : undefined;

    return (
      <tr style={{ height: metadata!.height, fontWeight }}>
        <td>
          <TreeGrid.Expander {...props} />
          {node.role == "item" && node.item.icon && (
            <ItemIcon icon={node.item.icon} />
          )}
          {`${metadata!.label}`}
        </td>
        <td>
          <Money
            amount={valuation.value}
            locale={locale}
            ccy={valuation.currency}
            moneyFormatter={moneyFormatter}
          />
        </td>
        <td>
          {sparkline !== undefined && <SparkLine series={sparkline as any} />}
        </td>
        <td>{change ? <ValuationChange amount={change.change1day} /> : "-"}</td>
        <td>
          {change ? <ValuationChange amount={change.change1week} /> : "-"}
        </td>
        <td>
          {change ? <ValuationChange amount={change.change1month} /> : "-"}
        </td>
        <td>
          {change ? <ValuationChange amount={change.change1year} /> : "-"}
        </td>
        <td>
          {change ? <ValuationChange amount={change.change2years} /> : "-"}
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
  props,
) => {
  const { userAccountId, locale, moneyFormatter } = props;

  const userAccountsReportsApi = useApi(UserAccountsReportsApi);
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<ValuationTree | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetch = async () => {
      try {
        setLoading(true);
        const result =
          await userAccountsReportsApi.getUserAccountHoldingsReport();
        setReport(result.report);
      } catch (e) {
        setError(`${e}`);
      }
      setLoading(false);
    };
    fetch();
  }, [userAccountsReportsApi, userAccountId]);

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
      tree={report.valuationTree as HoldingsReportNode}
      sortBy={(node) => getNodeValuation(node)?.value ?? Number.MIN_VALUE}
    />
  );
};
