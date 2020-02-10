import axios from 'axios';

const setAuthHeader = token => {
    if (token) {
        console.log(`Bearer${token}`)
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
        delete axios.defaults.headers.common['Authorization'];
    }
};

export default setAuthHeader;