import React from 'react';
import ReactDOM from 'react-dom';
import { Router } from 'react-router-dom';
import { createBrowserHistory } from "history";

import App from "./App"

const hist = createBrowserHistory();

ReactDOM.render(
    <Router history={hist}>
        <App />
    </Router>,
    document.getElementById('root'));