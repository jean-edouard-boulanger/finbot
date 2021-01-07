import React, {useState, useEffect} from 'react';
import AceEditor from "react-ace";
import "ace-builds/src-noconflict/theme-github";
import "ace-builds/src-noconflict/mode-json";
import {Col, Row, Card, Table, Button, Alert, Badge} from 'react-bootstrap';
import {useParams} from 'react-router-dom';
import {FaCube} from 'react-icons/fa';

import TreeGrid from 'components/tree-grid';
import FinbotClient from "clients/finbot-client";

const {DateTime} = require('luxon');

function hasError(node) {
  return node.metadata.error !== undefined;
}

function backPropagateError(node) {
  while (node.parent !== undefined) {
    node = node.parent;
    if (node.error !== null) {
      break;
    }
    node.error = 'inherit';
  }
}

function buildTree(traces) {
  const mappedTraces = {};
  let root = null;
  traces.forEach((t) => {
    t.prettyPath = t.path.join('.');
    t.children = []
    t.error = null;
    mappedTraces[t.prettyPath] = t
    if (t.path.length === 1) {
      root = t;
    }
  });
  traces.forEach((t) => {
    const parentPath = t.path.slice(0, -1);
    const prettyParentPath = parentPath.join('.');
    const parent = mappedTraces[prettyParentPath];
    if (parent !== undefined) {
      t.parent = parent;
      parent.children.push(t);
    }
  });
  traces.forEach((t) => {
    if (t.error === undefined) {
      t.error = null;
    }
    if (hasError(t)) {
      t.error = 'self';
      backPropagateError(t);
    }
  });
  return root;
}

function ellipsis(text, max) {
  if (text.length < max) {
    return text;
  }
  return text.slice(0, max) + "..."
}

function formatInlineData(data) {
  if (data === null || data === undefined) {
    return 'null';
  }
  if (typeof (data) === 'object') {
    return <span><FaCube/>{' payload'}</span>;
  }
  if (typeof (data) === 'string') {
    return ellipsis(data, 80);
  }
  return data;
}

function getEditorLanguage(data) {
  if (data === null || data === undefined) {
    return null;
  }
  if (typeof (data) === 'object') {
    return "json";
  }
  return null;
}

function getEditorData(data) {
  const payload = data[1];
  if (typeof (payload) === 'object') {
    return JSON.stringify(payload, null, 2);
  }
  return `${payload}`
}

function GridRow(callback) {
  return (props) => {
    const data = props.data;
    const duration = data.end_time.diff(data.start_time, 'seconds');
    const durationSeconds = duration.toObject().seconds;
    const className = data.error === null
      ? '' : (data.error === 'self' ? 'bg-danger' : 'text-danger');
    const metadata = data.metadata;
    return (
      <tr key={data.pretty_path} className={className}>
        <td>
          <TreeGrid.Expander {...props} />{' '}
          <Button variant="link" size="sm" className="text-reset" onClick={() => callback(data)}>
            {data.name}
          </Button>
        </td>
        <td>
          {metadata.description !== undefined && <Badge variant="primary">{metadata.description}</Badge>}
        </td>
        <td>
          {data.start_time.toLocaleString(DateTime.TIME_WITH_SECONDS)}
        </td>
        <td>
          {data.metadata.origin}
        </td>
        <td>
          {
            (durationSeconds ?? null) !== null
              && `${durationSeconds.toFixed(1)}s`
          }
          {
            (durationSeconds ?? null) === null
              && `N/A`
          }
        </td>
      </tr>
    )
  };
}


function getLogRowStyle(entry) {
  if (entry.level === "FATAL") {
    return "bg-dark";
  }
  if (entry.level === "ERROR") {
    return "bg-error";
  }
  if (entry.level === "WARNING") {
    return "bg-warning";
  }
  return "bg-white";
}


