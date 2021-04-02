import React, { useState, useEffect } from "react";

const limits = {
  now: 60.0,
  seconds: 60.0,
  minutes: 3600.0,
  hours: 3600.0 * 48.0,
};

const formatDuration = (d) => {
  const nowFmt = () => "now";
  const secondsFmt = (val) => `${Math.trunc(val)}s ago`;
  const minutesFmt = (val) => `${Math.trunc(val / 60.0)}m ago`;
  const hoursFmt = (val) => `${Math.trunc(val / 3600.0)}h ago`;
  const daysFmt = (val) => `${Math.trunc(val / (3600.0 * 24))}d ago`;

  switch (true) {
    case d < limits.now:
      return nowFmt(d);
    case d >= limits.now && d < limits.seconds:
      return secondsFmt(d);
    case d >= limits.seconds && d < limits.minutes:
      return minutesFmt(d);
    case d >= limits.minutes && d < limits.hours:
      return hoursFmt(d);
    default:
      return daysFmt(d);
  }
};

const DurationBadge = (props) => {
  const { from } = props;
  const [elapsed, setElapsed] = useState(0.0);
  const [timer, setTimer] = useState(null);

  const refreshElapsed = () => {
    const now = new Date();
    setElapsed(now.getTime / 1000.0 - from.getTime() / 1000.0);
  };

  useEffect(() => {
    refreshElapsed();
    setTimer(setInterval(refreshElapsed, 10 * 1000));
    return () => {
      if (timer !== null) {
        clearInterval(timer);
      }
    };
  }, []);

  return (
    <span className="badge badge-secondary">{formatDuration(elapsed)}</span>
  );
};

export default DurationBadge;
export { DurationBadge };
