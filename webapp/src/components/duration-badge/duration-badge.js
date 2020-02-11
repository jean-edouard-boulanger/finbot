import React from 'react';
import PropTypes from "prop-types";

class DurationBadge extends React.Component {
    constructor(props) {
        super(props);
        this.props = props;
        this.interval = null;
        this.state = {
            elapsed: 0
        };
    }

    refreshDuration() {
        const {
            from,
            to = (new Date())
        } = this.props;

        this.setState({
            elapsed: (to.getTime() / 1000.0) - (from.getTime() / 1000.0)
        })
    }

    componentDidMount() {
        if (this.props.to === undefined) {
            this.interval = setInterval(() => this.refreshDuration(), 10 * 1000);
        }
        this.refreshDuration();
    }

    componentWillUnmount() {
        clearInterval(this.interval);
        this.interval = null;
    }

    render() {
        const {
            nowLimit = 60.0,
            secondsLimit = 60.0,
            minutesLimit = 3600.0,
            hoursLimit = 3600.0 * 48.0
        } = this.props

        function formatDuration(d) {
            const nowFmt = (_) => "now";
            const secondsFmt = (val) => `${Math.trunc(val)}s ago`;
            const minutesFmt = (val) => `${Math.trunc(val / 60.0)}m ago`;
            const hoursFmt = (val) => `${Math.trunc(val / 3600.0)}h ago`;
            const daysFmt = (val) => `${Math.trunc(val / (3600.0 * 24))}d ago`;

            switch (true) {
                case (d < nowLimit): return nowFmt(d);
                case (d >= nowLimit && d < secondsLimit): return secondsFmt(d);
                case (d >= secondsLimit && d < minutesLimit): return minutesFmt(d);
                case (d >= minutesLimit && d < hoursLimit): return hoursFmt(d);
                default: return daysFmt(d);
            }
        }

        return (<span className="badge badge-secondary">{formatDuration(this.state.elapsed)}</span>)
    }
}

DurationBadge.propTypes = {
    from: PropTypes.instanceOf(Date)
};

export { DurationBadge };