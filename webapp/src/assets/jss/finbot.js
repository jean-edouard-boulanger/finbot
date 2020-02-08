// ##############################
// // // Variables - Styles that are used on more than one component
// #############################

// const drawerWidth = 260;

// const transition = {
//   transition: "all 0.33s cubic-bezier(0.685, 0.0473, 0.346, 1)"
// };

// const container = {
//   paddingRight: "15px",
//   paddingLeft: "15px",
//   marginRight: "auto",
//   marginLeft: "auto"
// };

// const defaultFont = {
//   fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
//   fontWeight: "300",
//   lineHeight: "1.5em"
// };

// const primaryColor = ["#9c27b0", "#ab47bc", "#8e24aa", "#af2cc5"];
// const warningColor = ["#ff9800", "#ffa726", "#fb8c00", "#ffa21a"];
// const dangerColor = ["#f44336", "#ef5350", "#e53935", "#f55a4e"];
// const successColor = ["#4caf50", "#66bb6a", "#43a047", "#5cb860"];
// const infoColor = ["#00acc1", "#26c6da", "#00acc1", "#00d3ee"];
// const roseColor = ["#e91e63", "#ec407a", "#d81b60", "#eb3573"];
// const grayColor = [
//   "#999",
//   "#777",
//   "#3C4858",
//   "#AAAAAA",
//   "#D2D2D2",
//   "#DDD",
//   "#b4b4b4",
//   "#555555",
//   "#333",
//   "#a9afbb",
//   "#eee",
//   "#e7e7e7"
// ];
// const blackColor = "#000";
// const whiteColor = "#FFF";

// const boxShadow = {
//   boxShadow:
//     "0 10px 30px -12px rgba(" +
//     hexToRgb(blackColor) +
//     ", 0.42), 0 4px 25px 0px rgba(" +
//     hexToRgb(blackColor) +
//     ", 0.12), 0 8px 10px -5px rgba(" +
//     hexToRgb(blackColor) +
//     ", 0.2)"
// };

// const primaryBoxShadow = {
//   boxShadow:
//     "0 4px 20px 0 rgba(" +
//     hexToRgb(blackColor) +
//     ",.14), 0 7px 10px -5px rgba(" +
//     hexToRgb(primaryColor[0]) +
//     ",.4)"
// };
// const infoBoxShadow = {
//   boxShadow:
//     "0 4px 20px 0 rgba(" +
//     hexToRgb(blackColor) +
//     ",.14), 0 7px 10px -5px rgba(" +
//     hexToRgb(infoColor[0]) +
//     ",.4)"
// };
// const successBoxShadow = {
//   boxShadow:
//     "0 4px 20px 0 rgba(" +
//     hexToRgb(blackColor) +
//     ",.14), 0 7px 10px -5px rgba(" +
//     hexToRgb(successColor[0]) +
//     ",.4)"
// };
// const warningBoxShadow = {
//   boxShadow:
//     "0 4px 20px 0 rgba(" +
//     hexToRgb(blackColor) +
//     ",.14), 0 7px 10px -5px rgba(" +
//     hexToRgb(warningColor[0]) +
//     ",.4)"
// };

// const warningCardHeader = {
//   background:
//     "linear-gradient(60deg, " + warningColor[1] + ", " + warningColor[2] + ")",
//   ...warningBoxShadow
// };
// const successCardHeader = {
//   background:
//     "linear-gradient(60deg, " + successColor[1] + ", " + successColor[2] + ")",
//   ...successBoxShadow
// };

// const defaultBoxShadow = {
//   border: "0",
//   borderRadius: "3px",
//   boxShadow:
//     "0 10px 20px -12px rgba(" +
//     hexToRgb(blackColor) +
//     ", 0.42), 0 3px 20px 0px rgba(" +
//     hexToRgb(blackColor) +
//     ", 0.12), 0 8px 10px -5px rgba(" +
//     hexToRgb(blackColor) +
//     ", 0.2)",
//   padding: "10px 0",
//   transition: "all 150ms ease 0s"
// };

// const title = {
//   color: grayColor[2],
//   textDecoration: "none",
//   fontWeight: "300",
//   marginTop: "30px",
//   marginBottom: "25px",
//   minHeight: "32px",
//   fontFamily: "'Roboto', 'Helvetica', 'Arial', sans-serif",
//   "& small": {
//     color: grayColor[1],
//     fontWeight: "400",
//     lineHeight: "1"
//   }
// };

// const cardTitle = {
//   ...title,
//   marginTop: "0",
//   marginBottom: "3px",
//   minHeight: "auto",
//   "& a": {
//     ...title,
//     marginTop: ".625rem",
//     marginBottom: "0.75rem",
//     minHeight: "auto"
//   }
// };

// const cardSubtitle = {
//   marginTop: "-.375rem"
// };

// const cardLink = {
//   "& + $cardLink": {
//     marginLeft: "1.25rem"
//   }
// };

// export {
//   hexToRgb,
//   //variables
//   drawerWidth,
//   transition,
//   container,
//   boxShadow,
//   card,
//   defaultFont,
//   primaryColor,
//   warningColor,
//   dangerColor,
//   successColor,
//   infoColor,
//   roseColor,
//   grayColor,
//   blackColor,
//   whiteColor,
//   primaryBoxShadow,
//   infoBoxShadow,
//   successBoxShadow,
//   warningBoxShadow,
//   dangerBoxShadow,
//   roseBoxShadow,
//   warningCardHeader,
//   successCardHeader,
//   dangerCardHeader,
//   infoCardHeader,
//   primaryCardHeader,
//   roseCardHeader,
//   cardActions,
//   cardHeader,
//   defaultBoxShadow,
//   title,
//   cardTitle,
//   cardSubtitle,
//   cardLink
// };