function LogsViewer({logs}) {
  return (
    <Table style={{tableLayout: 'fixed', wordWrap: 'break-word'}}>
      <tbody>
      {
        logs.map((entry) => {
          return (
            <tr className={getLogRowStyle(entry)}>
              <td>{entry.time}</td>
              <td>{entry.level}</td>
              <td style={{width: '500px'}}>{entry.message}</td>
              <td>{`${entry.filename}:${entry.line}`}</td>
            </tr>
          )
        })
      }
      </tbody>
    </Table>
  )
}


function getInspectorMode(data) {
  if (data === null || data === undefined) {
    return "hint";
  }
  const key = data[0];
  if (key === "logs") {
    return "logs";
  }
  return "editor";
}


function Inspector({data}) {
  const mode = getInspectorMode(data);
  if (mode === "hint") {
    return (
      <Alert variant="primary">Select a span attribute ...</Alert>
    )
  } else if (mode === "editor") {
    return (
      <AceEditor value={getEditorData(data)}
                 mode={getEditorLanguage(data)}
                 theme="github"
                 width="100%"
                 showGutter={true}
                 showPrintMargin={true}
                 readOnly={true}/>
    )
  } else if (mode === "logs") {
    return <LogsViewer logs={data[1]}/>
  }
}

export default function Admin() {
  const {guid} = useParams();
  const [tree, setTree] = useState(null);
  const [selectedSpan, setSelectedSpan] = useState(null);
  const [selectedData, setSelectedData] = useState(null);

  useEffect(() => {
    const impl = async function () {
      const client = new FinbotClient();
      const response = await client.getTraces({guid});
      response.traces.forEach((t) => {
        t.start_time = DateTime.fromISO(t.start_time);
        t.end_time = DateTime.fromISO(t.end_time);
      });
      setTree(buildTree(response.traces));
    }
    impl();
  }, [guid]);

  useEffect(() => {
    if (selectedData !== null) {
      const key = selectedData[0];
      if (selectedSpan.metadata[key] !== undefined) {
        setSelectedData([key, selectedSpan.metadata[key]]);
        return;
      }
    }
    setSelectedData(null);
  }, [selectedSpan, selectedData])

  return (
    <>
      <Row className="mb-4">
        <Col><h1>{guid}</h1></Col>
      </Row>
      {(tree !== null) &&
      <Row>
        <Col lg={6}>
          <Card>
            <Card.Header>Distributed trace</Card.Header>
            <Card.Body>
              <TreeGrid rowAs={GridRow(setSelectedSpan)}
                        tree={tree}/>
            </Card.Body>
          </Card>
        </Col>
        <Col>
          <Row>
            <Col>
              <Card>
                <Card.Header>Span metadata{selectedSpan !== null && ` (${selectedSpan.name})`}</Card.Header>
                <Card.Body>
                  {selectedSpan !== null &&
                  <Table hover size="sm">
                    <tbody>
                    {
                      Object.keys(selectedSpan.metadata).map((k) => {
                        const data = selectedSpan.metadata[k];
                        return (
                          <tr key={k}>
                            <td style={{width: '25%'}}>
                              <Button variant="link" size="sm" className="text-reset"
                                      onClick={() => setSelectedData([k, data])}>
                                {k}
                              </Button>
                            </td>
                            <td>
                              <Button variant="link" size="sm" className="text-reset"
                                      onClick={() => setSelectedData([k, data])}>
                                {formatInlineData(data)}
                              </Button>
                            </td>
                          </tr>
                        )
                      })
                    }
                    </tbody>
                  </Table>
                  }
                </Card.Body>
              </Card>
            </Col>
          </Row>
          <Row className="mt-3">
            <Col>
              <Card>
                <Card.Header>Inspector{selectedData !== null && ` (${selectedData[0]})`}</Card.Header>
                <Card.Body>
                  <Inspector data={selectedData}/>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </Col>
      </Row>
      }
    </>
  )
}
