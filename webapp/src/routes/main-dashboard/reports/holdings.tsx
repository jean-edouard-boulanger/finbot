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

import { TreeGrid, Money, ValuationChange } from "components";
import { TreeGridRowProps } from "components/tree-grid";
import { MoneyFormatterType } from "components/money";
import { Alert, AlertTitle, AlertDescription } from "components/ui/alert";

export type HoldingsReportNode =
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
    <tr className="text-muted-foreground">
      <td colSpan={7}>
        <>
          <TreeGrid.Expander {...rest} />
          <strong className="text-foreground">{`${data.label}: `}</strong>
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
      className="mr-2 inline-block rounded text-center text-xs font-bold text-white"
      style={{
        width: "2.35em",
        backgroundColor: props.icon.backgroundColour,
        paddingTop: "0.2em",
        paddingBottom: "0.2em",
      }}
    >
      {props.icon.label}
    </span>
  );
};

export const GridRow = (
  locale: string,
  moneyFormatter: MoneyFormatterType,
): ((props: TreeGridRowProps<HoldingsReportNode>) => React.JSX.Element) => {
  return (props: TreeGridRowProps<HoldingsReportNode>): React.JSX.Element => {
    const node = props.data;
    const metadata = getRowMetadata(node);

    if (node.role === "metadata") {
      const newProps = { ...props, data: node };
      return <GridMetadataRow {...newProps} />;
    }

    const valuation = getNodeValuation(node)!;
    const change = valuation.change;
    const fontWeight = node.role === "user_account" ? "bold" : undefined;

    return (
      <tr
        style={{ height: metadata!.height, fontWeight }}
        className="border-b border-border/30 transition-colors hover:bg-secondary/30"
      >
        <td>
          <TreeGrid.Expander {...props} />
          {node.role == "item" && node.item.icon && (
            <ItemIcon icon={node.item.icon} />
          )}
          {`${metadata!.label}`}
        </td>
        <td className="font-mono tabular-nums">
          <Money
            amount={valuation.value}
            locale={locale}
            ccy={valuation.currency}
            moneyFormatter={moneyFormatter}
          />
        </td>
        <td className="font-mono tabular-nums">
          {change ? <ValuationChange amount={change.change1day} /> : "-"}
        </td>
        <td className="font-mono tabular-nums">
          {change ? <ValuationChange amount={change.change1week} /> : "-"}
        </td>
        <td className="font-mono tabular-nums">
          {change ? <ValuationChange amount={change.change1month} /> : "-"}
        </td>
        <td className="font-mono tabular-nums">
          {change ? <ValuationChange amount={change.change1year} /> : "-"}
        </td>
        <td className="font-mono tabular-nums">
          {change ? <ValuationChange amount={change.change2years} /> : "-"}
        </td>
      </tr>
    );
  };
};

export const Header = (): React.JSX.Element => {
  return (
    <tr className="border-b border-border/50">
      <th
        style={{ width: "40em" }}
        className="text-left text-xs font-medium uppercase tracking-wider text-muted-foreground"
      >
        &nbsp;
      </th>
      <th className="text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
        Value
      </th>
      <th className="text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
        1D
      </th>
      <th className="text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
        1W
      </th>
      <th className="text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
        1M
      </th>
      <th className="text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
        1Y
      </th>
      <th className="text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
        2Y
      </th>
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
      <Alert variant="destructive">
        <AlertTitle>
          Snap! An error occurred while generating your report
        </AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  if (loading || !report) {
    return (
      <div className="space-y-3 py-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="skeleton-shimmer h-10 rounded" />
        ))}
      </div>
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
