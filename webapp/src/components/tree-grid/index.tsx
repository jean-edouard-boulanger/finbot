import React, { useState, useEffect } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";

import {
  Table,
  TableBody,
  TableHeader,
} from "components/ui/table";

interface TreeNodeWithChildren<NodeType> {
  children: Array<NodeType>;
}

interface TreeNodeWithoutChildren {}

type TreeNode<NodeType> =
  | TreeNodeWithChildren<NodeType>
  | TreeNodeWithoutChildren;

interface InternalTreeNode<UserNodeType> {
  id: number;
  level: number;
  order: number;
  expanded: boolean;
  visible: boolean;
  data: UserNodeType;
}

type Topology<UserNodeType extends TreeNode<UserNodeType>> = Array<
  InternalTreeNode<UserNodeType>
>;

export type SortBy<UserNodeType> = (node: UserNodeType) => number;

function getChildren<NodeType>(node: TreeNode<NodeType>): Array<NodeType> {
  if ("children" in node) {
    return node.children;
  }
  return [];
}

function topologicalSort<UserNodeType extends TreeNode<UserNodeType>>(
  tree: UserNodeType,
  sortBy: SortBy<UserNodeType>,
  expanded: boolean,
): Topology<UserNodeType> {
  let idAlloc = 0;
  function dfs(
    node: UserNodeType,
    res: Array<InternalTreeNode<UserNodeType>>,
    level: number,
    order: number,
  ): void {
    res.push({
      id: idAlloc++,
      level,
      order,
      expanded: expanded || level < 1,
      visible: expanded || level <= 1,
      data: node,
    });
    let cOrder = 0;
    [...getChildren(node)]
      .sort((c1, c2) => {
        return sortBy(c2) - sortBy(c1);
      })
      .forEach((c) => {
        dfs(c, res, level + 1, cOrder);
        cOrder += 1;
      });
  }
  const topology: Topology<UserNodeType> = [];
  dfs(tree, topology, 0, 0);
  return topology;
}

function refreshTopology<UserNodeType extends TreeNode<UserNodeType>>(
  topology: Topology<UserNodeType>,
): void {
  let displayLimit: number | null = null;
  topology.forEach((node) => {
    if (displayLimit === null) {
      node.visible = true;
    } else if (node.level <= displayLimit) {
      node.visible = true;
      displayLimit = null;
    } else if (node.level > displayLimit) {
      node.visible = false;
    }
    if (!node.expanded && displayLimit === null) {
      displayLimit = node.level;
    }
  });
}

function getExpanderIcon<UserNodeType extends TreeNode<UserNodeType>>(
  node: InternalTreeNode<UserNodeType>,
) {
  if (getChildren(node.data).length === 0) {
    return () => null;
  }
  if (node.expanded) {
    return ChevronDown;
  }
  return ChevronRight;
}

interface ExpanderSelfProps {
  level: number;
  leaf: boolean;
  cb(): void;
  Icon: any;
}

interface ExpanderProps {
  __expander: ExpanderSelfProps;
}

const Expander: React.FC<ExpanderProps> = (props) => {
  const self = props.__expander;
  const level = self.level;
  const leaf = self.leaf;
  const offset = leaf ? 20 : 0;
  const style = {
    marginLeft: `${level * 20 + offset}px`,
    marginRight: "5px",
  };
  return (
    <span style={style} className="inline-flex cursor-pointer">
      <self.Icon className="h-4 w-4" onClick={self.cb} />
    </span>
  );
};

export interface TreeGridProps<UserNodeType extends TreeNode<UserNodeType>> {
  tree: UserNodeType;
  sortBy?: SortBy<UserNodeType>;
  expanded?: boolean;
  rowAs: any;
  headerAs?: any | null;
}

export type TreeGridRowProps<UserNodeType extends TreeNode<UserNodeType>> =
  ExpanderProps & {
    data: UserNodeType;
  };

export function TreeGrid<UserNodeType extends TreeNode<UserNodeType>>(
  props: TreeGridProps<UserNodeType>,
): JSX.Element {
  const { tree, sortBy = () => 0, expanded = false } = props;
  const Row = props.rowAs;
  const Header = props.headerAs;

  const [topology, setTopology] = useState<Topology<UserNodeType> | null>(null);

  useEffect(() => {
    setTopology(topologicalSort(tree, sortBy, expanded));
  }, [tree, expanded]);

  function onNodeExpandClick(node: InternalTreeNode<UserNodeType>) {
    node.expanded = !node.expanded;
    refreshTopology(topology!);
    setTopology([...topology!]);
  }

  if (topology === null) {
    return <strong>Loading ...</strong>;
  }

  return (
    <Table>
      {(Header ?? null) !== null && (
        <TableHeader>
          <Header />
        </TableHeader>
      )}
      <TableBody>
        {topology
          .filter((n) => n.visible)
          .map((n) => {
            const rowProps: TreeGridRowProps<UserNodeType> = {
              data: n.data,
              __expander: {
                Icon: getExpanderIcon(n),
                level: n.level,
                leaf: getChildren(n.data).length === 0,
                cb: () => {
                  onNodeExpandClick(n);
                },
              },
            };
            return <Row key={n.id} {...rowProps} />;
          })}
      </TableBody>
    </Table>
  );
}

TreeGrid.Expander = Expander;

export default TreeGrid;
