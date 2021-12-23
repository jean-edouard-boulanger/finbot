import React, { useState, useEffect, useContext } from "react";
import { useParams } from "react-router-dom";

import { ServicesContext } from "contexts";
import { TracesTree, TracesTreeNode } from "clients/finbot-client/types";

import AceEditor from "react-ace";
import { Col, Row, Card, Table, Button, Alert, Badge } from "react-bootstrap";
import { FaCube, FaSpinner } from "react-icons/fa";
import { TreeGrid } from "components";

import "ace-builds/src-noconflict/theme-github";
import "ace-builds/src-noconflict/mode-json";
import { TreeGridRowProps } from "components/tree-grid";

import { DateTime } from "luxon";

function ellipsis(text: string, maxLength: number) {
  if (text.length < maxLength) {
    return text;
  }
  return text.slice(0, maxLength) + "...";
}

function formatInlineData(data: any) {
  if (data === null || data === undefined) {
    return "null";
  }
  if (typeof data === "object") {
    return (
      <span>
        <FaCube />
        {" payload"}
      </span>
    );
  }
  if (typeof data === "string") {
    return ellipsis(data, 80);
  }
  return data;
}

function getEditorLanguage({ data }: SelectedData) {
  if (typeof data === "object") {
    return "json";
  }
  return undefined;
}

function getEditorData({ data }: SelectedData) {
  if (typeof data === "object") {
    return JSON.stringify(data, null, 2);
  }
  return `${data}`;
}

function GridRow(clickedCallback: (node: TracesTreeNode) => void) {
  return (props: TreeGridRowProps<TracesTreeNode>) => {
    const node = props.data;
    const nodeData = node.data;
    const duration = DateTime.fromISO(nodeData.end_time).diff(
      DateTime.fromISO(nodeData.start_time),
      "seconds"
    );
    const durationSeconds = duration.toObject().seconds;
    const errorState = node.extra_properties.error_state;
    const className =
      errorState === null
        ? ""
        : errorState === "self"
        ? "bg-danger"
        : "text-danger";
    const metadata = nodeData.metadata;
    return (
      <tr key={nodeData.path} className={className}>
        <td>
          <TreeGrid.Expander {...props} />{" "}
          <Button
            variant="link"
            size="sm"
            className="text-reset"
            onClick={() => clickedCallback(node)}
          >
            {nodeData.name}
          </Button>
        </td>
        <td>
          {metadata.description !== undefined && (
            <Badge variant="primary">{metadata.description}</Badge>
          )}
        </td>
        <td>
          {DateTime.fromISO(nodeData.start_time).toLocaleString(
            DateTime.TIME_WITH_SECONDS
          )}
        </td>
        <td>{nodeData.metadata.origin ?? "N/A"}</td>
        <td>
          {(durationSeconds ?? null) !== null &&
            `${durationSeconds!.toFixed(1)}s`}
          {(durationSeconds ?? null) === null && <FaSpinner />}
        </td>
      </tr>
    );
  };
}

interface LogEntry {
  time: string;
  level: string;
  message: string;
  filename: string;
  line: number;
}

function getLogRowStyle(entry: LogEntry) {
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

interface LogsViewerProps {
  logs: Array<LogEntry>;
}

const LogsViewer: React.FC<LogsViewerProps> = ({ logs }) => {
  return (
    <Table style={{ tableLayout: "fixed", wordWrap: "break-word" }}>
      <tbody>
        {logs.map((entry, index) => {
          return (
            <tr key={`entry-${index}`} className={getLogRowStyle(entry)}>
              <td>{entry.time}</td>
              <td>{entry.level}</td>
              <td style={{ width: "500px" }}>{entry.message}</td>
              <td>{`${entry.filename}:${entry.line}`}</td>
            </tr>
          );
        })}
      </tbody>
    </Table>
  );
};

interface SelectedData {
  key: string;
  data: any | null | undefined;
}

function getInspectorMode(data?: SelectedData | null) {
  if (data === null || data === undefined) {
    return "hint";
  }
  if (data.key === "logs") {
    return "logs";
  }
  return "editor";
}

interface InspectorProps {
  data: SelectedData | null;
}

const Inspector: React.FC<InspectorProps> = ({ data }) => {
  const mode = getInspectorMode(data);
  if (mode === "hint") {
    return <Alert variant="primary">Select a span attribute ...</Alert>;
  } else if (mode === "editor") {
    return (
      <AceEditor
        value={getEditorData(data!)}
        mode={getEditorLanguage(data!)}
        theme="github"
        width="100%"
        showGutter={true}
        showPrintMargin={true}
        readOnly={true}
      />
    );
  } else if (mode === "logs") {
    return <LogsViewer logs={data!.data} />;
  } else {
    return <></>;
  }
};

export const Admin: React.FC<Record<string, never>> = () => {
  const { guid } = useParams<Record<string, string | undefined>>();
  const { finbotClient } = useContext(ServicesContext);
  const [tree, setTree] = useState<TracesTree | null>(null);
  const [selectedSpan, setSelectedSpan] = useState<TracesTreeNode | null>(null);
  const [selectedData, setSelectedData] = useState<SelectedData | null>(null);

  useEffect(() => {
    const impl = async function () {
      const result = await finbotClient!.getTraces({ guid: guid! });
      setTree(result);
    };
    impl();
  }, [finbotClient, guid]);

  useEffect(() => {
    setSelectedData(null);
  }, [selectedSpan]);

  return (
    <>
      <Row className="mb-4">
        <Col>
          <h1>{guid}</h1>
        </Col>
      </Row>
      {tree !== null && (
        <Row>
          <Col lg={6}>
            <Card>
              <Card.Header>Distributed trace</Card.Header>
              <Card.Body>
                <TreeGrid rowAs={GridRow(setSelectedSpan)} tree={tree} />
              </Card.Body>
            </Card>
          </Col>
          <Col>
            <Row>
              <Col>
                <Card>
                  <Card.Header>
                    Span metadata
                    {selectedSpan !== null && ` (${selectedSpan.data.name})`}
                  </Card.Header>
                  <Card.Body>
                    {selectedSpan !== null && (
                      <Table hover size="sm">
                        <tbody>
                          {Object.keys(selectedSpan.data.metadata).map(
                            (key) => {
                              const data = selectedSpan.data.metadata[key];
                              return (
                                <tr key={key}>
                                  <td style={{ width: "25%" }}>
                                    <Button
                                      variant="link"
                                      size="sm"
                                      className="text-reset"
                                      onClick={() =>
                                        setSelectedData({ key, data })
                                      }
                                    >
                                      {key}
                                    </Button>
                                  </td>
                                  <td>
                                    <Button
                                      variant="link"
                                      size="sm"
                                      className="text-reset"
                                      onClick={() =>
                                        setSelectedData({ key, data })
                                      }
                                    >
                                      {formatInlineData(data)}
                                    </Button>
                                  </td>
                                </tr>
                              );
                            }
                          )}
                        </tbody>
                      </Table>
                    )}
                  </Card.Body>
                </Card>
              </Col>
            </Row>
            <Row className="mt-3">
              <Col>
                <Card>
                  <Card.Header>
                    Inspector&nbsp;
                    {selectedData !== null && `(${selectedData.key})`}
                  </Card.Header>
                  <Card.Body>
                    <Inspector data={selectedData} />
                  </Card.Body>
                </Card>
              </Col>
            </Row>
          </Col>
        </Row>
      )}
    </>
  );
};

export default Admin;
