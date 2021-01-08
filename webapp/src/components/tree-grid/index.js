import React, { useState, useEffect } from 'react';
import { Table } from 'react-bootstrap';
import { FaCaretDown, FaCaretRight } from 'react-icons/fa';


function topologicalSort(tree, sortBy) {
  function dfs(node, res, level, order) {
    res.push({
      data: node,
      level,
      order
    });
    let cOrder = 0;
    (node.children ?? []).sort((c1, c2) => {
      return sortBy(c2) - sortBy(c1);
    }).forEach((c) => {
      dfs(c, res, level + 1, cOrder);
      cOrder += 1;
    });
  }
  let output = [];
  dfs(tree, output, 0, 0);
  return output;
}

function configureModel(topology, expanded) {
  let id = 0;
  topology.forEach((node) => {
    node.id = id++;
    node.expanded = (expanded) ? true : node.level < 1;
    node.visible = (expanded) ? true : node.level <= 1;
  });
  return topology;
}

function refreshModel(model) {
  let displayLimit = null;
  model.forEach((node) => {
    if (displayLimit === null) { node.visible = true; }
    else if (node.level <= displayLimit) {
      node.visible = true;
      displayLimit = null;
    }
    else if (node.level > displayLimit) {
      node.visible = false;
    }
    if (!node.expanded && displayLimit === null) {
      displayLimit = node.level;
    }
  });
}

function getExpanderIcon(node) {
  if ((node.data.children ?? []).length === 0) { return () => null }
  if (node.expanded) { return FaCaretDown; }
  return FaCaretRight;
}

function Expander (props) {
  const self = props.__expander;
  const level = self.level;
  const leaf = self.leaf;
  const offset = (leaf) ? 20 : 0;
  const style = {
    marginLeft: `${level * 20 + offset}px`,
    marginRight: "5px"
  }
  return (
    <span style={style}>
      <self.Icon onClick={self.cb} />
    </span>
  );
}

export default function TreeGrid(props) {
  const {
    tree,
    sortBy = (() => 0),
    expanded = false,
  } = props;
  const Row = props.rowAs;
  const Header = props.headerAs;

  const [model, setModel] = useState(null);

  useEffect(() => {
    const topology = topologicalSort(tree, sortBy);
    setModel(configureModel(topology, expanded));
  }, [tree, expanded]);

  function onNodeExpandClick(node) {
    node.expanded = !node.expanded;
    refreshModel(model);
    setModel([...model]);
  }

  if (model === null) {
    return <strong>Loading ...</strong>;
  }

  return (
    <Table hover size="sm">
      {
        ((Header ?? null) !== null) &&
          <thead>
            <Header />
          </thead>
      }
      <tbody>
        {
          model.filter(n => n.visible).map((n) => {
            const rowProps = {
              data: n.data,
              __expander: {
                Icon: getExpanderIcon(n),
                level: n.level,
                leaf: ((n.data.children ?? []).length === 0),
                cb: () => { onNodeExpandClick(n) }
              }
            };
            return <Row key={n.id} {...rowProps} />
          })
        }
      </tbody>
    </Table>
  );
}

TreeGrid.Expander = Expander;