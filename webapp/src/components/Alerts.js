import React, { useContext } from 'react';
import AlertContext from "../context/alertContext";

const Alerts = () => {
    const alertContext = useContext(AlertContext);

    return (
        alertContext.alerts.length > 0 &&
        alertContext.alerts.map(alert => (
            <div key={alert.id} className={`alert alert-${alert.type}`}>
                <i className='fas fa-info-cirlce'>{alert.msg}</i>
            </div>
        ))
    );
};

export default Alerts;