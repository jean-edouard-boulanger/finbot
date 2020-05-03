import React, { useState, useEffect } from 'react';
import { Container, Col, Row, Table, Card } from 'react-bootstrap';
import { useParams } from 'react-router-dom';
import BarLoader from "react-spinners/BarLoader";
import SyntaxHighlighter from 'react-syntax-highlighter';

import FinbotClient from "clients/finbot-client";


function TracesTable({traces, onPathClick}) {
    return (
        <Table hover size="sm">
            <tbody>
                {
                    traces.map((span) => {
                        const path = span.path.join(".");
                        const hasError = span.metadata.hasOwnProperty("error");
                        const rowClass = hasError ? "bg-danger" : "";
                        return (
                            <tr className={rowClass} onClick={(e)=>{onPathClick(span)}}>
                                <td>{path}</td>
                                <td>{span.name}</td>
                                <td>{span.start_time}</td>
                                <td>{span.end_time}</td>
                            </tr>
                        )
                    })
                }
            </tbody>
        </Table>
    );
}


function TraceViewer({trace}) {
    const error = trace.metadata.output;
    return (
        <Card>
            <Card.Header>{trace.name}</Card.Header>
            <Card.Body>{}
                <SyntaxHighlighter>
                    {error === undefined ? "no error" : JSON.stringify(error, null, 2)}
                </SyntaxHighlighter>
            </Card.Body>
        </Card>
    )
}


function getTopology(path) {
    const level = path.length;
    return {level, order: path[level - 1]}
}


export default function Admin(props) {
    let {guid} = useParams();
    let [traces, setTraces] = useState(null);
    let [selectedSpan, setSelectedSpan] = useState(null);

    useEffect(() => {
        const impl = async function() {
            const client = new FinbotClient();
            const response = await client.getTraces({guid});
            setTraces(response.traces);
        }
        impl();
    }, [guid]);

    return (
        <div className="main-wrapper">
            <Container>
                <Row className="mb-4">
                    <Col><h1>{guid}</h1></Col>
                </Row>
                <Row className="mb-4"> 
                    <Col>
                    {(traces === null) &&
                        <BarLoader color={"#F0F0F0"} />
                    }
                    {(traces !== null) &&
                        <Card>
                            <Card.Header>Traces ({traces.length})</Card.Header>
                            <Card.Body>
                                <div style={{maxHeight: '500px', overflow: 'auto'}}>
                                    <TracesTable traces={traces}
                                                onPathClick={setSelectedSpan} />
                                </div>
                            </Card.Body>
                        </Card>
                    }
                    </Col>
                </Row>
                <Row className="mb-4">
                    <Col>
                    {(selectedSpan !== null) &&
                        <TraceViewer trace={selectedSpan} />
                    }
                    </Col>
                </Row>
            </Container>
        </div>
    )
}
